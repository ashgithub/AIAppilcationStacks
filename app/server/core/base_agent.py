from abc import ABC
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from core.gen_ai_provider import GenAIProvider

class BaseAgent(ABC):
    """template for agents, may require rebuild"""

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_id="xai.grok-4-fast-reasoning", model_kwargs={"temperature": 0.1})
        self.agent_name = "backend_orchestrator"
        self.system_prompt = ''
        self.tools = []
        # each subclass must build the agent to overwrite
        self.agent = None

    def build_agent(self):
        """Build the agent"""
        return create_agent(
            model=self._client,
            tools=self.tools,
            system_prompt=self.system_prompt,
            name=self.agent_name,
            checkpointer=InMemorySaver()
        )