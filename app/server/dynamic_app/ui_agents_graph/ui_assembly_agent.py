import json
import os
from langchain.agents import create_agent
from langgraph.graph.message import MessagesState

from dynamic_app.configs.gen_ai_provider import GenAIProvider
from dynamic_app.ui_agents_graph.widget_tools import get_widget_schema, get_native_component_example, get_native_component_catalog

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

    @classmethod
    def _get_agent_instructions(cls):
        """Get the agent instructions with loaded schema."""
        return f"""
You are an agent in charge of generating different UI widgets for A2UI surfaces.
You will receive the list of widgets to generate and the raw data information to work with.
Your goal is to process the raw data and bind it to the right widgets selected using the tools provided.

COMPONENT USAGE:
- Use native components (Text, Button, Image, Column, Row, etc.) for basic UI elements
- Use custom widgets from the catalog for complex UI patterns (charts, forms, etc.)
- Get component examples and schemas using the available tools when needed
- The component examples shows how the particular component schemas should be filled out
- Surfaces can contain multiple components - combine them as needed

DATA BINDING:
- Use dataModelUpdate to provide data that components can reference via paths
- Components can reference data using {{"path": "/data/key"}} or provide literal values
- Ensure data structure matches what components expect

Your final output MUST be an A2UI UI JSON response.

To generate the response, you MUST follow these rules:
1.  Your response MUST be in two parts, separated by the delimiter: `---a2ui_JSON---`.
2.  The first part is your conversational text response.
3.  The second part is a single, raw JSON object which is a list of A2UI messages.
4.  The JSON part MUST conform to the A2UI message structure shown below.

--- CONDENSED A2UI SCHEMA ---
{cls._load_condensed_schema()}
--- END SCHEMA ---
"""

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature":0.7})
        self.agent_name = "assembly_agent"
        self.system_prompt = self._get_agent_instructions()
        self.agent = self._build_agent()

    async def __call__(self, state:MessagesState):
        return await self.agent.ainvoke(state)
    
    def _build_agent(self):
        return create_agent(
            model=self._client,
            tools=[get_widget_schema, get_native_component_example, get_native_component_catalog],
            system_prompt=self.system_prompt,
            name=self.agent_name
        )
    
async def main():
    from langchain.messages import HumanMessage
    orchestrator = UIAssemblyAgent()
    messages:MessagesState = {'messages':[HumanMessage("AIMessage(content='[bar-graph]'")]}
    response = await orchestrator(messages)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())