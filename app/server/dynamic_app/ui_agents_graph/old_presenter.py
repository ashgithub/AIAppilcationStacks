import json
import logging
import os
from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from dotenv import load_dotenv
load_dotenv()

import jsonschema
from agent.prompt_builder import (
    A2UI_SCHEMA,
    RESTAURANT_UI_EXAMPLES,
    get_ui_prompt,
)
from agent.graph.struct import AgentConfig

logger = logging.getLogger(__name__)

AGENT_INSTRUCTION = """
    You are a UI generation assistant. You receive restaurant data and must generate the appropriate A2UI UI JSON schema for display.

    Use the provided restaurant data to populate the UI. Follow these rules:
    - Determine the number of restaurants from the data.
    - If 5 or fewer restaurants, use the SINGLE_COLUMN_LIST_EXAMPLE template.
    - If more than 5 restaurants, use the TWO_COLUMN_LIST_EXAMPLE template.
    - Populate the dataModelUpdate.contents with the restaurant information.

    Output in the format: conversational text ---a2ui_JSON--- JSON list of A2UI messages
"""

class PresenterAgent:
    """ Agent that generates A2UI schemas from restaurant data """

    def __init__(self, base_url: str, use_ui: bool = False, config: AgentConfig = None, inline_catalog: list = None):
        if config:
            self.oci_model = config.model
            self.model_temperature = config.temperature
            self.agent_name = config.name
        else:
            self.oci_model = "xai.grok-4"
            self.model_temperature = 0.7
            self.agent_name = "presenter_agent"
        self.base_url = base_url
        self.use_ui = use_ui
        self.inline_catalog = inline_catalog or []

        # Add RestaurantCard schema to inline catalog
        restaurant_card_schema = {
            "name": "restaurantcard",
            "schema": {
                "type": "object",
                "properties": {
                    "restaurants": {
                        "oneOf": [
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "cuisine": {"type": "string"},
                                        "rating": {"type": "number", "minimum": 0, "maximum": 5},
                                        "priceRange": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["name", "cuisine", "rating", "priceRange", "description"],
                                },
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"}
                                },
                                "required": ["path"],
                            },
                        ],
                    },
                },
                "required": ["restaurants"],
            },
        }

        # Check if RestaurantCard schema is already in inline_catalog
        if not any(item.get("name") == "restaurantcard" for item in self.inline_catalog):
            self.inline_catalog.append(restaurant_card_schema)

        self._agent = self._build_agent()

        # Load the A2UI_SCHEMA string into a Python object for validation
        try:
            # First, load the schema for a *single message*
            single_message_schema = json.loads(A2UI_SCHEMA)

            # The prompt instructs the LLM to return a *list* of messages.
            # Therefore, our validation schema must be an *array* of the single message schema.
            self.a2ui_schema_object = {"type": "array", "items": single_message_schema}
            logger.info(
                "A2UI_SCHEMA successfully loaded and wrapped in an array validator."
            )
        except json.JSONDecodeError as e:
            logger.error(f"CRITICAL: Failed to parse A2UI_SCHEMA: {e}")
            self.a2ui_schema_object = None

    def _build_agent(self) -> CompiledStateGraph:
        """Builds the agent for the presenter."""
        instruction = AGENT_INSTRUCTION + get_ui_prompt(
            self.base_url, RESTAURANT_UI_EXAMPLES, self.inline_catalog
        )

        oci_llm = ChatOCIGenAI(
            model_id=self.oci_model,
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature": self.model_temperature},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

        return create_agent(
            model=oci_llm,
            tools=[],
            system_prompt=instruction,
            name=self.agent_name
        )
    
    async def __call__(self, state):
        """Call the presenter agent to generate and validate UI from restaurant data."""
        data = state['messages'][-1].content

        # UI Validation and Retry Logic (adapted from oci_agent.py)
        max_retries = 1  # Total 2 attempts
        attempt = 0
        current_query_text = data

        # Ensure schema was loaded
        if self.use_ui and self.a2ui_schema_object is None:
            logger.error(
                "--- PresenterAgent: A2UI_SCHEMA is not loaded. Cannot perform UI validation. ---"
            )
            return {
                'messages': state['messages'] + [
                    AIMessage(content="I'm sorry, I'm facing an internal configuration error with my UI components.")
                ]
            }

        while attempt <= max_retries:
            attempt += 1
            logger.info(
                f"--- PresenterAgent: Validation attempt {attempt}/{max_retries + 1} ---"
            )

            messages = {'messages': [HumanMessage(content=current_query_text)]}
            response = await self._agent.ainvoke(messages)
            final_response_content = response['messages'][-1].content

            # Validate the response
            is_valid = False
            error_message = ""

            if self.use_ui:
                logger.info(
                    f"--- PresenterAgent: Validating UI response (Attempt {attempt})... ---"
                )
                try:
                    if "---a2ui_JSON---" not in final_response_content:
                        raise ValueError("Delimiter '---a2ui_JSON---' not found.")

                    text_part, json_string = final_response_content.split(
                        "---a2ui_JSON---", 1
                    )

                    if not json_string.strip():
                        raise ValueError("JSON part is empty.")

                    json_string_cleaned = (
                        json_string.strip().lstrip("```json").rstrip("```").strip()
                    )

                    if not json_string_cleaned:
                        raise ValueError("Cleaned JSON string is empty.")

                    # Parse JSON
                    parsed_json_data = json.loads(json_string_cleaned)

                    # Validate against A2UI_SCHEMA
                    logger.info(
                        "--- PresenterAgent: Validating against A2UI_SCHEMA... ---"
                    )
                    jsonschema.validate(
                        instance=parsed_json_data, schema=self.a2ui_schema_object
                    )

                    logger.info(
                        f"--- PresenterAgent: UI JSON successfully parsed AND validated against schema. "
                        f"Validation OK (Attempt {attempt}). ---"
                    )
                    is_valid = True
                    final_response_content = f"{text_part}\n---a2ui_JSON---\n{json_string}"
                except (
                    ValueError,
                    json.JSONDecodeError,
                    jsonschema.exceptions.ValidationError,
                ) as e:
                    logger.warning(
                        f"--- PresenterAgent: A2UI validation failed: {e} (Attempt {attempt}) ---"
                    )
                    logger.warning(
                        f"--- Failed response content: {final_response_content[:500]}... ---"
                    )
                    error_message = f"Validation failed: {e}."

            else:  # Not using UI, so text is always "valid"
                is_valid = True

            if is_valid:
                logger.info(
                    f"--- PresenterAgent: Response is valid. Returning final response (Attempt {attempt}). ---"
                )
                # Update the response with validated content
                validated_response = response.copy()
                validated_response['messages'][-1] = AIMessage(content=final_response_content)
                return validated_response

            # If here, validation failed
            if attempt <= max_retries:
                logger.warning(
                    f"--- PresenterAgent: Retrying... ({attempt}/{max_retries + 1}) ---"
                )
                # Prepare retry query
                current_query_text = (
                    f"Your previous response was invalid. {error_message} "
                    "You MUST generate a valid response that strictly follows the A2UI JSON SCHEMA. "
                    "The response MUST be a JSON list of A2UI messages. "
                    "Ensure the response is split by '---a2ui_JSON---' and the JSON part is well-formed. "
                    f"Please retry the original request: '{data}'"
                )
                # Loop continues for retry

        # If here, max retries exhausted
        logger.error(
            "--- PresenterAgent: Max retries exhausted. Returning error. ---"
        )
        return {
            'messages': state['messages'] + [
                AIMessage(content=(
                    "I'm sorry, I'm having trouble generating the interface for that request right now. "
                    "Please try again in a moment."
                ))
            ]
        }