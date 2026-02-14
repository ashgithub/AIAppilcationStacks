from langchain.agents import create_agent
from langgraph.graph.message import MessagesState

from dynamic_app.ui_agents_graph.widget_tools import get_widget_catalog
from dynamic_app.configs.gen_ai_provider import GenAIProvider

class UIOrchestrator:
    """ Orchestrator that receives the user query, the summary of data found and widget skills to select the suitable ones """

    AGENT_INSTRUCTIONS = """
    You are an orchestrator agent that is in charge of slecting the suitable skills to the agent
    Select the most suitable widgets skills to show the user a good visual response
    You have to analyze the query from the user, compare to the given data summary.
    Pick between 1-3 skills max to generate the queries and pass the list of the selected skills.
    As final output generate the list of widgets to use followed by the raw data to populate
    The next agent will receive the widget names and based on the data you share will render the visual details.
    """

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_id="openai.gpt-4.1",model_kwargs={"temperature":0.7})
        self.agent_name = "ui_orchestrator"
        self.system_prompt = self.AGENT_INSTRUCTIONS
        self.agent = self._build_agent()

    async def __call__(self, state: MessagesState):
        return await self.agent.ainvoke(state)
    
    def _build_agent(self):
        return create_agent(
            model=self._client,
            system_prompt=self.system_prompt,
            tools=[get_widget_catalog],
            # Fix structured output wrappers
            # response_format=UIOrchestratorOutput,
            name=self.agent_name
        )
    
async def main():
    from langchain.messages import HumanMessage
    orchestrator = UIOrchestrator()
    messages:MessagesState = {'messages':[HumanMessage("What is my bill?")]}
    response = await orchestrator(messages)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())