from langchain.agents import create_agent
from langchain.messages import AIMessage
from langgraph.graph.message import MessagesState

from dynamic_app.configs.gen_ai_provider import GenAIProvider
from dynamic_app.back_agents_graph.outage_agent import get_outage_data
from dynamic_app.back_agents_graph.energy_agent import get_energy_data
from dynamic_app.back_agents_graph.industry_agent import get_industry_data


class BackendOrchestratorAgent:
    """Supervisor agent that coordinates data collection from worker agents and provides consolidated data to UI agents."""

    AGENT_INSTRUCTIONS = """
    You are a backend orchestrator agent responsible for coordinating data collection from various worker agents.
    Your role is to:

    1. Use the available worker tools to gather data on outages, energy, and industries
    2. Consolidate all the collected data into a comprehensive text summary
    3. Provide this consolidated information to the UI agents for visualization

    Always call all available data collection tools (outages, energy, industry) to ensure complete data coverage.
    Present the aggregated data in a clear, readable format that UI agents can easily parse and use for creating visualizations.

    Return the data in this format:
    ---
    OUTAGE DATA:
    [outage information]

    ENERGY DATA:
    [energy consumption and production information]

    INDUSTRY DATA:
    [industry performance information]
    ---
    """

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature": 0.1})
        self.agent_name = "backend_orchestrator"
        self.system_prompt = self.AGENT_INSTRUCTIONS
        self.agent = self._build_agent()

    async def __call__(self, state: MessagesState):
        """Orchestrate data collection and return consolidated results."""
        return await self.agent.ainvoke(state)

    def _build_agent(self):
        """Build the agent with worker tools."""
        tools = [get_outage_data, get_energy_data, get_industry_data]

        return create_agent(
            model=self._client,
            tools=tools,
            system_prompt=self.system_prompt,
            name=self.agent_name
        )
