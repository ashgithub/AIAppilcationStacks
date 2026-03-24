import asyncio
import json
import logging
import os
import re
import time
import uuid

from collections.abc import AsyncIterable
from typing import Any

from langchain.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from core.common_struct import SUGGESTION_QUERY, SuggestedQuestions, SuggestionModel
from core.dynamic_app.dynamic_struct import AgentConfig
from core.langfuse_tracing import LangfuseTracingProvider, extract_total_tokens_from_message
from streaming_app.data_agents.data_orchestrator import DataOrchestrator
from streaming_app.ui_builders.layout_builder import LayoutBuilder
from streaming_app.ui_builders.ui_parallel_fragment_merge_agent import (
    UIParallelFragmentMergeAgent,
    WorkerFragment,
)
from streaming_app.ui_builders.ui_parallel_widget_worker_agent import UIParallelWidgetWorkerAgent

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
PARALLEL_WIDGET_WORKER_COUNT = max(1, int(os.getenv("STREAMING_UI_PARALLEL_WORKERS", "4")))
SOURCE_PATTERN = re.compile(r"\(Source:\s*([^)]+)\)")


def extract_rag_sources(semantic_result: str) -> list[str]:
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


class StreamingDynamicApp:
    """Graph app for progressive UI streaming with parallel widget workers."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream", "application/json+a2ui"]
    CONTENT_TRUNCATION_LENGTH = 80

    def __init__(
        self,
        base_url: str,
        langfuse_client: Langfuse | None = None,
        use_ui: bool = False,
        graph_configuration: dict[str, AgentConfig] | None = None,
        inline_catalog: list | None = None,
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

        self._streaming_app_graph = None
        self._progress_queue: asyncio.Queue[dict[str, Any]] | None = None

    @property
    def inline_catalog(self):
        return self._inline_catalog

    @inline_catalog.setter
    def inline_catalog(self, value):
        self._inline_catalog = value or []
        if hasattr(self, "_widget_worker"):
            self._widget_worker.inline_catalog = self._inline_catalog

    @staticmethod
    def _safe_json_loads(content: str, fallback: Any) -> Any:
        try:
            return json.loads(content)
        except Exception:
            return fallback

    @staticmethod
    def _find_latest_message_by_name(messages: list[AnyMessage], name: str) -> AnyMessage | None:
        for message in reversed(messages):
            if getattr(message, "name", None) == name:
                return message
        return None

    async def _emit_progress_message(self, message: AnyMessage, node_name: str) -> None:
        if self._progress_queue is None:
            return
        await self._progress_queue.put(
            {
                "type": "runtime_message",
                "node_name": node_name,
                "message": message,
            }
        )

    async def _invoke_agent_and_keep_last_message(self, agent: Any, state: MessagesState) -> dict[str, Any]:
        result = await agent(state)
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if not messages:
            return {"messages": []}
        return {"messages": [messages[-1]]}

    async def _data_orchestrator_node(self, state: MessagesState) -> dict[str, Any]:
        return await self._invoke_agent_and_keep_last_message(self._data_orchestrator, state)

    async def _layout_builder_node(self, state: MessagesState) -> dict[str, Any]:
        result = await self._invoke_agent_and_keep_last_message(self._layout_builder, state)
        latest = result.get("messages", [])[-1] if result.get("messages") else None
        if latest is not None:
            await self._emit_progress_message(latest, "layout_builder")
        return result

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

        async def run_package(package: dict[str, Any]) -> tuple[dict[str, Any], AIMessage]:
            package_id = str(package.get("package_id", "pkg-unknown"))
            package_priority = int(package.get("priority", 2))
            package_started = time.perf_counter()
            logger.info("Worker package %s queued (priority=%s).", package_id, package_priority)
            async with semaphore:
                started_inside = time.perf_counter()
                output = await self._widget_worker.run_package(
                    state=worker_state,
                    package_id=package_id,
                    widgets=package.get("widgets", []),
                    target_component_ids=package.get("target_component_ids", []),
                    target_data_keys=package.get("target_data_keys", []),
                )
                finished = time.perf_counter()

            worker_output = {
                "package_id": package_id,
                "priority": package_priority,
                "timing": {
                    "elapsed_ms": int((finished - package_started) * 1000),
                    "queue_wait_ms": int((started_inside - package_started) * 1000),
                    "run_ms": int((finished - started_inside) * 1000),
                },
                "payload": output.model_dump(),
            }
            worker_message = AIMessage(
                content=json.dumps(output.model_dump(), ensure_ascii=False),
                name=f"widget_worker_{package_id}",
            )
            return worker_output, worker_message

        worker_outputs: list[dict[str, Any]] = []
        tasks = [asyncio.create_task(run_package(package)) for package in work_packages]
        for completed in asyncio.as_completed(tasks):
            worker_output, worker_message = await completed
            worker_outputs.append(worker_output)
            await self._emit_progress_message(worker_message, str(getattr(worker_message, "name", "widget_worker")))

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
        merged_message = AIMessage(
            content=json.dumps(merged, ensure_ascii=False),
            name="ui_parallel_fragment_merger",
        )
        await self._emit_progress_message(merged_message, "parallel_fragment_merger")
        return {"messages": [merged_message]}

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

    def _extract_node_name_from_stream_chunk(self, chunk: Any) -> str:
        if isinstance(chunk, tuple) and chunk:
            path = chunk[0]
            if isinstance(path, tuple) and path:
                return str(path[-1])
            if isinstance(path, str):
                return path
        return "GRAPH"

    def _extract_chunk_state(self, chunk: Any) -> dict[str, Any]:
        if isinstance(chunk, tuple) and len(chunk) > 1 and isinstance(chunk[1], dict):
            return chunk[1]
        if isinstance(chunk, dict):
            return chunk
        return {}

    def _message_dedupe_key(self, message: AnyMessage) -> str:
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
        source_documents: list[str] | None = None,
    ) -> tuple[str, int, str]:
        if source_documents is None:
            source_documents = []

        agent_name = str(message.name) if hasattr(message, "name") and message.name else (node_name or "GRAPH")
        content = str(message.content)[: self.CONTENT_TRUNCATION_LENGTH]

        if hasattr(message, "tool_calls") and message.tool_calls:
            if len(message.tool_calls) == 1:
                tool_name = str(message.tool_calls[0].get("name", ""))
                tool_args = str(message.tool_calls[0].get("args", ""))
                timeline_message = f"{agent_name} called tool: {tool_name}"
                detailed_message = f"{agent_name} called tool: {tool_name} with args {tool_args}"
            else:
                tool_names = [str(tc.get("name", "")) for tc in message.tool_calls]
                timeline_message = f"{agent_name} called tools: {', '.join(tool_names)}"
                detailed_message = timeline_message
        elif isinstance(message, ToolMessage):
            tool_name = str(message.name)
            timeline_message = f"Tool {tool_name} responded"
            detailed_message = f"Tool {tool_name} responded with data:\n{content}"
            if tool_name == "semantic_search":
                for document_name in extract_rag_sources(str(message.content)):
                    if document_name not in source_documents:
                        source_documents.append(document_name)
        elif isinstance(message, AIMessage):
            model_id = str(message.response_metadata.get("model_id", ""))
            total_tokens_on_call = extract_total_tokens_from_message(message)
            updated_token_count = model_token_count + total_tokens_on_call
            timeline_message = f"{agent_name} responded"
            detailed_message = (
                f"{agent_name} response:\n{content}...\n\n"
                f"Agent metadata:\nmodel_id: {model_id}\n"
                f"total_tokens_on_call: {total_tokens_on_call}\n"
                f"aggregated_total_tokens: {updated_token_count}"
            )
            return timeline_message, updated_token_count, detailed_message
        elif isinstance(message, HumanMessage):
            timeline_message = f"{node_name} received query"
            detailed_message = f"Query in process at {node_name}:\n{content}..."
        else:
            timeline_message = "Routing to next step"
            detailed_message = "Routing to next step"

        return timeline_message, model_token_count, detailed_message

    def _extract_progressive_a2ui_messages(self, message: AnyMessage) -> list[dict[str, Any]]:
        if not isinstance(message, AIMessage):
            return []

        name = str(getattr(message, "name", "") or "")
        payload = self._safe_json_loads(str(getattr(message, "content", "") or ""), {})
        if not isinstance(payload, dict):
            return []

        if name == self._layout_builder.agent_name:
            shell_messages = payload.get("shell_messages", [])
            return self._normalize_a2ui_messages([msg for msg in shell_messages if isinstance(msg, dict)])

        if name.startswith("widget_worker_"):
            surface_messages = payload.get("surface_messages", [])
            return self._normalize_a2ui_messages([msg for msg in surface_messages if isinstance(msg, dict)])

        if name == "ui_parallel_worker_pool":
            messages: list[dict[str, Any]] = []
            for output in payload.get("worker_outputs", []):
                worker_payload = output.get("payload", {}) if isinstance(output, dict) else {}
                surface_messages = worker_payload.get("surface_messages", []) if isinstance(worker_payload, dict) else []
                messages.extend([msg for msg in surface_messages if isinstance(msg, dict)])
            return self._normalize_a2ui_messages(messages)

        if name == "ui_parallel_fragment_merger":
            final_messages = payload.get("final_a2ui_messages", payload.get("ordered_messages", []))
            return self._normalize_a2ui_messages([msg for msg in final_messages if isinstance(msg, dict)])

        return []

    @staticmethod
    def _normalize_path(path: str | None) -> str:
        if not path or path.strip() == "":
            return "/"
        if path.startswith("/"):
            return path
        return f"/{path}"

    @staticmethod
    def _join_data_path(base_path: str, child_key: str) -> str:
        base = StreamingDynamicApp._normalize_path(base_path)
        escaped_key = child_key.replace("~", "~0").replace("/", "~1")
        if base == "/":
            return f"/{escaped_key}"
        return f"{base.rstrip('/')}/{escaped_key}"

    @staticmethod
    def _to_leaf_contents(entry: dict[str, Any]) -> list[dict[str, Any]]:
        value_keys = [key for key in entry.keys() if key.startswith("value")]
        if len(value_keys) != 1:
            return [entry]
        value_key = value_keys[0]
        return [{"key": ".", value_key: entry[value_key]}]

    @staticmethod
    def _set_typed_value(entry: dict[str, Any], value: Any) -> None:
        for key in ("valueString", "valueNumber", "valueBoolean", "valueBool", "valueMap"):
            entry.pop(key, None)
        if isinstance(value, bool):
            entry["valueBoolean"] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            entry["valueNumber"] = value
        elif isinstance(value, list):
            entry["valueMap"] = value
        elif isinstance(value, dict):
            value_map = []
            for k, v in value.items():
                child = {"key": str(k)}
                StreamingDynamicApp._set_typed_value(child, v)
                value_map.append(child)
            entry["valueMap"] = value_map
        else:
            entry["valueString"] = str(value)

    def _coerce_content_entry(
        self,
        entry: Any,
        fallback_key: str,
    ) -> dict[str, Any] | None:
        if not isinstance(entry, dict):
            return None

        normalized = dict(entry)
        key = normalized.get("key")
        if not isinstance(key, str) or not key.strip():
            if "type" in normalized and "value" in normalized:
                normalized["key"] = fallback_key
            else:
                return None

        has_typed_value = any(
            value_key in normalized
            for value_key in ("valueString", "valueNumber", "valueBoolean", "valueBool", "valueMap")
        )
        if not has_typed_value and "value" in normalized:
            self._set_typed_value(normalized, normalized.get("value"))
        elif not has_typed_value:
            return None

        normalized.pop("type", None)
        normalized.pop("value", None)

        if "valueMap" in normalized and isinstance(normalized["valueMap"], dict):
            # Convert accidental object map into A2UI valueMap list entries.
            coerced_children = []
            for child_key, child_value in normalized["valueMap"].items():
                child_entry = {"key": str(child_key)}
                self._set_typed_value(child_entry, child_value)
                coerced_children.append(child_entry)
            normalized["valueMap"] = coerced_children

        return normalized

    def _expand_data_model_update(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        update = message.get("dataModelUpdate")
        if not isinstance(update, dict):
            return [message]

        surface_id = update.get("surfaceId")
        contents = update.get("contents")
        if not isinstance(surface_id, str) or not isinstance(contents, list):
            return [message]

        path = self._normalize_path(update.get("path", "/"))
        expanded_messages: list[dict[str, Any]] = []

        for index, entry in enumerate(contents):
            fallback_key = f"item_{index}"
            coerced_entry = self._coerce_content_entry(entry, fallback_key=fallback_key)
            if coerced_entry is None:
                continue

            entry_key = coerced_entry.get("key")
            if not isinstance(entry_key, str) or entry_key == ".":
                expanded_messages.append(
                    {
                        "dataModelUpdate": {
                            "surfaceId": surface_id,
                            "path": path,
                            "contents": [coerced_entry],
                        }
                    }
                )
                continue

            expanded_messages.append(
                {
                    "dataModelUpdate": {
                        "surfaceId": surface_id,
                        "path": self._join_data_path(path, entry_key),
                        "contents": self._to_leaf_contents(coerced_entry),
                    }
                }
            )

        return expanded_messages

    def _normalize_a2ui_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            if "dataModelUpdate" in message:
                normalized.extend(self._expand_data_model_update(message))
            else:
                normalized.append(message)
        return normalized

    async def _process_message_for_client(
        self,
        latest_message: AnyMessage,
        node_name: str,
        model_token_count: int,
        source_documents: list[str],
        seen_message_keys: set[str],
        emitted_a2ui_hashes: set[str],
    ) -> tuple[dict[str, Any] | None, int, str | None, list[dict[str, Any]]]:
        dedupe_key = self._message_dedupe_key(latest_message)
        if dedupe_key in seen_message_keys:
            return None, model_token_count, None, []
        seen_message_keys.add(dedupe_key)

        timeline_message, model_token_count, detailed_message = self._format_message(
            latest_message,
            node_name,
            model_token_count,
            source_documents,
        )

        progressive: list[dict[str, Any]] = []
        for message in self._extract_progressive_a2ui_messages(latest_message):
            serialized = json.dumps(message, sort_keys=True, ensure_ascii=False)
            if serialized in emitted_a2ui_hashes:
                continue
            emitted_a2ui_hashes.add(serialized)
            progressive.append(message)

        final_fragment = None
        if isinstance(latest_message, AIMessage) and str(getattr(latest_message, "name", "")) == "ui_parallel_fragment_merger":
            payload = self._safe_json_loads(str(getattr(latest_message, "content", "")), {})
            if isinstance(payload, dict):
                final_fragment = self._normalize_a2ui_messages(
                    payload.get("final_a2ui_messages", payload.get("ordered_messages", []))
                )

        update = {
            "is_task_complete": False,
            "updates": timeline_message,
            "detailed_updates": detailed_message,
            "content": str(getattr(latest_message, "content", "") or ""),
            "a2ui_messages": progressive,
        }
        return update, model_token_count, final_fragment, progressive

    async def call_streaming_dynamic_app(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        if self._streaming_app_graph is None:
            await self.build_graph()

        request_id = uuid.uuid4().hex
        stable_session_id = str(session_id) if session_id else request_id
        current_message = {"messages": [HumanMessage(query)]}

        model_token_count = 0
        source_documents: list[str] = []
        seen_message_keys: set[str] = set()
        emitted_a2ui_hashes: set[str] = set()
        detailed_message = ""
        final_response_content = ""
        final_a2ui_messages: list[dict[str, Any]] = []

        langfuse_client = self.langfuse_client or self.langfuse_tracing_provider.get_current_client()
        session_token = self.langfuse_tracing_provider.set_current_session_id(stable_session_id)
        client_token = self.langfuse_tracing_provider.set_current_client(langfuse_client)

        progress_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._progress_queue = progress_queue

        async def run_graph(config: RunnableConfig) -> None:
            try:
                async for chunk in self._streaming_app_graph.astream(
                    input=current_message,
                    config=config,
                    stream_mode="values",
                    subgraphs=True,
                ):
                    await progress_queue.put({"type": "graph_chunk", "chunk": chunk})
            except Exception as exc:
                await progress_queue.put({"type": "graph_error", "error": exc})
            finally:
                await progress_queue.put({"type": "graph_done"})

        try:
            config: RunnableConfig = self.langfuse_tracing_provider.build_runnable_config(
                run_id=request_id,
                session_id=stable_session_id,
                thread_id=stable_session_id,
                user_id=os.getenv("LANGFUSE_USER_ID", "default_user"),
                tags=["main_streaming_app"],
                extra_metadata={"request_id": request_id},
            )

            graph_task = asyncio.create_task(run_graph(config))
            graph_done = False

            while not graph_done or not progress_queue.empty():
                item = await progress_queue.get()
                item_type = item.get("type")

                if item_type == "graph_done":
                    graph_done = True
                    continue

                if item_type == "graph_error":
                    raise item["error"]

                if item_type == "runtime_message":
                    runtime_message = item["message"]
                    node_name = str(item.get("node_name", "runtime"))
                    update, model_token_count, final_fragment, _ = await self._process_message_for_client(
                        runtime_message,
                        node_name,
                        model_token_count,
                        source_documents,
                        seen_message_keys,
                        emitted_a2ui_hashes,
                    )
                    if update is not None:
                        detailed_message = update["detailed_updates"]
                        if isinstance(runtime_message, AIMessage):
                            final_response_content = str(getattr(runtime_message, "content", "") or "")
                        if isinstance(final_fragment, list):
                            final_a2ui_messages = [msg for msg in final_fragment if isinstance(msg, dict)]
                        yield update
                    continue

                if item_type == "graph_chunk":
                    chunk = item["chunk"]
                    chunk_state = self._extract_chunk_state(chunk)
                    node_name = self._extract_node_name_from_stream_chunk(chunk)
                    messages = chunk_state.get("messages", [])

                    for latest_message in messages:
                        update, model_token_count, final_fragment, _ = await self._process_message_for_client(
                            latest_message,
                            node_name,
                            model_token_count,
                            source_documents,
                            seen_message_keys,
                            emitted_a2ui_hashes,
                        )
                        if update is not None:
                            detailed_message = update["detailed_updates"]
                            if isinstance(latest_message, AIMessage):
                                final_response_content = str(getattr(latest_message, "content", "") or "")
                            if isinstance(final_fragment, list):
                                final_a2ui_messages = [msg for msg in final_fragment if isinstance(msg, dict)]
                            yield update

            await graph_task

            if final_a2ui_messages:
                final_content = (
                    f"{final_response_content.strip() if final_response_content else 'No response generated'}\n"
                    f"---a2ui_JSON---\n"
                    f"{json.dumps(final_a2ui_messages, ensure_ascii=False)}"
                )
            else:
                final_content = final_response_content or "No response generated"

            fall_back_suggestions_model = SuggestionModel().build_suggestion_model()
            raw_suggestions = await fall_back_suggestions_model.ainvoke(
                self._out_query + f"\n\nContext for question generation:\n{final_response_content}"
            )
            if not raw_suggestions:
                raw_suggestions = SuggestedQuestions(
                    suggested_questions=[
                        "Tell me more details about first data",
                        "Make a summary of data given",
                    ]
                )

            yield {
                "is_task_complete": True,
                "content": final_content,
                "detailed_updates": detailed_message,
                "token_count": str(model_token_count),
                "suggestions": raw_suggestions.model_dump_json(),
                "sources": json.dumps(source_documents),
                "a2ui_messages": final_a2ui_messages,
            }
        finally:
            self._progress_queue = None
            self.langfuse_tracing_provider.reset_current_client(client_token)
            self.langfuse_tracing_provider.reset_current_session_id(session_token)


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
    async for event in graph.call_streaming_dynamic_app(
        "What are the most common outage cause categories in the last 6 months?",
        "1234",
    ):
        event_count += 1
        elapsed = time.perf_counter() - started_at
        print(f"\n[+{elapsed:.2f}s][event={event_count}] is_complete={event.get('is_task_complete')}")
        print(event.get("updates", event.get("content", "")))

    total_elapsed = time.perf_counter() - started_at
    print(f"\nTotal request time: {total_elapsed:.2f}s across {event_count} streamed event(s).")


if __name__ == "__main__":
    asyncio.run(main())
