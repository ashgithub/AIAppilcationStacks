""" This is the main graph to put together the backend service and the dynamic ui """

from collections.abc import AsyncIterable
from typing import Any
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from dynamic_app.ui_agents_graph.ui_orchestrator_agent import UIOrchestrator
from dynamic_app.ui_agents_graph.ui_assembly_agent import UIAssemblyAgent
from dynamic_app.back_agents_graph.backend_orchestrator_agent import BackendOrchestratorAgent
from dynamic_app.configs.common_struct import AgentGraphException
from dynamic_app.configs.common_struct import AgentConfig

from dotenv import load_dotenv
load_dotenv()

class DynamicGraph:
    """ Graph to call the UI agent chain """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream"]
    CONTENT_TRUNCATION_LENGTH = 50

    def __init__(self, base_url:str, use_ui:bool = False, graph_configuration: dict[str, AgentConfig] = None, inline_catalog: list = None):
        self._inline_catalog = inline_catalog or []
        self._backend_orchestrator = BackendOrchestratorAgent()
        self._ui_orchestrator = UIOrchestrator()
        self._ui_assembly = UIAssemblyAgent(base_url, self._inline_catalog)

    @property
    def inline_catalog(self):
        return self._inline_catalog

    @inline_catalog.setter
    def inline_catalog(self, value):
        self._inline_catalog = value or []
        # Update inline catalog on UI assembly agent
        if hasattr(self, '_ui_assembly'):
            self._ui_assembly.inline_catalog = self._inline_catalog

    async def build_graph(self):
        checkpointer = InMemorySaver()

        graph_builder = StateGraph(MessagesState)

        # Add backend orchestrator (supervisor)
        graph_builder.add_node("backend_orchestrator", self._backend_orchestrator)

        # Add UI agents
        graph_builder.add_node("ui_orchestrator", self._ui_orchestrator)
        graph_builder.add_node("ui_assembly", self._ui_assembly)

        # Define edges: START -> backend_orchestrator -> ui_orchestrator -> ui_assembly -> END
        graph_builder.add_edge(START, "backend_orchestrator")
        graph_builder.add_edge("backend_orchestrator", "ui_orchestrator")
        graph_builder.add_edge("ui_orchestrator", "ui_assembly")
        graph_builder.add_edge("ui_assembly", END)

        self._dynamic_ui_graph = graph_builder.compile(checkpointer=checkpointer)

    def _format_tool_call_message(self, message: AnyMessage) -> tuple[str, str]:
        tool_name = str(message.tool_calls[0].get('name'))
        tool_args = str(message.tool_calls[0].get('args'))
        agent_name = str(message.name) if message.name else ""
        timeline_message = f"{agent_name} called tool: {tool_name}"
        detailed_message = f"Agent {agent_name} called tool: {tool_name} with args {tool_args}"
        return timeline_message, detailed_message

    def _format_tool_message(self, message: ToolMessage) -> tuple[str, str]:
        tool_name = str(message.name)
        status_content = str(message.content)
        timeline_message = f"Tool {tool_name} responded"
        detailed_message = f"Tool {tool_name} responded with data:\n{status_content[:self.CONTENT_TRUNCATION_LENGTH]}"
        return timeline_message, detailed_message

    def _format_ai_message(self, message: AIMessage, model_token_count: int) -> tuple[str, int, str]:
        status_content = str(message.content)
        model_id = str(message.response_metadata.get("model_id"))
        total_tokens_on_call = int(message.response_metadata.get("total_tokens", '0'))
        updated_token_count = model_token_count + total_tokens_on_call
        agent_name = str(message.name) if message.name else "GRAPH"
        model_data = f"""
            model_id: {model_id},
            total_tokens_on_call: {str(updated_token_count)}
        """
        formatted = f"{agent_name} response:\n{status_content[:self.CONTENT_TRUNCATION_LENGTH]}...\n\nAgent metadata:\n{model_data}"
        
        timeline_message = f"{agent_name} responded"
        detailed_message = formatted
        return timeline_message, updated_token_count, detailed_message

    def _format_human_message(self, message: HumanMessage, node_name: str) -> tuple[str, str]:
        status_content = str(message.content)
        timeline_message = f"Current query: {node_name}"
        detailed_message = f"Query in process at {node_name}:\n{status_content[:self.CONTENT_TRUNCATION_LENGTH]}..."
        return timeline_message, detailed_message

    def _format_other_message(self, message: AnyMessage, node_name: str) -> tuple[str, str]:
        status_content = str(message.content)
        timeline_message = f"Calling node: {node_name}"
        detailed_message = f"Calling node {node_name} with status: {status_content[:self.CONTENT_TRUNCATION_LENGTH]}"
        return timeline_message, detailed_message

    async def call_dynamic_ui_graph(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        current_message = {"messages":[HumanMessage(query)]}
        config:RunnableConfig = {
            "run_id":str(session_id), 
            "configurable":{"thread_id":str(session_id)},
        }
        final_response_content = None
        model_token_count = 0
        node_name = "START"

        # Stream graph execution
        async for chunk in self._dynamic_ui_graph.astream(
            input=current_message,
            config=config,
            stream_mode='values',
            subgraphs=True
        ):
            latest_message: AnyMessage = chunk[1]['messages'][-1]
            final_response_content = latest_message.content

            # Format the message based on its type
            if hasattr(latest_message, 'tool_calls') and latest_message.tool_calls:
                timeline_message, detailed_message = self._format_tool_call_message(latest_message)
            elif isinstance(latest_message, ToolMessage):
                timeline_message, detailed_message = self._format_tool_message(latest_message)
            elif isinstance(latest_message, AIMessage):
                timeline_message, model_token_count, detailed_message = self._format_ai_message(latest_message, model_token_count)
            elif isinstance(latest_message, HumanMessage):
                # For human messages, update node_name from state before formatting
                state = self._dynamic_ui_graph.get_state(config=config, subgraphs=True)
                node_name = str(state.next[0]) if state.next else "GRAPH"
                timeline_message, detailed_message = self._format_human_message(latest_message, node_name)
            else:
                timeline_message, detailed_message = self._format_other_message(latest_message, node_name)

            # Update node_name from graph state for non-human messages
            if not isinstance(latest_message, HumanMessage):
                state = self._dynamic_ui_graph.get_state(config=config, subgraphs=True)
                node_name = str(state.next[0]) if state.next else "GRAPH"

            # Yield intermediate updates
            yield {
                "is_task_complete": False,
                "updates": timeline_message,
                "detailed_updates": detailed_message
            }

        # Ensure final_response_content is valid
        if final_response_content and "---a2ui_JSON---" in final_response_content:
            text_part, json_string = final_response_content.split("---a2ui_JSON---", 1)
            final_content = f"{text_part.strip()}\n---a2ui_JSON---\n{json_string.strip()}"
        else:
            final_content = final_response_content or "No response generated"

        yield {
            "is_task_complete": True,
            "content": final_content,
            "detailed_updates": detailed_message,
            "token_count": str(model_token_count)
        }

#region Testing
async def main():
    graph = DynamicGraph(base_url="http://localhost:8000")

    await graph.build_graph()

    async for event in graph.call_dynamic_ui_graph("Show me a dashboard with some charts and graphs about energy usage", "1234"):
        if event['is_task_complete']:
            print(f"\nFinal event: {event}")
        else:
            if len(event['updates']) < 200:
                print(event)
            else:
                print(event['updates'][:200])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
