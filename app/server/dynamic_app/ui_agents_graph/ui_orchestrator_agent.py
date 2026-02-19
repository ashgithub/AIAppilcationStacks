from langchain.agents import create_agent
from langgraph.graph.message import MessagesState
from langchain.messages import AIMessage

from dynamic_app.ui_agents_graph.widget_tools import get_widget_catalog, get_native_component_catalog
from dynamic_app.configs.gen_ai_provider import GenAIProvider
from dynamic_app.configs.common_struct import UIOrchestratorOutput

class UIOrchestrator:
    """ Orchestrator that receives the user query, the summary of data found and widget skills to select the suitable ones """

    AGENT_INSTRUCTIONS = """
    You are an orchestrator agent that selects suitable UI components for data visualization.

    TASK:
    - Analyze the user query and available data
    - Select 1-3 most appropriate UI components from the available catalogs
    - ALWAYS use 'get_widget_catalog' for custom visualization components (charts, tables, etc.)
    - Optionally use 'get_native_component_catalog' for basic UI components (Text, Button, etc.) if needed for layout
    - Return ONLY a simple list of component names in this format:

    COMPONENTS: component1, component2, component3

    EXAMPLE OUTPUT (confirm components available with the tools):
    COMPONENTS: bar-graph, table, text

    Do not include any other text or explanation. Just the component list.
    Focus on selecting the main visualization components, native components are supplementary.
    """

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_id="openai.gpt-4.1",model_kwargs={"temperature":0.7})
        self._output_client = self.gen_ai_provider.build_oci_client(model_id="openai.gpt-4.1",model_kwargs={"temperature":0.7})
        self.agent_name = "ui_orchestrator"
        self.agent = self._build_agent()
        self.output_response = self._build_output_llm()

    async def __call__(self, state: MessagesState):
        response =  await self.agent.ainvoke(state)
        # To support structured output, seems langchain_oci has erro here
        structured_response = await self.output_response.ainvoke(f"Build the component list with the information on: {response['messages'][-1].content}")
        return {
            'messages': state['messages'] + [
                AIMessage(content=(
                    str(structured_response.model_dump_json())
                ))
            ]
        }
    
    def _build_agent(self):
        return create_agent(
            model=self._client,
            system_prompt=self.AGENT_INSTRUCTIONS,
            tools=[get_widget_catalog, get_native_component_catalog],
            name=self.agent_name
        )
    
    def _build_output_llm(self):
        return self._output_client.with_structured_output(UIOrchestratorOutput)
    
async def main():
    from langchain.messages import HumanMessage
    orchestrator = UIOrchestrator()
    messages:MessagesState = {'messages':[HumanMessage("What is my bill?")]}
    response = await orchestrator(messages)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())