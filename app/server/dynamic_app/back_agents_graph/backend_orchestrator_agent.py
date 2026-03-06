from langchain.agents import create_agent

from dynamic_app.back_agents_graph.rag_agent import semantic_search
from dynamic_app.back_agents_graph.nl2graph_agent import call_graphDB
from core.gen_ai_provider import GenAIProvider
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.prompts import BACKEND_ORCHESTRATOR_INSTRUCTIONS


class BackendOrchestratorAgent:
    """Supervisor agent that coordinates data collection from worker agents and provides consolidated data to UI agents."""

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_kwargs={"temperature": 0.1})
        self.agent_name = "backend_orchestrator"
        self.system_prompt = BACKEND_ORCHESTRATOR_INSTRUCTIONS
        self.agent = self._build_agent()

    async def __call__(self, state: DynamicGraphState):
        """Orchestrate data collection and return consolidated results."""
        return await self.agent.ainvoke(state)

    def _build_agent(self):
        """Build the agent with worker tools."""
        tools = [call_graphDB, semantic_search]

        return create_agent(
            model=self._client,
            tools=tools,
            system_prompt=self.system_prompt,
            name=self.agent_name
        )
