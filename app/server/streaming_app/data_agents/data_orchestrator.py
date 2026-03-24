import logging

from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import InMemorySaver

from streaming_app.data_agents.nl2graph_agent import call_graphDB
from streaming_app.data_agents.rag_agent import semantic_search
from core.dynamic_app.prompts import BACKEND_ORCHESTRATOR_INSTRUCTIONS
from core.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DataOrchestrator(BaseAgent):
    """Supervisor agent that coordinates data collection from worker agents and provides consolidated data to UI agents."""

    def __init__(self):
        super().__init__()
        self.agent_name = "data_orchestrator"
        self.system_prompt = BACKEND_ORCHESTRATOR_INSTRUCTIONS
        self.tools = [call_graphDB, semantic_search]
        self.checkpointer=InMemorySaver()
        self.agent = self.build_agent()

    async def __call__(self, state: MessagesState):
        """Orchestrate data collection and return consolidated results."""
        return await self.agent.ainvoke(state)