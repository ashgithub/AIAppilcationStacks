import logging
import json
from typing import Any

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
from a2a.utils import (
    new_agent_parts_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.a2a import create_a2ui_part
from chat_app.main_llm import OCIOutageEnergyLLM

logger = logging.getLogger(__name__)


def _extract_a2ui_messages_from_content(content: str) -> list[dict[str, Any]]:
    """Extract A2UI messages from delimited content blocks."""
    if not isinstance(content, str) or "---a2ui_JSON---" not in content:
        return []

    _, json_string = content.split("---a2ui_JSON---", 1)
    cleaned = json_string.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    if not cleaned:
        return []

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("Skipping non-JSON A2UI fragment in LLM update.")
        return []

    if isinstance(parsed, list):
        return [msg for msg in parsed if isinstance(msg, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _append_unique_a2ui_parts(
    target_parts: list[Part], content: str, seen_hashes: set[str]
) -> None:
    for message in _extract_a2ui_messages_from_content(content):
        serialized = json.dumps(message, sort_keys=True, ensure_ascii=False)
        if serialized in seen_hashes:
            continue
        seen_hashes.add(serialized)
        target_parts.append(create_a2ui_part(message))


#region Executor
class OutageEnergyLLMExecutor(AgentExecutor):
    """Executor for outage and energy chat flows."""

    #region Lifecycle
    def __init__(self, langfuse_client: Langfuse):
        self.oci_ui_agent = OCIOutageEnergyLLM(langfuse_client)
        self.oci_text_agent = OCIOutageEnergyLLM(langfuse_client)
    #endregion

    #region Main Execution
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = ""
        emitted_a2ui_hashes: set[str] = set()

        logger.info(
            f"--- Client requested extensions: {context.requested_extensions} ---"
        )

        agent = self.oci_text_agent

        session_id = None
        if context.message and context.message.parts:
            logger.info(
                f"--- AGENT_EXECUTOR: Processing {len(context.message.parts)} message parts ---"
            )
            for i, part in enumerate(context.message.parts):
                if isinstance(part.root, DataPart):
                    data = part.root.data
                    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}

                    if "sessionId" in metadata:
                        session_id = metadata["sessionId"]
                        logger.info(f"  Part {i}: Found sessionId in metadata: {session_id}")

                    if "userAction" in data:
                        logger.info(f"  Part {i}: Found a2ui UI ClientEvent payload.")
                        ui_event_part = data["userAction"]
                    elif "request" in data:
                        logger.info(f"  Part {i}: Found request in DataPart.")
                        query = data["request"]
                    else:
                        logger.info(f"  Part {i}: DataPart (data: {data})")
                elif isinstance(part.root, TextPart):
                    logger.info(f"  Part {i}: TextPart (text: {part.root.text})")
                    if not query:
                        query = part.root.text
                else:
                    logger.info(f"  Part {i}: Unknown part type ({type(part.root)})")

        if not query:
            logger.info("No a2ui UI event part found. Falling back to text input.")
            query = context.get_user_input()

        logger.info(f"--- AGENT_EXECUTOR: Final query for LLM: '{query}' ---")

        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        memory_id = session_id if session_id else task.context_id
        logger.info(f"--- AGENT_EXECUTOR: Using memory ID: {memory_id} ---")

        async for item in agent.oci_stream(query, memory_id):
            is_task_complete = item["is_task_complete"]
            if not is_task_complete:
                update_parts = [Part(root=TextPart(text=item["updates"]))]
                _append_unique_a2ui_parts(update_parts, item.get("content", ""), emitted_a2ui_hashes)
                await updater.update_status(
                    TaskState.working,
                    new_agent_parts_message(update_parts, task.context_id, task.id),
                )
                continue
            
            content = item["content"]
            final_parts = []
            if "---a2ui_JSON---" in content:
                text_content, _ = content.split("---a2ui_JSON---", 1)
                if text_content.strip():
                    final_parts.append(Part(root=TextPart(text=text_content.strip())))
            else:
                final_parts.append(Part(root=TextPart(text=content.strip())))

            _append_unique_a2ui_parts(final_parts, content, emitted_a2ui_hashes)

            final_state = item['final_state']
            final_parts.append(Part(root=TextPart(text=final_state.strip())))

            final_token_count = item['token_count']
            final_parts.append(Part(root=TextPart(text=final_token_count.strip())))

            suggestions = item['suggestions']
            final_parts.append(Part(root=TextPart(text=suggestions.strip())))

            sources = item.get('sources', '[]')
            final_parts.append(Part(root=TextPart(text=sources.strip())))

            # Keep a stable payload order for clients:
            # answer, model state, token count, suggestions, sources.
            logger.info("--- FINAL PARTS TO BE SENT ---")
            for i, part in enumerate(final_parts):
                logger.info(f"  - Part {i}: Type = {type(part.root)}")
                if isinstance(part.root, TextPart):
                    logger.info(f"    - Text: {part.root.text[:200]}...")
                elif isinstance(part.root, DataPart):
                    logger.info(f"    - Data: {str(part.root.data)[:200]}...")
            logger.info("-----------------------------")

            final_state = TaskState.completed

            await updater.update_status(
                final_state,
                new_agent_parts_message(final_parts, task.context_id, task.id),
                final=True,
            )
            break
    #endregion

    #region Cancellation
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
    #endregion
#endregion
