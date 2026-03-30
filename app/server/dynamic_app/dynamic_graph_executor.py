"""Overall graph executor for the dynamic application."""
import asyncio
import json
import logging
import copy
import os
from dataclasses import asdict
import jsonschema
from langfuse import Langfuse
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
from a2a.utils import (
    new_agent_parts_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.a2a import create_a2ui_part, try_activate_a2ui_extension
from dynamic_app.dynamic_agents_graph import DynamicGraph
from core.dynamic_app.dynamic_struct import AgentConfig, CONFIG_SCHEMA, DEFAULT_CONFIG

logger = logging.getLogger(__name__)

# Progressive replay tuning (demo-friendly defaults).
PROGRESSIVE_UI_COMPONENT_CHUNK_SIZE = max(
    1, int(os.getenv("A2UI_PROGRESSIVE_COMPONENT_CHUNK_SIZE", "1"))
)
PROGRESSIVE_UI_STEP_DELAY_SECONDS = max(
    0.0, float(os.getenv("A2UI_PROGRESSIVE_STEP_DELAY_SECONDS", "0.35"))
)
# When false (default), only final replay emits A2UI parts. This avoids full-UI pre-emission.
ENABLE_INTERMEDIATE_A2UI_PARTS = (
    os.getenv("A2UI_ENABLE_INTERMEDIATE_PARTS", "false").strip().lower()
    in {"1", "true", "yes", "on"}
)


def _extract_inline_catalogs_from_metadata(metadata: dict[str, Any] | None) -> list:
    """Read inline catalogs from standards-aligned metadata with backward compatibility."""
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
    """Extract A2UI messages from text content using the standard delimiter."""
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
        logger.debug("Skipping non-JSON A2UI fragment in incremental update.")
        return []

    if isinstance(parsed, list):
        return [msg for msg in parsed if isinstance(msg, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    return []


def _append_unique_a2ui_parts(
    target_parts: list[Part], content: str, seen_hashes: set[str]
) -> None:
    """Parse and append unique A2UI messages as DataParts."""
    for message in _extract_a2ui_messages_from_content(content):
        serialized = json.dumps(message, sort_keys=True, ensure_ascii=False)
        if serialized in seen_hashes:
            continue
        seen_hashes.add(serialized)
        target_parts.append(create_a2ui_part(message))


def _is_layout_component(component_entry: dict[str, Any]) -> bool:
    """Heuristic for components that define structure before leaf content."""
    component_wrapper = component_entry.get("component")
    if not isinstance(component_wrapper, dict) or not component_wrapper:
        return False

    component_type = next(iter(component_wrapper.keys()))
    component_props = component_wrapper.get(component_type, {})

    if component_type in {"Column", "Row", "Card", "List", "Tabs", "Modal"}:
        return True

    if isinstance(component_props, dict):
        structural_keys = {"children", "child", "contentChild", "entryPointChild", "tabItems"}
        return any(key in component_props for key in structural_keys)

    return False


def _extract_component_references(component_entry: dict[str, Any], known_ids: set[str]) -> set[str]:
    """Collect referenced component IDs from structural fields in a component."""
    refs: set[str] = set()
    component_wrapper = component_entry.get("component")
    if not isinstance(component_wrapper, dict):
        return refs

    structural_single_keys = {"child", "contentChild", "entryPointChild", "componentId"}
    structural_list_keys = {"explicitList"}

    def walk(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
            return

        if isinstance(value, list):
            if key in structural_list_keys:
                for item in value:
                    if isinstance(item, str) and item in known_ids:
                        refs.add(item)
            else:
                for item in value:
                    walk(item, key)
            return

        if isinstance(value, str) and key in structural_single_keys and value in known_ids:
            refs.add(value)

    walk(component_wrapper)
    return refs


def _build_loading_placeholder(component_id: str) -> dict[str, Any]:
    return {
        "id": component_id,
        "component": {
            "Text": {
                "text": {"literalString": f"Loading {component_id}..."},
                "usageHint": "caption",
            }
        },
    }


def _is_loading_placeholder(component_entry: dict[str, Any]) -> bool:
    component_wrapper = component_entry.get("component")
    if not isinstance(component_wrapper, dict):
        return False

    text_component = component_wrapper.get("Text")
    if not isinstance(text_component, dict):
        return False

    text_value = text_component.get("text")
    if not isinstance(text_value, dict):
        return False

    literal = text_value.get("literalString")
    return isinstance(literal, str) and literal.startswith("Loading ")


def _chunk_list(items: list[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        return [items]
    return [items[i : i + size] for i in range(0, len(items), size)]


def _build_progressive_messages(
    messages: list[dict[str, Any]], component_chunk_size: int
) -> list[dict[str, Any]]:
    """
    Build a compliant progressive sequence from final A2UI:
    1) beginRendering messages,
    2) structural skeleton components,
    3) remaining leaf components in chunks,
    4) dataModelUpdate messages.
    """
    progressive: list[dict[str, Any]] = []
    root_by_surface: dict[str, str] = {}
    pending_surface_updates: list[dict[str, Any]] = []
    pending_data_updates: list[dict[str, Any]] = []
    passthrough: list[dict[str, Any]] = []

    for msg in messages:
        begin = msg.get("beginRendering")
        if isinstance(begin, dict):
            surface_id = begin.get("surfaceId")
            root_id = begin.get("root")
            if isinstance(surface_id, str) and isinstance(root_id, str):
                root_by_surface[surface_id] = root_id
            progressive.append(msg)
            continue

        if "surfaceUpdate" in msg:
            pending_surface_updates.append(msg)
            continue

        if "dataModelUpdate" in msg:
            pending_data_updates.append(msg)
            continue

        passthrough.append(msg)

    for msg in pending_surface_updates:
        surface_update = msg.get("surfaceUpdate", {})
        surface_id = surface_update.get("surfaceId")
        components = surface_update.get("components", [])
        if not isinstance(surface_id, str) or not isinstance(components, list):
            progressive.append(msg)
            continue

        component_map: dict[str, dict[str, Any]] = {}
        for component in components:
            if isinstance(component, dict):
                component_id = component.get("id")
                if isinstance(component_id, str):
                    component_map[component_id] = component
        known_ids = set(component_map.keys())

        root_id = root_by_surface.get(surface_id)
        root_components: list[dict[str, Any]] = []
        layout_components: list[dict[str, Any]] = []
        leaf_components: list[dict[str, Any]] = []

        for component in components:
            if not isinstance(component, dict):
                continue
            comp_id = component.get("id")
            if isinstance(root_id, str) and comp_id == root_id:
                root_components.append(component)
            elif _is_layout_component(component):
                layout_components.append(component)
            else:
                leaf_components.append(component)

        skeleton_components: list[dict[str, Any]] = []
        skeleton_ids: set[str] = set()
        for component in [*root_components, *layout_components]:
            comp_id = component.get("id")
            if isinstance(comp_id, str) and comp_id not in skeleton_ids:
                skeleton_components.append(component)
                skeleton_ids.add(comp_id)

        if not skeleton_components:
            # Fallback: start from first chunk if no clear layout layer exists.
            skeleton_components = []

        # Add placeholders for missing references used by skeleton components.
        missing_ref_ids: set[str] = set()
        for component in skeleton_components:
            for ref_id in _extract_component_references(component, known_ids):
                if ref_id not in skeleton_ids:
                    missing_ref_ids.add(ref_id)

        ordered_progressive_state: dict[str, dict[str, Any]] = {}
        placeholder_ids: set[str] = set()
        for component in skeleton_components:
            component_id = component.get("id")
            if isinstance(component_id, str):
                ordered_progressive_state[component_id] = component
        for ref_id in sorted(missing_ref_ids):
            ordered_progressive_state[ref_id] = _build_loading_placeholder(ref_id)
            placeholder_ids.add(ref_id)

        def append_progressive_step() -> None:
            progressive.append({
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": list(ordered_progressive_state.values()),
                }
            })

        if ordered_progressive_state:
            append_progressive_step()

        remaining_components: list[dict[str, Any]] = []
        seeded_real_ids = {
            component_id
            for component_id, component in ordered_progressive_state.items()
            if component_id not in placeholder_ids and not _is_loading_placeholder(component)
        }
        for component in components:
            if not isinstance(component, dict):
                continue
            component_id = component.get("id")
            # Allow real components to replace placeholders using the same ID.
            if isinstance(component_id, str) and (
                component_id not in seeded_real_ids or component_id in placeholder_ids
            ):
                remaining_components.append(component)

        for chunk in _chunk_list(remaining_components, component_chunk_size):
            for component in chunk:
                component_id = component.get("id")
                if isinstance(component_id, str):
                    ordered_progressive_state[component_id] = component
                    if component_id in placeholder_ids:
                        placeholder_ids.remove(component_id)
            append_progressive_step()

        # Finalize unresolved placeholders so the UI does not stay stuck in loading state.
        if placeholder_ids:
            for component_id in sorted(placeholder_ids):
                ordered_progressive_state[component_id] = {
                    "id": component_id,
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": f"Content unavailable for '{component_id}'."
                            },
                            "usageHint": "caption",
                        }
                    },
                }
            append_progressive_step()

        if not ordered_progressive_state and components:
            progressive.append(msg)

    progressive.extend(pending_data_updates)
    progressive.extend(passthrough)
    return progressive


def _is_pre_progressive_sequence(messages: list[dict[str, Any]]) -> bool:
    """
    Detect payloads that already contain ordered progressive updates.
    Parallel UI assembler already emits:
    beginRendering -> skeleton surfaceUpdate -> N surfaceUpdate deltas -> dataModelUpdate.
    Re-transforming that sequence creates reset/flicker behavior on the client.
    """
    surface_update_count = 0
    begin_count = 0
    seen_surfaces: set[str] = set()

    for message in messages:
        begin = message.get("beginRendering")
        if isinstance(begin, dict):
            begin_count += 1

        surface_update = message.get("surfaceUpdate")
        if isinstance(surface_update, dict):
            surface_update_count += 1
            surface_id = surface_update.get("surfaceId")
            if isinstance(surface_id, str):
                seen_surfaces.add(surface_id)

    # A single surface with multiple surface updates is already progressive.
    return begin_count >= 1 and surface_update_count >= 2 and len(seen_surfaces) <= 1


#region Executor
class DynamicGraphExecutor(AgentExecutor):
    """Executor for the full dynamic graph pipeline."""

    #region Lifecycle
    def __init__(self, base_url: str, langfuse_client: Langfuse):
        self.default_config = copy.deepcopy(DEFAULT_CONFIG)
        self.current_config = copy.deepcopy(self.default_config)
        self.base_url = base_url
        self.langfuse_client = langfuse_client
        self.progressive_component_chunk_size = PROGRESSIVE_UI_COMPONENT_CHUNK_SIZE
        self.progressive_step_delay_seconds = PROGRESSIVE_UI_STEP_DELAY_SECONDS
        self.enable_intermediate_a2ui_parts = ENABLE_INTERMEDIATE_A2UI_PARTS
        logger.info(
            "Progressive UI replay config | chunk_size=%s step_delay_s=%s intermediate_parts=%s",
            self.progressive_component_chunk_size,
            self.progressive_step_delay_seconds,
            self.enable_intermediate_a2ui_parts,
        )
        self._recreate_graphs()

    def _recreate_graphs(self):
        """Recreate graph instances with current config"""
        self.ui_dynamic_graph = DynamicGraph(
            base_url=self.base_url,
            langfuse_client=self.langfuse_client,
            use_ui=True,
            graph_configuration=self.current_config,
            inline_catalog=None  # Will be set at execution time
        )
        self._dynamic_graph = DynamicGraph(
            base_url=self.base_url,
            langfuse_client=self.langfuse_client,
            use_ui=False,
            graph_configuration=self.current_config,
            inline_catalog=None
        )
    #endregion

    #region Main Execution
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = ""
        ui_event_part = None
        action = None
        inline_catalog = []
        emitted_a2ui_hashes: set[str] = set()

        logger.info(f"--- Client requested extensions: {context.requested_extensions} ---")
        use_ui = try_activate_a2ui_extension(context)

        if use_ui:
            agent = self.ui_dynamic_graph
            await agent.build_graph()
            logger.info("--- AGENT_EXECUTOR: A2UI extension is active. Using UI agent. ---")
        else:
            agent = self._dynamic_graph
            await agent.build_graph()
            logger.info("--- AGENT_EXECUTOR: A2UI extension is not active. Using text agent. ---")

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

                    inline_catalog_from_part = _extract_inline_catalogs_from_metadata(metadata)
                    if inline_catalog_from_part:
                        inline_catalog = inline_catalog_from_part
                        logger.info(f"  Part {i}: Found {len(inline_catalog)} inline catalog(s) in metadata.")

                    if "userAction" in data:
                        logger.info(f"  Part {i}: Found a2ui UI ClientEvent payload.")
                        ui_event_part = data["userAction"]
                    elif "request" in data:
                        logger.info(f"  Part {i}: Found 'request' in DataPart.")
                        query = data["request"]
                    else:
                        logger.info(f"  Part {i}: DataPart (data: {data})")
                elif isinstance(part.root, TextPart):
                    logger.info(f"  Part {i}: TextPart (text: {part.root.text})")
                else:
                    logger.info(f"  Part {i}: Unknown part type ({type(part.root)})")

        if use_ui:
            self.ui_dynamic_graph.inline_catalog = inline_catalog
        else:
            self._dynamic_graph.inline_catalog = inline_catalog

        if inline_catalog:
            logger.info(f"--- Found inline catalog with {len(inline_catalog)} components ---")

        if ui_event_part:
            logger.info(f"Received a2ui ClientEvent: {ui_event_part}")
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
        else:
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

        async for item in agent.call_dynamic_ui_graph(query, memory_id):
            is_task_complete = item["is_task_complete"]
            if not is_task_complete:
                update_parts = []
                update_parts.append(Part(root=TextPart(text=item['updates'])))
                update_parts.append(Part(root=TextPart(text=item['detailed_updates'])))
                if self.enable_intermediate_a2ui_parts:
                    _append_unique_a2ui_parts(
                        update_parts, item.get("content", ""), emitted_a2ui_hashes
                    )
                await updater.update_status(
                    TaskState.working,
                    new_agent_parts_message(update_parts, task.context_id, task.id),
                )
                continue

            content = item["content"]
            final_parts = []
            if "---a2ui_JSON---" in content:
                logger.info("Splitting final response into text and UI parts.")
                text_content, json_string = content.split("---a2ui_JSON---", 1)

                if text_content.strip():
                    final_parts.append(Part(root=TextPart(text=text_content.strip())))

                if json_string.strip():
                    try:
                        json_string_cleaned = (json_string.strip().lstrip("```json").rstrip("```").strip())
                        json_data = json.loads(json_string_cleaned)

                        if isinstance(json_data, list):
                            ordered_messages = [
                                message for message in json_data if isinstance(message, dict)
                            ]
                            if _is_pre_progressive_sequence(ordered_messages):
                                progressive_messages = ordered_messages
                                logger.info(
                                    "Found %s final A2UI message(s) already progressive. Replaying as-is.",
                                    len(progressive_messages),
                                )
                            else:
                                logger.info(
                                    "Found %s final A2UI message(s) requiring progressive transformation.",
                                    len(ordered_messages),
                                )
                                progressive_messages = _build_progressive_messages(
                                    ordered_messages,
                                    component_chunk_size=self.progressive_component_chunk_size,
                                )
                            total_steps = len(progressive_messages)

                            for index, progressive_message in enumerate(progressive_messages):
                                serialized = json.dumps(progressive_message, sort_keys=True, ensure_ascii=False)
                                if serialized in emitted_a2ui_hashes:
                                    continue
                                emitted_a2ui_hashes.add(serialized)

                                step_parts = [
                                    Part(root=TextPart(text=f"Building interface step {index + 1}/{total_steps}")),
                                    Part(root=TextPart(text=item['detailed_updates'])),
                                    create_a2ui_part(progressive_message),
                                ]
                                await updater.update_status(
                                    TaskState.working,
                                    new_agent_parts_message(step_parts, task.context_id, task.id),
                                )
                                await asyncio.sleep(self.progressive_step_delay_seconds)
                        else:
                            logger.info("Received a single JSON object. Creating a DataPart.")
                            serialized = json.dumps(json_data, sort_keys=True, ensure_ascii=False)
                            if serialized not in emitted_a2ui_hashes:
                                emitted_a2ui_hashes.add(serialized)
                                step_parts = [
                                    Part(root=TextPart(text="Building interface step 1/1")),
                                    Part(root=TextPart(text=item['detailed_updates'])),
                                    create_a2ui_part(json_data),
                                ]
                                await updater.update_status(
                                    TaskState.working,
                                    new_agent_parts_message(step_parts, task.context_id, task.id),
                                )
                                await asyncio.sleep(self.progressive_step_delay_seconds)

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse UI JSON: {e}")
                        final_parts.append(Part(root=TextPart(text=json_string)))
            else:
                final_parts.append(Part(root=TextPart(text=content.strip())))

            final_parts.append(Part(root=TextPart(text=item['detailed_updates'])))
            final_parts.append(Part(root=TextPart(text=item['token_count'])))
            final_parts.append(Part(root=TextPart(text=item['suggestions'])))
            final_parts.append(Part(root=TextPart(text=item['sources'])))

            logger.info("--- FINAL PARTS TO BE SENT ---")
            for i, part in enumerate(final_parts):
                logger.info(f"  - Part {i}: Type = {type(part.root)}")
                if isinstance(part.root, TextPart):
                    logger.info(f"    - Text: {part.root.text[:200]}...")
                elif isinstance(part.root, DataPart):
                    logger.info(f"    - Data: {str(part.root.data)[:200]}...")
            logger.info("-----------------------------")
        
            await updater.update_status(
                TaskState.completed,
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

    #region Config Helpers
    def get_config(self) -> dict:
        """Get current configuration as a serializable dictionary."""
        return {k: asdict(v) for k, v in self.current_config.items()}

    def update_config(self, new_config: dict) -> tuple[bool, str]:
        """
        Update configuration with validation
        Returns (success, error_message)
        """
        try:
            jsonschema.validate(instance=new_config, schema=CONFIG_SCHEMA)

            config_objects = {}
            for agent_name, agent_data in new_config.items():
                config_objects[agent_name] = AgentConfig(**agent_data)

            self.current_config = config_objects

            self._recreate_graphs()

            logger.info("Configuration updated successfully")
            return True, ""

        except jsonschema.ValidationError as e:
            error_msg = f"Configuration validation failed: {e.message}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Configuration update failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def reset_config(self) -> None:
        """Reset configuration to default"""
        self.current_config = copy.deepcopy(self.default_config)
        self._recreate_graphs()
        logger.info("Configuration reset to default")
    #endregion
#endregion
