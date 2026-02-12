from langchain.agents import create_agent
from langgraph.graph.message import MessagesState

from dynamic_app.configs.gen_ai_provider import GenAIProvider
from dynamic_app.ui_agents_graph.widget_tool import build_widget_schema
from dynamic_app.configs.widget_skills_provider import SkillExecutionMiddleware

class UIAssemblyAgent:
    """ Agent in charge of generating the ordered UI schemas from ui orchestrator """

    AGENT_INSTRUCTIONS = """
    You are an agent in charge of generating different ui widgets.
    You will receive the list of widgets to generate and the raw data information to work with.
    Your goal is to process the raw data and bind it to the right widgets selected using the tool provided.
    Be sure to add all the necesary details and instructions to the tool.
    Select the suitable widget for each section of the information based on the given instructions.
    """

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature":0.7})
        self.agent_name = "assembly_agent"
        self.system_prompt = self.AGENT_INSTRUCTIONS
        self.agent = self._build_agent()

    async def __call__(self, state:MessagesState):
        return await self.agent.ainvoke(state)
    
    def _build_agent(self):
        return create_agent(
            model=self._client,
            tools=[build_widget_schema],
            middleware=[SkillExecutionMiddleware()],
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