import logging
import re
import json
import os
import uuid

from collections.abc import AsyncIterable
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse

from dynamic_app.ui_agents_graph.ui_orchestrator_agent import UIOrchestrator
from dynamic_app.ui_agents_graph.ui_orchestrator_agent import SuggestionsReponseLLM
from dynamic_app.ui_agents_graph.ui_assembly_agent import UIAssemblyAgent
from dynamic_app.ui_agents_graph.ui_parallel_structured_agents import ParallelUIStructuredAssembler
from dynamic_app.back_agents_graph.backend_orchestrator_agent import BackendOrchestratorAgent
from core.dynamic_app.dynamic_struct import AgentConfig
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.langfuse_tracing import (
    LangfuseTracingProvider,
    extract_total_tokens_from_message,
)
from core.common_struct import SuggestedQuestions
from core.common_struct import SuggestionModel
from core.common_struct import SUGGESTION_QUERY

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


SOURCE_PATTERN = re.compile(r"\(Source:\s*([^)]+)\)")


#region Utilities
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
#endregion


#region Dynamic Graph
class DynamicGraph:
    """Graph that orchestrates backend retrieval and UI generation."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream", "application/json+a2ui"]
    CONTENT_TRUNCATION_LENGTH = 50
    UI_RESPONSE_AGENT_NAMES = {"parallel_structured_ui_assembly", "ui_assembly"}

    def __init__(
        self,
        base_url: str,
        langfuse_client: Langfuse | None = None,
        use_ui: bool = False,
        graph_configuration: dict[str, AgentConfig] = None,
        inline_catalog: list = None,
    ):
        self.use_ui = use_ui
        self.graph_configuration = graph_configuration or {}
        self._inline_catalog = inline_catalog or []
        self.langfuse_client = langfuse_client
        self._backend_orchestrator = BackendOrchestratorAgent()
        self._ui_orchestrator = UIOrchestrator()
        self._suggestions_llm = SuggestionsReponseLLM()
        self._ui_assembly = UIAssemblyAgent(
            base_url,
            self._inline_catalog,
        )
        self._parallel_structured_ui_assembly = ParallelUIStructuredAssembler()
        self._use_parallel_structured_ui = True
        self._out_query = SUGGESTION_QUERY
        self.langfuse_tracing_provider = LangfuseTracingProvider(langfuse_client=langfuse_client)

    @property
    def inline_catalog(self):
        return self._inline_catalog

    @inline_catalog.setter
    def inline_catalog(self, value):
        self._inline_catalog = value or []
        if hasattr(self, '_ui_assembly'):
            self._ui_assembly.inline_catalog = self._inline_catalog

    #region Graph Nodes
    async def aggregator(self,state:DynamicGraphState):
        """Combine output fields from parallel graph branches."""
        return {
            'messages': state['messages'],
            'suggestions': state['suggestions']
        }
    #endregion

    #region Graph Build
    async def build_graph(self):
        checkpointer = InMemorySaver()

        graph_builder = StateGraph(DynamicGraphState)

        graph_builder.add_node("backend_orchestrator", self._backend_orchestrator)

        graph_builder.add_node("suggestions", self._suggestions_llm)
        graph_builder.add_node("aggregator", self.aggregator)

        graph_builder.add_edge(START, "backend_orchestrator")

        if self._use_parallel_structured_ui:
            graph_builder.add_node(
                "parallel_structured_ui_assembly", self._parallel_structured_ui_assembly
            )
            graph_builder.add_edge("backend_orchestrator", "parallel_structured_ui_assembly")
            graph_builder.add_edge("backend_orchestrator", "suggestions")
            graph_builder.add_edge("parallel_structured_ui_assembly", "aggregator")
            graph_builder.add_edge("suggestions", "aggregator")
            graph_builder.add_edge("aggregator", END)
        else:
            graph_builder.add_node("ui_orchestrator", self._ui_orchestrator)
            graph_builder.add_node("ui_assembly", self._ui_assembly)
            graph_builder.add_edge("backend_orchestrator", "ui_orchestrator")
            graph_builder.add_edge("ui_orchestrator", "ui_assembly")
            graph_builder.add_edge("ui_orchestrator", "suggestions")
            graph_builder.add_edge("ui_assembly", "aggregator")
            graph_builder.add_edge("suggestions", "aggregator")
            graph_builder.add_edge("aggregator", END)

        self._dynamic_ui_graph = graph_builder.compile(checkpointer=checkpointer)
    #endregion

    #region Stream Formatting
    def _extract_node_name_from_stream_chunk(self, chunk: Any) -> str:
        """Resolve node name directly from subgraph stream chunk path."""
        if isinstance(chunk, tuple) and chunk:
            path = chunk[0]
            if isinstance(path, tuple) and path:
                return str(path[-1])
            if isinstance(path, str):
                return path
        return "GRAPH"

    def _extract_chunk_state(self, chunk: Any) -> dict[str, Any]:
        """Normalize chunk state shape for subgraph stream mode."""
        if isinstance(chunk, tuple) and len(chunk) > 1 and isinstance(chunk[1], dict):
            return chunk[1]
        if isinstance(chunk, dict):
            return chunk
        return {}

    def _message_dedupe_key(self, message: AnyMessage) -> str:
        """Build a stable dedupe key for streamed messages."""
        message_id = getattr(message, "id", None)
        if message_id:
            return str(message_id)

        message_name = str(getattr(message, "name", "") or "")
        message_content = str(getattr(message, "content", "") or "")
        message_type = message.__class__.__name__
        return f"{message_type}:{message_name}:{message_content}"

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

        agent_name = str(message.name) if hasattr(message, 'name') and message.name else (node_name or "GRAPH")
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
            total_tokens_on_call = extract_total_tokens_from_message(message)
            updated_token_count = model_token_count + total_tokens_on_call
            model_data = f"""
            model_id: {model_id},
            total_tokens_on_call: {str(total_tokens_on_call)},
            aggregated_total_tokens: {str(updated_token_count)}
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
    #endregion

    #region Execution
    async def call_dynamic_ui_graph(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        current_message = {"messages":[HumanMessage(query)]}
        request_id = uuid.uuid4().hex
        stable_session_id = str(session_id) if session_id else request_id
        final_response_content = None
        ui_response_content = None
        ai_message_count = 0
        model_token_count = 0
        node_name = "START"
        suggestions = ""
        source_documents: list[str] = []
        detailed_message = ""
        seen_message_keys: set[str] = set()
        emitted_human_message = False
        final_payload: dict[str, Any] | None = None
        langfuse_client = self.langfuse_client or self.langfuse_tracing_provider.get_current_client()
        session_token = self.langfuse_tracing_provider.set_current_session_id(stable_session_id)
        client_token = self.langfuse_tracing_provider.set_current_client(langfuse_client)
        try:
            config:RunnableConfig = self.langfuse_tracing_provider.build_runnable_config(
                run_id=request_id,
                session_id=stable_session_id,
                thread_id=stable_session_id,
                user_id=os.getenv("LANGFUSE_USER_ID", "default_user"),
                tags=["main_dynamic_app"],
                extra_metadata={"request_id": request_id},
            )
            async for chunk in self._dynamic_ui_graph.astream(
                input=current_message,
                config=config,
                stream_mode='values',
                subgraphs=True
            ):
                chunk_state = self._extract_chunk_state(chunk)
                node_name = self._extract_node_name_from_stream_chunk(chunk)

                if 'suggestions' in chunk_state:
                    suggestions = chunk_state['suggestions']

                messages = chunk_state.get("messages", [])
                new_messages: list[AnyMessage] = []
                for message in messages:
                    dedupe_key = self._message_dedupe_key(message)
                    if dedupe_key in seen_message_keys:
                        continue
                    seen_message_keys.add(dedupe_key)
                    new_messages.append(message)

                logger.debug(
                    "dynamic stream chunk node=%s total_messages=%s new_messages=%s",
                    node_name,
                    len(messages),
                    len(new_messages),
                )

                for latest_message in new_messages:
                    if isinstance(latest_message, HumanMessage):
                        if emitted_human_message:
                            continue
                        emitted_human_message = True

                    if isinstance(latest_message, AIMessage):
                        ai_message_count += 1
                        final_response_content = latest_message.content
                        message_name = str(getattr(latest_message, "name", "") or "")
                        message_content = str(getattr(latest_message, "content", "") or "")
                        if (
                            "---a2ui_JSON---" in message_content
                            or message_name in self.UI_RESPONSE_AGENT_NAMES
                        ):
                            ui_response_content = message_content
                            logger.info(
                                "Captured UI candidate message | node=%s name=%s has_a2ui=%s len=%s",
                                node_name,
                                message_name,
                                "---a2ui_JSON---" in message_content,
                                len(message_content),
                            )
                        else:
                            logger.debug(
                                "Captured non-UI AI message | node=%s name=%s len=%s",
                                node_name,
                                message_name,
                                len(message_content),
                            )

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
                        "detailed_updates": detailed_message,
                        # Expose raw model content so the executor can progressively parse A2UI payloads.
                        "content": str(getattr(latest_message, "content", "") or ""),
                    }

                    yield updates

            selected_final_response = ui_response_content or final_response_content
            logger.info(
                "Final response selection | ai_messages=%s ui_selected=%s ui_len=%s fallback_len=%s",
                ai_message_count,
                ui_response_content is not None,
                len(ui_response_content or ""),
                len(final_response_content or ""),
            )

            if selected_final_response and "---a2ui_JSON---" in selected_final_response:
                text_part, json_string = selected_final_response.split("---a2ui_JSON---", 1)
                final_content = f"{text_part.strip()}\n---a2ui_JSON---\n{json_string.strip()}"
            else:
                final_content = selected_final_response or "No response generated"

            # Fallback suggestion generation ensures response consistency.
            fall_back_suggestions_model = SuggestionModel().build_suggestion_model()
            raw_suggestions = await fall_back_suggestions_model.ainvoke(
                self._out_query
                + f"\n\nContext for question generation:\n{selected_final_response}"
            )
            if not raw_suggestions:
                raw_suggestions = SuggestedQuestions(suggested_questions=["Tell me more details about first data", "Make a summary of data given"])
            suggestions = raw_suggestions.model_dump_json()

            final_payload = {
                "is_task_complete": True,
                "content": final_content,
                "detailed_updates": detailed_message,
                "token_count": str(model_token_count),
                "suggestions": suggestions,
                "sources": json.dumps(source_documents)
            }
        finally:
            self.langfuse_tracing_provider.reset_current_client(client_token)
            self.langfuse_tracing_provider.reset_current_session_id(session_token)

        if final_payload is not None:
            yield final_payload
    #endregion
#endregion


#region Testing
async def main():
    langfuse_client = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )
    graph = DynamicGraph(base_url="http://localhost:8000", langfuse_client=langfuse_client)

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
