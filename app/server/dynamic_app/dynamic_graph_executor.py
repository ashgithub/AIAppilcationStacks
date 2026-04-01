from __future__ import annotations

import asyncio
import json
import logging

from langfuse import Langfuse

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_parts_message, new_task
from a2a.utils.errors import ServerError
from a2ui.a2a import create_a2ui_part, try_activate_a2ui_extension
from dynamic_app.dynamic_agents_graph import DynamicGraph

logger = logging.getLogger(__name__)


class DynamicGraphExecutor(AgentExecutor):
    """Executor for the real-time parallel dynamic graph pipeline."""

    def __init__(self, base_url: str, langfuse_client: Langfuse):
        self.base_url = base_url
        self.langfuse_client = langfuse_client
        self.dynamic_graph = DynamicGraph(
            base_url=self.base_url,
            langfuse_client=self.langfuse_client,
        )
        self._graph_ready = False
        self._graph_build_lock = asyncio.Lock()
        logger.info("Dynamic graph executor initialized.")

    async def _ensure_graph_ready(self) -> None:
        if self._graph_ready:
            return
        async with self._graph_build_lock:
            if self._graph_ready:
                return
            await self.dynamic_graph.build_graph()
            self._graph_ready = True
            logger.info("Dynamic graph compiled.")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_graph_ready()

        query = ""
        ui_event_part: dict | None = None
        session_id: str | None = None
        emitted_a2ui_hashes: set[str] = set()

        use_ui = try_activate_a2ui_extension(context)
        logger.info("Dynamic graph execution started | a2ui_extension=%s", use_ui)

        if context.message and context.message.parts:
            for part in context.message.parts:
                if not isinstance(part.root, DataPart):
                    continue
                data = part.root.data
                if not isinstance(data, dict):
                    continue

                metadata = data.get("metadata", {})
                if isinstance(metadata, dict):
                    metadata_session_id = metadata.get("sessionId")
                    if isinstance(metadata_session_id, str) and metadata_session_id:
                        session_id = metadata_session_id

                if "userAction" in data and isinstance(data["userAction"], dict):
                    ui_event_part = data["userAction"]
                elif "request" in data and not query:
                    query = str(data["request"])

        if ui_event_part:
            action = ui_event_part.get("name") or ui_event_part.get("actionName") or "unknown"
            event_context = ui_event_part.get("context", {})
            query = f"User submitted an event: {action} with data: {event_context}"
            logger.info("UI action received | action=%s", action)
        elif not query:
            query = context.get_user_input()

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        memory_id = session_id or task.context_id
        logger.info("Processing request | memory_id=%s", memory_id)

        async for item in self.dynamic_graph.call_dynamic_ui_graph(query, memory_id):
            if not item["is_task_complete"]:
                update_parts: list[Part] = [
                    Part(root=TextPart(text=str(item.get("updates") or ""))),
                    Part(root=TextPart(text=str(item.get("detailed_updates") or ""))),
                ]
                for ui_message in list(item.get("ui_messages") or []):
                    serialized = json.dumps(ui_message, sort_keys=True, ensure_ascii=False)
                    if serialized in emitted_a2ui_hashes:
                        continue
                    emitted_a2ui_hashes.add(serialized)
                    update_parts.append(create_a2ui_part(ui_message))

                await updater.update_status(
                    TaskState.working,
                    new_agent_parts_message(update_parts, task.context_id, task.id),
                )
                continue

            final_parts: list[Part] = []
            content = str(item.get("content") or "").strip()
            if content:
                final_parts.append(Part(root=TextPart(text=content)))

            final_parts.append(Part(root=TextPart(text=str(item.get("detailed_updates") or ""))))
            final_parts.append(Part(root=TextPart(text=str(item.get("token_count") or ""))))
            final_parts.append(Part(root=TextPart(text=str(item.get("suggestions") or ""))))
            final_parts.append(Part(root=TextPart(text=str(item.get("sources") or ""))))

            await updater.update_status(
                TaskState.completed,
                new_agent_parts_message(final_parts, task.context_id, task.id),
                final=True,
            )
            logger.info("Request completed | memory_id=%s", memory_id)
            break

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())

