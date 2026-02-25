""" This is the overall graph executor for the dynamic application """
import json
import logging
import copy
from dataclasses import asdict
import jsonschema

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
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from a2ui.extension.a2ui_extension import create_a2ui_part, try_activate_a2ui_extension
from dynamic_app.dynamic_agents_graph import DynamicGraph
from core.dynamic_app.dynamic_struct import AgentConfig, CONFIG_SCHEMA, DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class DynamicGraphExecutor(AgentExecutor):
    """Executor of a full graph"""

    def __init__(self, base_url: str):
        self.default_config = copy.deepcopy(DEFAULT_CONFIG)
        self.current_config = copy.deepcopy(self.default_config)
        self.base_url = base_url
        self._recreate_graphs()

    def _recreate_graphs(self):
        """Recreate graph instances with current config"""
        self.ui_dynamic_graph = DynamicGraph(
            base_url=self.base_url,
            use_ui=True,
            graph_configuration=self.current_config,
            inline_catalog=None  # Will be set at execution time
        )
        self._dynamic_graph = DynamicGraph(
            base_url=self.base_url,
            use_ui=False,
            graph_configuration=self.current_config,
            inline_catalog=None  # Will be set at execution time
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = ""
        ui_event_part = None
        action = None
        inline_catalog = []

        logger.info(f"--- Client requested extensions: {context.requested_extensions} ---")
        use_ui = try_activate_a2ui_extension(context)

        # Determine which agent to use based on whether the a2ui extension is active.
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
                    if "userAction" in part.root.data:
                        logger.info(f"  Part {i}: Found a2ui UI ClientEvent payload.")
                        ui_event_part = part.root.data["userAction"]
                    elif "request" in part.root.data:
                        logger.info(f"  Part {i}: Found 'request' in DataPart.")
                        query = part.root.data["request"]

                        # Check for inline catalog
                        if "metadata" in part.root.data and "inlineCatalogs" in part.root.data["metadata"]:
                             logger.info(f"  Part {i}: Found 'inlineCatalogs' in DataPart.")
                             inline_catalog = part.root.data["metadata"]["inlineCatalogs"]

                        # Extract session ID from metadata
                        if "metadata" in part.root.data and "sessionId" in part.root.data["metadata"]:
                            session_id = part.root.data["metadata"]["sessionId"]
                            logger.info(f"  Part {i}: Found sessionId in metadata: {session_id}")
                    else:
                        logger.info(f"  Part {i}: DataPart (data: {part.root.data})")
                elif isinstance(part.root, TextPart):
                    logger.info(f"  Part {i}: TextPart (text: {part.root.text})")
                else:
                    logger.info(f"  Part {i}: Unknown part type ({type(part.root)})")

        # Set inline catalog on the agents
        if use_ui:
            self.ui_dynamic_graph.inline_catalog = inline_catalog
        else:
            self._dynamic_graph.inline_catalog = inline_catalog

        if inline_catalog:
            logger.info(f"--- Found inline catalog with {len(inline_catalog)} components ---")

        #TODO: past action items that must be removed.
        if ui_event_part:
            logger.info(f"Received a2ui ClientEvent: {ui_event_part}")
            # Changed on event name due to new version, could change in the future
            action = ui_event_part.get("name")
            ctx = ui_event_part.get("context", {})

            if action == "book_restaurant":
                restaurant_name = ctx.get("restaurantName", "Unknown Restaurant")
                address = ctx.get("address", "Address not provided")
                image_url = ctx.get("imageUrl", "")
                query = f"USER_WANTS_TO_BOOK: {restaurant_name}, Address: {address}, ImageURL: {image_url}"

            elif action == "submit_booking":
                restaurant_name = ctx.get("restaurantName", "Unknown Restaurant")
                party_size = ctx.get("partySize", "Unknown Size")
                reservation_time = ctx.get("reservationTime", "Unknown Time")
                dietary_reqs = ctx.get("dietary", "None")
                image_url = ctx.get("imageUrl", "")
                query = f"User submitted a booking for {restaurant_name} for {party_size} people at {reservation_time} with dietary requirements: {dietary_reqs}. The image URL is {image_url}"

            else:
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

        # MAIN execution method
        async for item in agent.call_dynamic_ui_graph(query, memory_id):
            is_task_complete = item["is_task_complete"]
            if not is_task_complete:
                update_parts = []
                update_parts.append(Part(root=TextPart(text=item['updates'])))
                update_parts.append(Part(root=TextPart(text=item['detailed_updates'])))
                await updater.update_status(
                    TaskState.working,
                    new_agent_parts_message(update_parts, task.context_id, task.id),
                )
                continue

            final_state = (
                TaskState.completed
                if action == "submit_booking"
                else TaskState.input_required
            )

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
                            logger.info(f"Found {len(json_data)} messages. Creating individual DataParts.")
                            for message in json_data:
                                final_parts.append(create_a2ui_part(message))
                        else:
                            # Handle the case where a single JSON object is returned
                            logger.info("Received a single JSON object. Creating a DataPart.")
                            final_parts.append(create_a2ui_part(json_data))

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse UI JSON: {e}")
                        final_parts.append(Part(root=TextPart(text=json_string)))
            else:
                final_parts.append(Part(root=TextPart(text=content.strip())))

            final_parts.append(Part(root=TextPart(text=item['detailed_updates'])))
            final_parts.append(Part(root=TextPart(text=item['token_count'])))
            final_parts.append(Part(root=TextPart(text=item['suggestions'])))

            logger.info("--- FINAL PARTS TO BE SENT ---")
            for i, part in enumerate(final_parts):
                logger.info(f"  - Part {i}: Type = {type(part.root)}")
                if isinstance(part.root, TextPart):
                    logger.info(f"    - Text: {part.root.text[:200]}...")
                elif isinstance(part.root, DataPart):
                    logger.info(f"    - Data: {str(part.root.data)[:200]}...")
            logger.info("-----------------------------")
            # TODO: remove in case multiturn is enabled
            final_state = TaskState.completed

            await updater.update_status(
                final_state,
                new_agent_parts_message(final_parts, task.context_id, task.id),
                final=(final_state == TaskState.completed),
            )
            break

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())

    # region helper config
    def get_config(self) -> dict:
        """Get current configuration as dict"""
        return {k: asdict(v) for k, v in self.current_config.items()}

    def update_config(self, new_config: dict) -> tuple[bool, str]:
        """
        Update configuration with validation
        Returns (success, error_message)
        """
        try:
            # Validate JSON schema
            jsonschema.validate(instance=new_config, schema=CONFIG_SCHEMA)

            # Convert to AgentConfig objects
            config_objects = {}
            for agent_name, agent_data in new_config.items():
                config_objects[agent_name] = AgentConfig(**agent_data)

            # Update current config
            self.current_config = config_objects

            # Recreate graphs with new config
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
