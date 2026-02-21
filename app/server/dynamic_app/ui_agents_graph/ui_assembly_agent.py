import json
import logging
import os
import jsonschema
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from typing import List

from dynamic_app.ui_agents_graph.widget_tools import get_native_component_example, create_custom_component_tools
from core.gen_ai_provider import GenAIProvider
from core.dynamic_app.dynamic_struct import DynamicGraphState

logger = logging.getLogger(__name__)

class UIAssemblyAgent:
    """ Agent in charge of generating the ordered UI schemas from ui orchestrator """

    #region helpers
    @staticmethod
    def _load_full_a2ui_schema():
        """Load the condensed A2UI schema from file."""
        schema_path = os.path.join(os.path.dirname(__file__),'..','configs','schemas','a2ui_native_schema.json')
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), indent=2)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load a2ui schema: {e}")
            return "{}"

    def _inject_custom_schemas_into_schema(self, schema_str, custom_schemas, allowed_components=None):
        """Inject custom component schemas into the A2UI schema, optionally filtering to allowed components."""
        if not custom_schemas:
            return schema_str
        try:
            schema_obj = json.loads(schema_str)
            component_properties = schema_obj["properties"]["surfaceUpdate"]["properties"]["components"]["items"]["properties"]["component"]["properties"]
            for custom_schema in custom_schemas:
                if "name" in custom_schema and "schema" in custom_schema:
                    component_name = custom_schema["name"]
                    # If allowed_components specified, only include those
                    if allowed_components and component_name.lower() not in [c.lower() for c in allowed_components]:
                        continue
                    component_schema = custom_schema["schema"]
                    component_properties[component_name] = component_schema
            return json.dumps(schema_obj, indent=2)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to inject custom schemas: {e}")
            return schema_str

    def _extract_allowed_components(self, data: str) -> List[str]:
        """Extract the list of allowed component names from orchestrator output."""
        try:
            # Try to parse as UIOrchestratorOutput JSON
            parsed = json.loads(data)
            if isinstance(parsed, dict) and 'widgets' in parsed:
                # It's UIOrchestratorOutput format
                return [widget.get('name', '').lower() for widget in parsed['widgets']]
        except (json.JSONDecodeError, TypeError):
            return ['bar-graph']

    def _get_agent_instructions(self, allowed_components, data_context: str):
        """Get the agent instructions with loaded schema and base_url."""
        self.allowed_str = ", ".join(allowed_components) if allowed_components else "any available"

        # Identify which components are custom (have schemas in CUSTOM_CATALOG)
        from core.dynamic_app.schemas.widget_schemas.a2ui_custom_catalog_list import CUSTOM_CATALOG
        custom_components = [comp for comp in allowed_components
                           if any(cat["widget-name"].lower() == comp.lower() for cat in CUSTOM_CATALOG)]

        # Build dynamic requirements for custom components
        requirements = []
        if custom_components:
            requirements.append("CRITICAL: For all custom components, you MUST call get_custom_component_example() FIRST and use the EXACT schema structures provided.")
            for comp in custom_components:
                requirements.append(f"- {comp}: Use get_custom_component_example('{comp}') and follow the schema exactly")

        requirements_str = "\n".join(requirements) if requirements else ""

        return f"""
You are an A2UI UI generation agent. Your task is to create valid A2UI message arrays that will render dynamic user interfaces based SOLELY on the orchestrator's component selection and available examples.

ORCHESTRATOR COMPONENT SELECTION: {self.allowed_str}
You MUST include and properly configure all the orchestrator-selected components above.

ADDITIONAL COMPONENTS: You may also use native A2UI components (Text, Button, Image, Icon, Row, Column, Card, etc.) for layout, styling, and user interaction purposes.

DATA TO VISUALIZE:
{data_context}
Extract and structure only the data relevant to the selected components. Ignore any data that doesn't pertain to the allowed components.

{requirements_str}

MANDATORY STEP-BY-STEP PROCESS:
1. FIRST: Call get_custom_component_catalog() to see all available custom components.
2. For EACH orchestrator-selected component that appears in the catalog: Call get_custom_component_example(component_name) and COPY the component structure EXACTLY.
3. For ANY native components you want to use: Call get_native_component_catalog() to see options, then call get_native_component_example(component_name) and COPY the structure EXACTLY.
4. NEVER invent component structures - ALWAYS copy from tool examples.
5. NEVER modify property names, data paths, or structures from the examples.
6. Build the A2UI message by combining the copied component structures.

COMPONENT USAGE RULES:
- For custom components: Use EXACTLY the structure from get_custom_component_example()
- For native components: Use EXACTLY the structure from get_native_component_example()
- Data paths must match the examples exactly (e.g., "/chartData", "/chartLabels")
- Component property names must match examples exactly
- Prioritize vertical layout for complex widget groups (columns, vertical).
- If an example uses {{"path": "/data"}}, you MUST use {{"path": "/data"}} - do not change to "/data"

EXAMPLE A2UI MESSAGE STRUCTURE:
[
  {{
    "beginRendering": {{
      "surfaceId": "dashboard",
      "root": "main-container",
      "styles": {{"font": "Arial", "primaryColor": "#007bff"}}
    }}
  }},
  {{
    "surfaceUpdate": {{
      "surfaceId": "dashboard",
      "components": [
        {{
          "id": "main-container",
          "component": {{"Column": {{"children": {{"explicitList": ["title", "chart"]}}}}}}
        }},
        {{
          "id": "title",
          "component": {{"Text": {{"text": {{"literalString": "Industry Growth Rates"}}, "usageHint": "h2"}}}}
        }},
        {{
          "id": "chart",
          "component": {{"BarGraph": {{"dataPath": "/values", "labelPath": "/labels"}}}}
        }}
      ]
    }}
  }},
  {{
    "dataModelUpdate": {{
      "surfaceId": "dashboard",
      "contents": [
        {{
          "key": "labels",
          "valueMap": [
            {{"key": "0", "valueString": "Manufacturing"}},
            {{"key": "1", "valueString": "Technology"}},
            {{"key": "2", "valueString": "Healthcare"}}
          ]
        }},
        {{
          "key": "values",
          "valueMap": [
            {{"key": "0", "valueNumber": 3.2}},
            {{"key": "1", "valueNumber": 8.7}},
            {{"key": "2", "valueNumber": 4.1}}
          ]
        }}
      ]
    }}
  }}
]

OUTPUT FORMAT:
First, provide a brief conversational response.
Then `---a2ui_JSON---`
Then the complete JSON array of A2UI messages (no markdown code blocks).

MANDATORY TOOLS USAGE:
- Always start with get_custom_component_catalog() to see available custom components
- For each allowed custom component: get_custom_component_example(component_name)
- Use get_native_component_example(component_name) for native components
- Use get_native_component_catalog() to see available native options

Generate a complete, valid A2UI message array that uses ONLY the allowed components from the orchestrator selection and follows the EXACT predefined schema structures from the tools. Ignore any irrelevant data.
"""
    #region agent logic
    def __init__(self, base_url: str = None, inline_catalog: List[dict] = None):
        self.base_url = base_url or "http://localhost:8000"
        self.inline_catalog = inline_catalog or []

        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature":0.7})
        self.agent_name = "assembly_agent"

        # Initialize with no restrictions - will be set per call
        self.allowed_components = None
        self.system_prompt = None
        self.agent = None

        # Schema will be loaded per call with filtering
        self.a2ui_schema_object = None

    def _build_agent(self):
        return create_agent(
            model=self._client,
            tools=[self.get_custom_component_example_tool, get_native_component_example],
            system_prompt=self.system_prompt,
            name=self.agent_name
        )

    async def __call__(self, state: DynamicGraphState):
        """Call the UI assembly agent to generate and validate UI from orchestrator data."""
        orchestrator_data = state['messages'][-1].content

        # Parse the orchestrator output to extract allowed components
        allowed_components = self._extract_allowed_components(orchestrator_data)

        # Extract data from message history
        data_context = state['messages'][-2].content

        # Load schema with filtering for allowed components
        self.A2UI_SCHEMA = self._inject_custom_schemas_into_schema(
            self._load_full_a2ui_schema(),
            self.inline_catalog,
            allowed_components
        )

        # Load the A2UI_SCHEMA string into a Python object for validation
        try:
            single_message_schema = json.loads(self.A2UI_SCHEMA)
            self.a2ui_schema_object = {"type": "array", "items": single_message_schema}
            logger.info("A2UI_SCHEMA successfully loaded and wrapped in an array validator.")
        except json.JSONDecodeError as e:
            logger.error(f"CRITICAL: Failed to parse A2UI_SCHEMA: {e}")
            self.a2ui_schema_object = None

        # Set up agent with restrictions
        self.allowed_components = allowed_components
        self.system_prompt = self._get_agent_instructions(allowed_components, data_context)

        # Create custom tools with restrictions
        self.get_custom_component_catalog_tool, self.get_custom_component_example_tool = create_custom_component_tools(
            self.inline_catalog, allowed_components
        )

        # Build the agent with the restricted tools
        self.agent = self._build_agent()

        # UI Validation and Retry Logic (adapted from old PresenterAgent)
        max_retries = 1  # Total 2 attempts (keeping retries as model can make mistakes)
        attempt = 0
        current_query_text = f"""Orchestrator component selection: {orchestrator_data}

Data to visualize: {data_context}

INSTRUCTIONS: You must FIRST call the required tools to get component examples, THEN generate the A2UI JSON. Do not attempt to generate JSON without calling the tools first.

REQUIRED TOOL CALLS:
1. Call get_custom_component_catalog() immediately
2. For each component in [{self.allowed_str}], call get_custom_component_example() if it's a custom component
3. Call get_native_component_catalog() to see native options
4. For any native components you want to use, call get_native_component_example()

Only after calling all required tools, generate the final A2UI JSON response."""

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

            #region a2ui validation
            is_valid = False
            error_message = ""

            logger.info(f"--- UIAssemblyAgent: Validating UI response (Attempt {attempt})... ---")
            try:
                if "---a2ui_JSON---" not in final_response_content:
                    raise ValueError("Delimiter '---a2ui_JSON---' not found.")

                text_part, json_string = final_response_content.split("---a2ui_JSON---", 1)

                if not json_string.strip():
                    raise ValueError("JSON part is empty.")

                json_string_cleaned = ( json_string.strip().lstrip("```json").rstrip("```").strip() )

                if not json_string_cleaned:
                    raise ValueError("Cleaned JSON string is empty.")

                # Parse JSON
                parsed_json_data = json.loads(json_string_cleaned)

                # Validate against A2UI_SCHEMA
                logger.info("--- UIAssemblyAgent: Validating against A2UI_SCHEMA... ---")
                jsonschema.validate( instance=parsed_json_data, schema=self.a2ui_schema_object )

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
                    f"Please retry the original request: 'Orchestrator component selection: {orchestrator_data}\n\nData to visualize: {data_context}'"
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
    messages:DynamicGraphState = {'messages':[HumanMessage("AIMessage(content='[bar-graph]'")]}
    response = await orchestrator(messages)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())