import logging
import re
import json

from collections.abc import AsyncIterable
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from dynamic_app.ui_agents_graph.ui_orchestrator_agent import UIOrchestrator
from dynamic_app.ui_agents_graph.ui_orchestrator_agent import SuggestionsReponseLLM
from dynamic_app.ui_agents_graph.ui_assembly_agent import UIAssemblyAgent
from dynamic_app.back_agents_graph.backend_orchestrator_agent import BackendOrchestratorAgent
from core.dynamic_app.dynamic_struct import AgentGraphException
from core.dynamic_app.dynamic_struct import AgentConfig
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.common_struct import SuggestedQuestions
from core.common_struct import SuggestionModel
from core.common_struct import SUGGESTION_QUERY

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


SOURCE_PATTERN = re.compile(r"\(Source:\s*([^)]+)\)")


def extract_RAG_sources(semantic_result: str) -> list[str]:
    """Extract unique document names from semantic search tool output."""
    if not semantic_result:
        return []

    documents: list[str] = []
    seen: set[str] = set()

    for source in SOURCE_PATTERN.findall(semantic_result):
        filename = source.strip().replace("\\", "/").split("/")[-1]
        match = re.match(r"(.+?\.[A-Za-z0-9]+)(?:_start_\d+)?$", filename)
        doc_name = match.group(1) if match else filename

        if doc_name and doc_name not in seen:
            seen.add(doc_name)
            documents.append(doc_name)

    return documents

class DynamicGraph:
    """ Graph to call the UI agent chain """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream"]
    CONTENT_TRUNCATION_LENGTH = 50

    def __init__(self, base_url:str, use_ui:bool = False, graph_configuration: dict[str, AgentConfig] = None, inline_catalog: list = None):
        self._inline_catalog = inline_catalog or []
        self._backend_orchestrator = BackendOrchestratorAgent()
        self._ui_orchestrator = UIOrchestrator()
        self._suggestions_llm = SuggestionsReponseLLM()
        self._ui_assembly = UIAssemblyAgent(base_url, self._inline_catalog)
        # TODO: temp solution to graph state
        self._out_query = SUGGESTION_QUERY

    @property
    def inline_catalog(self):
        return self._inline_catalog

    @inline_catalog.setter
    def inline_catalog(self, value):
        self._inline_catalog = value or []
        # Update inline catalog on UI assembly agent
        if hasattr(self, '_ui_assembly'):
            self._ui_assembly.inline_catalog = self._inline_catalog

    async def aggregator(self,state:DynamicGraphState):
        """ Combines the outputs """

        return {
            'messages': state['messages'],
            'suggestions': state['suggestions']
        }

    async def build_graph(self):
        checkpointer = InMemorySaver()

        graph_builder = StateGraph(DynamicGraphState)

        # Add backend orchestrator (supervisor)
        graph_builder.add_node("backend_orchestrator", self._backend_orchestrator)

        # Add UI agents
        graph_builder.add_node("ui_orchestrator", self._ui_orchestrator)
        graph_builder.add_node("ui_assembly", self._ui_assembly)

        # Helper nodes
        graph_builder.add_node("suggestions", self._suggestions_llm)
        graph_builder.add_node("aggregator", self.aggregator)

        # Define edges: START -> backend_orchestrator -> ui_orchestrator -> ui_assembly -> END
        graph_builder.add_edge(START, "backend_orchestrator")
        graph_builder.add_edge("backend_orchestrator", "ui_orchestrator")
        graph_builder.add_edge("ui_orchestrator", "ui_assembly")
        graph_builder.add_edge("ui_orchestrator", "suggestions")
        graph_builder.add_edge("ui_assembly", "aggregator")
        graph_builder.add_edge("suggestions", "aggregator")
        graph_builder.add_edge("aggregator", END)

        self._dynamic_ui_graph = graph_builder.compile(checkpointer=checkpointer)

    def _format_message(
        self,
        message: AnyMessage,
        node_name: str = "",
        model_token_count: int = 0,
        source_documents: list[str] | None = None
    ) -> tuple[str, int, str]:
        """Status updates for client from each type of message"""
        if source_documents is None:
            source_documents = []

        agent_name = str(message.name) if hasattr(message, 'name') and message.name else "GRAPH"
        content = str(message.content)[:self.CONTENT_TRUNCATION_LENGTH]

        if hasattr(message, 'tool_calls') and message.tool_calls:
            if len(message.tool_calls) == 1:
                tool_name = str(message.tool_calls[0].get('name', ''))
                tool_args = str(message.tool_calls[0].get('args', ''))
                timeline_message = f"{agent_name} called tool: {tool_name}"
                detailed_message = f"{agent_name} called tool: {tool_name} with args {tool_args}"
            else:
                tool_names = [str(tc.get('name', '')) for tc in message.tool_calls]
                timeline_message = f"{agent_name} called tools: {', '.join(tool_names)}"
                detailed_message = f"{agent_name} called tools: {', '.join(tool_names)}"
        elif isinstance(message, ToolMessage):
            tool_name = str(message.name)
            timeline_message = f"Tool {tool_name} responded"
            detailed_message = f"Tool {tool_name} responded with data:\n{content}"
            if tool_name == "semantic_search":
                    for document_name in extract_RAG_sources(str(message.content)):
                        if document_name not in source_documents:
                            source_documents.append(document_name)
        elif isinstance(message, AIMessage):
            model_id = str(message.response_metadata.get("model_id", ""))
            total_tokens_on_call = int(message.response_metadata.get("total_tokens", '0'))
            updated_token_count = model_token_count + total_tokens_on_call
            model_data = f"""
            model_id: {model_id},
            total_tokens_on_call: {str(updated_token_count)}
            """
            timeline_message = f"{agent_name} responded"
            detailed_message = f"{agent_name} response:\n{content}...\n\nAgent metadata:\n{model_data}"
            return timeline_message, updated_token_count, detailed_message
        elif isinstance(message, HumanMessage):
            timeline_message = f"{node_name} received query"
            detailed_message = f"Query in process at {node_name}:\n{content}..."
        else:
            timeline_message = f"Routing to next step"
            detailed_message = f"Routing to next step"

        return timeline_message, model_token_count, detailed_message

    async def call_dynamic_ui_graph(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        current_message = {"messages":[HumanMessage(query)]}
        config:RunnableConfig = {
            "run_id":str(session_id), 
            "configurable":{"thread_id":str(session_id)},
        }
        final_response_content = None
        model_token_count = 0
        node_name = "START"
        suggestions = ""
        source_documents: list[str] = []
        detailed_message = ""
        processed_messages = 0

        async for chunk in self._dynamic_ui_graph.astream(
            input=current_message,
            config=config,
            stream_mode='values',
            subgraphs=True
        ):
            if 'suggestions' in chunk[1]:
                suggestions = chunk[1]['suggestions']
            messages = chunk[1].get("messages", [])
            new_messages = messages[processed_messages:]
            processed_messages = len(messages)

            # Update node_name from graph state
            state = self._dynamic_ui_graph.get_state(config=config, subgraphs=True)
            node_name = str(state.next[0]) if state.next else "GRAPH"

            for latest_message in new_messages:
                if isinstance(latest_message, AIMessage):
                    final_response_content = latest_message.content

                # Skip state for graph routing or no named nodes
                if (
                    (node_name == "GRAPH" and isinstance(latest_message, AIMessage))
                    or (hasattr(latest_message, 'name') and not latest_message.name)
                ):
                    continue

                if isinstance(latest_message, AIMessage):
                    timeline_message, model_token_count, detailed_message = self._format_message(
                        latest_message,
                        node_name,
                        model_token_count,
                        source_documents
                    )
                else:
                    timeline_message, _, detailed_message = self._format_message(
                        latest_message,
                        node_name,
                        model_token_count,
                        source_documents
                    )

                updates = {
                    "is_task_complete": False,
                    "updates": timeline_message,
                    "detailed_updates": detailed_message
                }

                yield updates

        # Ensure final_response_content is valid
        if final_response_content and "---a2ui_JSON---" in final_response_content:
            text_part, json_string = final_response_content.split("---a2ui_JSON---", 1)
            final_content = f"{text_part.strip()}\n---a2ui_JSON---\n{json_string.strip()}"
        else:
            final_content = final_response_content or "No response generated"

        # TODO: temp fix for state on graph
        fall_back_suggestions_model = SuggestionModel().build_suggestion_model()
        raw_suggestions = await fall_back_suggestions_model.ainvoke(self._out_query+f"\n\nContext for question generation:\n{final_response_content}")
        if not raw_suggestions: raw_suggestions = SuggestedQuestions(suggested_questions=["Tell me more details about first data", "Make a summary of data given"])
        suggestions = raw_suggestions.model_dump_json()

        final_payload = {
            "is_task_complete": True,
            "content": final_content,
            "detailed_updates": detailed_message,
            "token_count": str(model_token_count),
            "suggestions": suggestions,
            "sources": json.dumps(source_documents)
        }

        yield final_payload

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
