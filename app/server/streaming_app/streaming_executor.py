"""Overall graph executor for the streaming application."""

import json
import logging
from typing import Any

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
from langfuse import Langfuse

from streaming_app.streaming_graph import StreamingDynamicApp

logger = logging.getLogger(__name__)


def _extract_inline_catalogs_from_metadata(metadata: dict[str, Any] | None) -> list:
    if not isinstance(metadata, dict):
        return []

    capabilities = metadata.get("a2uiClientCapabilities")
    if isinstance(capabilities, dict):
        inline_catalogs = capabilities.get("inlineCatalogs")
        if isinstance(inline_catalogs, list):
            return inline_catalogs

    legacy_inline_catalogs = metadata.get("inlineCatalogs")
    if isinstance(legacy_inline_catalogs, list):
        return legacy_inline_catalogs

    return []


def _extract_a2ui_messages_from_content(content: str) -> list[dict[str, Any]]:
    if not isinstance(content, str) or "---a2ui_JSON---" not in content:
        return []

    _, json_string = content.split("---a2ui_JSON---", 1)
    cleaned = json_string.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json") :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    if not cleaned:
        return []

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("Skipping non-JSON A2UI fragment in streaming update.")
        return []

    if isinstance(parsed, list):
        return [msg for msg in parsed if isinstance(msg, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _append_unique_a2ui_dicts(
    target_parts: list[Part],
    messages: list[dict[str, Any]],
    seen_hashes: set[str],
) -> None:
    for message in messages:
        if not isinstance(message, dict):
            continue
        serialized = json.dumps(message, sort_keys=True, ensure_ascii=False)
        if serialized in seen_hashes:
            continue
        seen_hashes.add(serialized)
        target_parts.append(create_a2ui_part(message))


def _append_unique_a2ui_parts_from_content(
    target_parts: list[Part], content: str, seen_hashes: set[str]
) -> None:
    _append_unique_a2ui_dicts(target_parts, _extract_a2ui_messages_from_content(content), seen_hashes)


class StreamingGraphExecutor(AgentExecutor):
    """Executor for the streaming graph pipeline."""

    def __init__(self, base_url: str, langfuse_client: Langfuse):
        self.base_url = base_url
        self.langfuse_client = langfuse_client
        self.ui_streaming_graph = StreamingDynamicApp(
            base_url=self.base_url,
            langfuse_client=self.langfuse_client,
            use_ui=True,
            inline_catalog=None,
        )
        self._streaming_graph = StreamingDynamicApp(
            base_url=self.base_url,
            langfuse_client=self.langfuse_client,
            use_ui=False,
            inline_catalog=None,
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = ""
        ui_event_part = None
        inline_catalog = []
        emitted_a2ui_hashes: set[str] = set()

        logger.info("--- Client requested extensions: %s ---", context.requested_extensions)
        use_ui = try_activate_a2ui_extension(context)

        if use_ui:
            agent = self.ui_streaming_graph
            await agent.build_graph()
            logger.info("--- STREAMING_EXECUTOR: A2UI extension active. Using UI streaming agent. ---")
        else:
            agent = self._streaming_graph
            await agent.build_graph()
            logger.info("--- STREAMING_EXECUTOR: A2UI extension inactive. Using text streaming agent. ---")

        session_id = None
        if context.message and context.message.parts:
            logger.info("--- STREAMING_EXECUTOR: Processing %s message parts ---", len(context.message.parts))
            for i, part in enumerate(context.message.parts):
                if isinstance(part.root, DataPart):
                    data = part.root.data
                    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}

                    if "sessionId" in metadata:
                        session_id = metadata["sessionId"]
                        logger.info("  Part %s: Found sessionId in metadata: %s", i, session_id)

                    inline_catalog_from_part = _extract_inline_catalogs_from_metadata(metadata)
                    if inline_catalog_from_part:
                        inline_catalog = inline_catalog_from_part
                        logger.info(
                            "  Part %s: Found %s inline catalog(s) in metadata.",
                            i,
                            len(inline_catalog),
                        )

                    if "userAction" in data:
                        logger.info("  Part %s: Found a2ui UI ClientEvent payload.", i)
                        ui_event_part = data["userAction"]
                    elif "request" in data:
                        logger.info("  Part %s: Found 'request' in DataPart.", i)
                        query = data["request"]
                    else:
                        logger.info("  Part %s: DataPart (data: %s)", i, data)
                elif isinstance(part.root, TextPart):
                    logger.info("  Part %s: TextPart (text: %s)", i, part.root.text)
                    if not query:
                        query = part.root.text
                else:
                    logger.info("  Part %s: Unknown part type (%s)", i, type(part.root))

        if use_ui:
            self.ui_streaming_graph.inline_catalog = inline_catalog
        else:
            self._streaming_graph.inline_catalog = inline_catalog

        if ui_event_part:
            action = ui_event_part.get("name") or ui_event_part.get("actionName")
            surface_id = ui_event_part.get("surfaceId")
            source_component_id = ui_event_part.get("sourceComponentId")
            timestamp = ui_event_part.get("timestamp")
            ctx = ui_event_part.get("context", {})

            logger.info(
                "USER_ACTION received | action=%s surface_id=%s source_component_id=%s timestamp=%s context=%s",
                action,
                surface_id,
                source_component_id,
                timestamp,
                ctx,
            )
            query = f"User submitted an event: {action} with data: {ctx}"
        elif not query:
            logger.info("No explicit request found. Falling back to text input.")
            query = context.get_user_input()

        logger.info("--- STREAMING_EXECUTOR: Final query for LLM: '%s' ---", query)

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        memory_id = session_id if session_id else task.context_id
        logger.info("--- STREAMING_EXECUTOR: Using memory ID: %s ---", memory_id)

        async for item in agent.call_streaming_dynamic_app(query, memory_id):
            if not item.get("is_task_complete", False):
                update_parts = [
                    Part(root=TextPart(text=str(item.get("updates", "")))),
                    Part(root=TextPart(text=str(item.get("detailed_updates", "")))),
                ]
                _append_unique_a2ui_dicts(
                    update_parts,
                    item.get("a2ui_messages", []),
                    emitted_a2ui_hashes,
                )
                await updater.update_status(
                    TaskState.working,
                    new_agent_parts_message(update_parts, task.context_id, task.id),
                )
                continue

            content = str(item.get("content", ""))
            final_parts: list[Part] = []

            if "---a2ui_JSON---" in content:
                text_content, _ = content.split("---a2ui_JSON---", 1)
                if text_content.strip():
                    final_parts.append(Part(root=TextPart(text=text_content.strip())))
            else:
                final_parts.append(Part(root=TextPart(text=content.strip())))

            _append_unique_a2ui_dicts(
                final_parts,
                item.get("a2ui_messages", []),
                emitted_a2ui_hashes,
            )
            _append_unique_a2ui_parts_from_content(final_parts, content, emitted_a2ui_hashes)

            final_parts.append(Part(root=TextPart(text=str(item.get("detailed_updates", "")))))
            final_parts.append(Part(root=TextPart(text=str(item.get("token_count", "0")))))
            final_parts.append(Part(root=TextPart(text=str(item.get("suggestions", "")))))
            final_parts.append(Part(root=TextPart(text=str(item.get("sources", "[]")))))

            logger.info("--- STREAMING FINAL PARTS TO BE SENT ---")
            for i, part in enumerate(final_parts):
                logger.info("  - Part %s: Type = %s", i, type(part.root))
                if isinstance(part.root, TextPart):
                    logger.info("    - Text: %s...", part.root.text[:200])
                elif isinstance(part.root, DataPart):
                    logger.info("    - Data: %s...", str(part.root.data)[:200])
            logger.info("---------------------------------------")

            await updater.update_status(
                TaskState.completed,
                new_agent_parts_message(final_parts, task.context_id, task.id),
                final=True,
            )
            break

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
