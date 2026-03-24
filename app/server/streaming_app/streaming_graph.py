import logging
import re
import json
import os
import uuid
import asyncio
import time

from collections.abc import AsyncIterable
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse

from streaming_app.data_agents.data_orchestrator import DataOrchestrator
from streaming_app.ui_builders.layout_builder import LayoutBuilder
from streaming_app.ui_builders.ui_parallel_widget_worker_agent import UIParallelWidgetWorkerAgent
from streaming_app.ui_builders.ui_parallel_fragment_merge_agent import (
    UIParallelFragmentMergeAgent,
    WorkerFragment,
)
from core.dynamic_app.dynamic_struct import AgentConfig
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
PARALLEL_WIDGET_WORKER_COUNT = max(1, int(os.getenv("STREAMING_UI_PARALLEL_WORKERS", "4")))

class StreamingDynamicApp:
    """ Graph that uses streaming capabilities to generate progressive UI """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream"]
    CONTENT_TRUNCATION_LENGTH = 50

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
        self._data_orchestrator = DataOrchestrator()
        self._layout_builder = LayoutBuilder()
        self._widget_worker = UIParallelWidgetWorkerAgent(inline_catalog=self._inline_catalog)
        self._fragment_merger = UIParallelFragmentMergeAgent()
        self._out_query = SUGGESTION_QUERY
        self.langfuse_tracing_provider = LangfuseTracingProvider(langfuse_client=langfuse_client)

    @property
    def inline_catalog(self):
        return self._inline_catalog

    @inline_catalog.setter
    def inline_catalog(self, value):
        self._inline_catalog = value or []
        if hasattr(self, "_widget_worker"):
            self._widget_worker.inline_catalog = self._inline_catalog

    async def _invoke_agent_and_keep_last_message(self, agent: Any, state: MessagesState) -> dict[str, Any]:
        """Invoke an agent and normalize output to a single appended message."""
        result = await agent(state)
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if not messages:
            return {"messages": []}
        return {"messages": [messages[-1]]}

    @staticmethod
    def _find_latest_message_by_name(messages: list[AnyMessage], name: str) -> AnyMessage | None:
        for message in reversed(messages):
            if getattr(message, "name", None) == name:
                return message
        return None

    @staticmethod
    def _safe_json_loads(content: str, fallback: Any) -> Any:
        try:
            return json.loads(content)
        except Exception:
            return fallback

    async def _data_orchestrator_node(self, state: MessagesState) -> dict[str, Any]:
        return await self._invoke_agent_and_keep_last_message(self._data_orchestrator, state)

    async def _layout_builder_node(self, state: MessagesState) -> dict[str, Any]:
        return await self._invoke_agent_and_keep_last_message(self._layout_builder, state)

    async def _parallel_widget_builders_node(self, state: MessagesState) -> dict[str, Any]:
        messages = state.get("messages", [])
        plan_message = self._find_latest_message_by_name(messages, self._layout_builder.agent_name)
        if not plan_message:
            logger.warning("No layout plan found. Skipping parallel workers.")
            return {
                "messages": [
                    AIMessage(
                        content=json.dumps({"worker_outputs": [], "warnings": ["missing_layout_plan"]}),
                        name="ui_parallel_worker_pool",
                    )
                ]
            }

        layout_plan = self._safe_json_loads(str(getattr(plan_message, "content", "")), {})
        work_packages = layout_plan.get("work_packages", []) if isinstance(layout_plan, dict) else []
        if not work_packages:
            logger.info("Layout plan has no work packages. Worker pool skipped.")
            return {
                "messages": [
                    AIMessage(
                        content=json.dumps({"worker_outputs": [], "warnings": ["no_work_packages"]}),
                        name="ui_parallel_worker_pool",
                    )
                ]
            }

        worker_state = {"messages": messages, "suggestions": ""}
        semaphore = asyncio.Semaphore(PARALLEL_WIDGET_WORKER_COUNT)

        async def run_package(package: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                output = await self._widget_worker.run_package(
                    state=worker_state,
                    package_id=str(package.get("package_id", "pkg-unknown")),
                    widgets=package.get("widgets", []),
                    target_component_ids=package.get("target_component_ids", []),
                    target_data_keys=package.get("target_data_keys", []),
                )
                return {
                    "package_id": str(package.get("package_id", "pkg-unknown")),
                    "priority": int(package.get("priority", 2)),
                    "payload": output.model_dump(),
                }

        worker_outputs = await asyncio.gather(*(run_package(package) for package in work_packages))

        return {
            "messages": [
                AIMessage(
                    content=json.dumps({"worker_outputs": worker_outputs}, ensure_ascii=False),
                    name="ui_parallel_worker_pool",
                )
            ]
        }

    async def _parallel_fragment_merge_node(self, state: MessagesState) -> dict[str, Any]:
        messages = state.get("messages", [])
        plan_message = self._find_latest_message_by_name(messages, self._layout_builder.agent_name)
        worker_message = self._find_latest_message_by_name(messages, "ui_parallel_worker_pool")

        if not plan_message:
            logger.warning("Missing layout plan in merge stage.")
            return {"messages": []}

        layout_plan = self._safe_json_loads(str(getattr(plan_message, "content", "")), {})
        shell_messages = layout_plan.get("shell_messages", []) if isinstance(layout_plan, dict) else []

        worker_payload = self._safe_json_loads(str(getattr(worker_message, "content", "")), {"worker_outputs": []})
        outputs = worker_payload.get("worker_outputs", []) if isinstance(worker_payload, dict) else []

        worker_fragments: list[WorkerFragment] = []
        for output in outputs:
            payload = output.get("payload", {})
            priority = int(output.get("priority", 2))
            fragment = self._fragment_merger.parse_worker_fragment(
                raw_payload=json.dumps(payload, ensure_ascii=False),
                priority=priority,
            )
            worker_fragments.append(fragment)

        merged = self._fragment_merger.merge(shell_messages=shell_messages, worker_fragments=worker_fragments)
        merged["final_a2ui_messages"] = merged.get("ordered_messages", [])

        return {
            "messages": [
                AIMessage(
                    content=json.dumps(merged, ensure_ascii=False),
                    name="ui_parallel_fragment_merger",
                )
            ]
        }

    async def build_graph(self):
        checkpointer = InMemorySaver()

        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("data_orchestrator", self._data_orchestrator_node)
        graph_builder.add_node("layout_builder", self._layout_builder_node)
        graph_builder.add_node("parallel_widget_builders", self._parallel_widget_builders_node)
        graph_builder.add_node("parallel_fragment_merger", self._parallel_fragment_merge_node)

        graph_builder.add_edge(START, "data_orchestrator")
        graph_builder.add_edge("data_orchestrator", "layout_builder")
        graph_builder.add_edge("layout_builder", "parallel_widget_builders")
        graph_builder.add_edge("parallel_widget_builders", "parallel_fragment_merger")
        graph_builder.add_edge("parallel_fragment_merger", END)

        self._streaming_app_graph = graph_builder.compile(checkpointer=checkpointer)

    async def call_streaming_dynamic_app(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        current_message = {"messages": [HumanMessage(query)]}
        final_response_content = None

        configurable:RunnableConfig = {"configurable": {"thread_id": session_id}}
        async for chunk in self._streaming_app_graph.astream(
            input=current_message, 
            config=configurable,
            stream_mode='values',
            subgraphs=True
        ):
            yield chunk

async def main():
    langfuse_client = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )
    graph = StreamingDynamicApp(base_url="http://localhost:8000", langfuse_client=langfuse_client)

    await graph.build_graph()

    started_at = time.perf_counter()
    event_count = 0
    async for event in graph.call_streaming_dynamic_app("What are the most common outage cause categories in the last 6 months?", "1234"):
        event_count += 1
        elapsed = time.perf_counter() - started_at
        latest_message = event[1]['messages'][-1]
        message_name = getattr(latest_message, "name", "unknown")
        print(f"[+{elapsed:.2f}s][event={event_count}][node={message_name}]")
        print(latest_message)

    total_elapsed = time.perf_counter() - started_at
    print(f"\nTotal request time: {total_elapsed:.2f}s across {event_count} streamed event(s).")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
