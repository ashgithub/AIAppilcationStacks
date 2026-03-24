# region Imports
from abc import ABC
from langchain.agents import create_agent

from core.gen_ai_provider import GenAIProvider
# endregion Imports

# region Classes
class BaseAgent(ABC):
    """Base template for agent wrappers."""

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self.model = "xai.grok-4-fast-non-reasoning"
        self.model_kwargs = {"temperature": 0.1}
        self.agent_name = "backend_orchestrator"
        self.system_prompt = ''
        self.tools = []
        self.response_format=None
        self.checkpointer = None
        # Subclasses set this with build_agent().
        self.agent = None

    def build_agent(self):
        """Build the agent"""
        self._client = self.gen_ai_provider.build_oci_client(self.model, self.model_kwargs)

        return create_agent(
            model=self._client,
            tools=self.tools,
            system_prompt=self.system_prompt,
            name=self.agent_name,
            checkpointer=self.checkpointer,
            response_format=self.response_format
        )
# endregion Classes
