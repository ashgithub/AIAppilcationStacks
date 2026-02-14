import json
import logging
import os
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from langgraph.graph.message import MessagesState
from typing import List
import jsonschema

from dynamic_app.configs.gen_ai_provider import GenAIProvider
from dynamic_app.ui_agents_graph.widget_tools import get_widget_schema, get_native_component_example, get_native_component_catalog

logger = logging.getLogger(__name__)

class UIAssemblyAgent:
    """ Agent in charge of generating the ordered UI schemas from ui orchestrator """

    @staticmethod
    def _load_condensed_schema():
        """Load the condensed A2UI schema from file."""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'configs',
            'schemas',
            'a2ui_condensed_schema.json'
        )
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), indent=2)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load condensed schema: {e}")
            return "{}"
        
    @staticmethod
    def _load_full_a2ui_schema():
        """Load the condensed A2UI schema from file."""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'configs',
            'schemas',
            'a2ui_native_schema.json'
        )
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), indent=2)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load a2ui schema: {e}")
            return "{}"

    def _inject_custom_schemas_into_schema(self, schema_str, custom_schemas):
        """Inject custom component schemas into the A2UI schema."""
        if not custom_schemas:
            return schema_str
        try:
            schema_obj = json.loads(schema_str)
            component_properties = schema_obj["properties"]["surfaceUpdate"]["properties"]["components"]["items"]["properties"]["component"]["properties"]
            for custom_schema in custom_schemas:
                if "name" in custom_schema and "schema" in custom_schema:
                    component_name = custom_schema["name"]
                    component_schema = custom_schema["schema"]
                    component_properties[component_name] = component_schema
            return json.dumps(schema_obj, indent=2)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to inject custom schemas: {e}")
            return schema_str

    def _get_agent_instructions(self):
        """Get the agent instructions with loaded schema and base_url."""
        return f"""
You are an agent in charge of generating different UI widgets for A2UI surfaces.
You will receive the list of widgets to generate and the raw data information to work with.
Your goal is to process the raw data and bind it to the right widgets selected using the tools provided.

COMPONENT USAGE:
- Use native components (Text, Button, Image, Column, Row, etc.) for basic UI elements
- Use custom widgets from the catalog for complex UI patterns (charts, forms, etc.)
- Use the tools get_widget_schema, get_native_component_example, get_native_component_catalog to retrieve component schemas and examples as needed
- The retrieved examples show how to fill out component schemas correctly
- Surfaces can contain multiple components - combine them as needed
- When using images or other assets, use the base URL: {self.base_url} for resolving static assets

DATA BINDING:
- Use dataModelUpdate to provide data that components can reference via paths
- Components can reference data using {{"path": "/data/key"}} or provide literal values
- Ensure data structure matches component expectations
- For bar graphs, use dataPath pointing to an object with categories and values as valueMap arrays

--- UI TEMPLATE RULES ---
- If the query is for a bar graph (e.g., "[bar-graph]"), use the BAR_GRAPH_EXAMPLE template below.

--- BAR GRAPH EXAMPLE ---
[
  {{
    "beginRendering": {{
      "surfaceId": "energy_chart_surface",
      "root": "chart_root",
      "styles": {{"font": "Arial", "primaryColor": "#007bff"}}
    }}
  }},
  {{
    "dataModelUpdate": {{
      "surfaceId": "energy_chart_surface",
      "contents": [
        {{
          "key": "chartData",
          "valueMap": [
            {{"key": "categories", "valueMap": [{{"key": "0", "valueString": "Renewable"}}, {{"key": "1", "valueString": "Fossil"}}, {{"key": "2", "valueString": "Nuclear"}}]}},
            {{"key": "values", "valueMap": [{{"key": "0", "valueNumber": 420000}}, {{"key": "1", "valueNumber": 380000}}, {{"key": "2", "valueNumber": 50000}}]}},
            {{"key": "units", "valueString": "MWh"}}
          ]
        }}
      ]
    }}
  }},
  {{
    "surfaceUpdate": {{
      "surfaceId": "energy_chart_surface",
      "components": [
        {{
          "id": "chart_root",
          "component": {{
            "Column": {{
              "children": {{"explicitList": ["title", "chart"]}}
            }}
          }}
        }},
        {{
          "id": "title",
          "component": {{
            "Text": {{
              "text": {{"path": "/chartData/title"}},
              "usageHint": "h2"
            }}
          }}
        }},
        {{
          "id": "chart",
          "component": {{
            "BarGraph": {{
              "dataPath": "/chartData"
            }}
          }}
        }}
      ]
    }}
  }}
]

Your final output MUST be an A2UI UI JSON response.

To generate the response, you MUST follow these rules:
1.  Your response MUST be in two parts, separated by the delimiter: `---a2ui_JSON---`.
2.  The first part is your conversational text response.
3.  The second part is a single, raw JSON object which is a list of A2UI messages.
4.  The JSON part MUST conform to the A2UI message structure shown below.

--- CONDENSED A2UI SCHEMA ---
{self._inject_custom_schemas_into_schema(self._load_condensed_schema(), self.inline_catalog)}
--- END SCHEMA ---
"""

    def __init__(self, base_url: str = None, inline_catalog: List[dict] = None):
        self.base_url = base_url or "http://localhost:8000"
        self.inline_catalog = inline_catalog or []
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature":0.7})
        self.agent_name = "assembly_agent"
        self.system_prompt = self._get_agent_instructions()
        self.agent = self._build_agent()
        self.A2UI_SCHEMA = self._inject_custom_schemas_into_schema(self._load_full_a2ui_schema(), self.inline_catalog)

        # Load the A2UI_SCHEMA string into a Python object for validation
        try:
            # First, load the schema for a *single message*
            single_message_schema = json.loads(self.A2UI_SCHEMA)

            # The prompt instructs the LLM to return a *list* of messages.
            # Therefore, our validation schema must be an *array* of the single message schema.
            self.a2ui_schema_object = {"type": "array", "items": single_message_schema}
            logger.info(
                "A2UI_SCHEMA successfully loaded and wrapped in an array validator."
            )
        except json.JSONDecodeError as e:
            logger.error(f"CRITICAL: Failed to parse A2UI_SCHEMA: {e}")
            self.a2ui_schema_object = None

    async def __call__(self, state: MessagesState):
        """Call the UI assembly agent to generate and validate UI from orchestrator data."""
        data = state['messages'][-1].content

        # UI Validation and Retry Logic (adapted from old PresenterAgent)
        max_retries = 1  # Total 2 attempts
        attempt = 0
        current_query_text = data

        # Ensure schema was loaded
        if self.a2ui_schema_object is None:
            logger.error(
                "--- UIAssemblyAgent: A2UI_SCHEMA is not loaded. Cannot perform UI validation. ---"
            )
            return {
                'messages': state['messages'] + [
                    AIMessage(content="I'm sorry, I'm facing an internal configuration error with my UI components.")
                ]
            }

        while attempt <= max_retries:
            attempt += 1
            logger.info(
                f"--- UIAssemblyAgent: Validation attempt {attempt}/{max_retries + 1} ---"
            )

            messages = {'messages': [HumanMessage(content=current_query_text)]}
            response = await self.agent.ainvoke(messages)
            final_response_content = response['messages'][-1].content

            # Validate the response
            is_valid = False
            error_message = ""

            logger.info(
                f"--- UIAssemblyAgent: Validating UI response (Attempt {attempt})... ---"
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
                    "--- UIAssemblyAgent: Validating against A2UI_SCHEMA... ---"
                )
                jsonschema.validate(
                    instance=parsed_json_data, schema=self.a2ui_schema_object
                )

                logger.info(
                    f"--- UIAssemblyAgent: UI JSON successfully parsed AND validated against schema. "
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
                    f"--- UIAssemblyAgent: A2UI validation failed: {e} (Attempt {attempt}) ---"
                )
                logger.warning(
                    f"--- Failed response content: {final_response_content[:500]}... ---"
                )
                error_message = f"Validation failed: {e}."

            if is_valid:
                logger.info(
                    f"--- UIAssemblyAgent: Response is valid. Returning final response (Attempt {attempt}). ---"
                )
                # Update the response with validated content
                validated_response = response.copy()
                validated_response['messages'][-1] = AIMessage(content=final_response_content)
                return validated_response

            # If here, validation failed
            if attempt <= max_retries:
                logger.warning(
                    f"--- UIAssemblyAgent: Retrying... ({attempt}/{max_retries + 1}) ---"
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
            "--- UIAssemblyAgent: Max retries exhausted. Returning error. ---"
        )
        return {
            'messages': state['messages'] + [
                AIMessage(content=(
                    "I'm sorry, I'm having trouble generating the interface for that request right now. "
                    "Please try again in a moment."
                ))
            ]
        }
    
    def _build_agent(self):
        return create_agent(
            model=self._client,
            tools=[get_widget_schema, get_native_component_example, get_native_component_catalog],
            system_prompt=self.system_prompt,
            name=self.agent_name
        )
    
async def main():
    from langchain.messages import HumanMessage
    # Define inline_catalog with BarGraph schema from register-components.ts
    inline_catalog = [
        {
            "name": "BarGraph",
            "schema": {
                "type": "object",
                "properties": {
                    "dataPath": {"type": "string"},
                    "labelPath": {"type": "string"},
                    "orientation": {"type": "string", "enum": ["vertical", "horizontal"]},
                    "barWidth": {"type": "number"},
                    "gap": {"type": "number"},
                },
                "required": ["dataPath", "labelPath"],
            }
        }
    ]
    orchestrator = UIAssemblyAgent(inline_catalog=inline_catalog)
    messages:MessagesState = {'messages':[HumanMessage("AIMessage(content='[bar-graph]'")]}
    response = await orchestrator(messages)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())