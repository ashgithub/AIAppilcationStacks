import json
import logging
import jsonschema
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from typing import List, Optional, Dict, Any, Tuple

from dynamic_app.ui_agents_graph.widget_tools import get_native_component_example, create_custom_component_tools
from core.gen_ai_provider import GenAIProvider
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.prompts import get_ui_assembly_instructions
from core.dynamic_app.schema_utils import (
    load_a2ui_schema,
    inject_custom_schemas_into_schema,
    create_array_schema_validator,
    extract_allowed_components
)

logger = logging.getLogger(__name__)

class UIAssemblyAgent:
    """Agent in charge of generating the ordered UI schemas from ui orchestrator."""

    def __init__(self, base_url: str = None, inline_catalog: List[Dict[str, Any]] = None):
        self.base_url = base_url or "http://localhost:8000"
        self.inline_catalog = inline_catalog or []

        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature": 0.7})
        self.agent_name = "assembly_agent"

        # Initialize per-call attributes
        self.allowed_components: Optional[List[str]] = None
        self.system_prompt: Optional[str] = None
        self.agent = None
        self.a2ui_schema_object: Optional[Dict[str, Any]] = None

    def _build_agent(self) -> Any:
        return create_agent(
            model=self._client,
            tools=[self.get_custom_component_example_tool, get_native_component_example],
            system_prompt=self.system_prompt,
            name=self.agent_name
        )

    def _setup_schema_and_tools(self, orchestrator_data: str, data_context: str) -> List[str]:
        """Setup schema, tools, and prompt for the current request."""
        allowed_components = extract_allowed_components(orchestrator_data)

        base_schema = load_a2ui_schema()
        self.A2UI_SCHEMA = inject_custom_schemas_into_schema(
            base_schema, self.inline_catalog, allowed_components
        )

        # Load schema for validation
        self.a2ui_schema_object = create_array_schema_validator(self.A2UI_SCHEMA)

        self.allowed_components = allowed_components
        self.system_prompt = get_ui_assembly_instructions(allowed_components, data_context)

        self.get_custom_component_catalog_tool, self.get_custom_component_example_tool = create_custom_component_tools(
            self.inline_catalog, allowed_components
        )

        self.agent = self._build_agent()
        return allowed_components

    def _validate_ui_response(self, response_content: str) -> Tuple[bool, str, str]:
        """Validate UI response against A2UI schema. Returns (is_valid, error_message, final_content)."""
        try:
            if "---a2ui_JSON---" not in response_content:
                raise ValueError("Delimiter '---a2ui_JSON---' not found.")

            text_part, json_string = response_content.split("---a2ui_JSON---", 1)

            if not json_string.strip():
                raise ValueError("JSON part is empty.")

            json_string_cleaned = json_string.strip().lstrip("```json").rstrip("```").strip()

            if not json_string_cleaned:
                raise ValueError("Cleaned JSON string is empty.")

            parsed_json_data = json.loads(json_string_cleaned)
            jsonschema.validate(instance=parsed_json_data, schema=self.a2ui_schema_object)

            final_content = f"{text_part}\n---a2ui_JSON---\n{json_string}"
            return True, "", final_content

        except (ValueError, json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
            return False, f"Validation failed: {e}", ""

    def _generate_query_text(self, orchestrator_data: str, data_context: str, is_retry: bool = False, error_message: str = "") -> str:
        """Generate the query text for the agent, including retry instructions if needed."""
        allowed_str = ", ".join(self.allowed_components) if self.allowed_components else "any available"

        base_instructions = f"""Orchestrator component selection: {orchestrator_data}

Data to visualize: {data_context}

INSTRUCTIONS: You must FIRST call the required tools to get component examples, THEN generate the A2UI JSON. Do not attempt to generate JSON without calling the tools first.

REQUIRED TOOL CALLS:
1. Call get_custom_component_catalog() immediately
2. For each component in [{allowed_str}], call get_custom_component_example() if it's a custom component
3. Call get_native_component_catalog() to see native options
4. For any native components you want to use, call get_native_component_example()

Only after calling all required tools, generate the final A2UI JSON response."""

        if is_retry:
            return (
                f"Your previous response was invalid. {error_message} "
                "You MUST generate a valid response that strictly follows the A2UI JSON SCHEMA. "
                "The response MUST be a JSON list of A2UI messages. "
                "Ensure the response is split by '---a2ui_JSON---' and the JSON part is well-formed. "
                f"Please retry the original request: 'Orchestrator component selection: {orchestrator_data}\n\nData to visualize: {data_context}'"
            )

        return base_instructions

    async def _generate_with_retry(self, orchestrator_data: str, data_context: str, max_retries: int = 1) -> Dict[str, Any]:
        """Generate UI with retry logic on validation failure."""
        for attempt in range(max_retries + 1):
            logger.info(f"UI Assembly validation attempt {attempt + 1}/{max_retries + 1}")

            query_text = self._generate_query_text(orchestrator_data, data_context, attempt > 0)
            messages = {'messages': [HumanMessage(content=query_text)]}
            response = await self.agent.ainvoke(messages)
            response_content = response['messages'][-1].content

            is_valid, error_message, final_content = self._validate_ui_response(response_content)

            if is_valid:
                validated_response = response.copy()
                validated_response['messages'][-1] = AIMessage(content=final_content)
                return validated_response

            if attempt < max_retries:
                query_text = self._generate_query_text(orchestrator_data, data_context, True, error_message)

        # Max retries exhausted
        return {
            'messages': [
                AIMessage(content="I'm sorry, I'm having trouble generating the interface for that request right now. Please try again in a moment.")
            ]
        }

    async def __call__(self, state: DynamicGraphState) -> Dict[str, Any]:
        """Call the UI assembly agent to generate and validate UI from orchestrator data."""
        orchestrator_data = state['messages'][-1].content
        data_context = state['messages'][-2].content

        allowed_components = self._setup_schema_and_tools(orchestrator_data, data_context)

        if self.a2ui_schema_object is None:
            logger.error("--- UIAssemblyAgent: A2UI_SCHEMA is not loaded. Cannot perform UI validation. ---")
            return {
                'messages': state['messages'] + [
                    AIMessage(content="I'm sorry, I'm facing an internal configuration error with my UI components.")
                ]
            }

        result = await self._generate_with_retry(orchestrator_data, data_context)
        result['messages'] = state['messages'] + result['messages']
        return result
    
async def main():
    from langchain.messages import HumanMessage, AIMessage
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
    # Create proper test state with orchestrator output and data context
    state: DynamicGraphState = {
        'messages': [
            AIMessage(content='Sample data context for visualization'),
            AIMessage(content='{"widgets": [{"name": "bar-graph"}]}')  # Orchestrator output
        ]
    }
    response = await orchestrator(state)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())