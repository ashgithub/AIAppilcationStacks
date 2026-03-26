# region Imports
from abc import ABC
from typing import Any

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from core.gen_ai_provider import GenAIProvider
# endregion Imports

# region Classes
class BaseAgent(ABC):
    """Base template for agent wrappers."""

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self.model = "xai.grok-4-fast-non-reasoning"
        self.agent_name = "backend_orchestrator"
        self.system_prompt = ''
        self.tools = []
        self.response_format: Any = None
        # Subclasses set this with build_agent().
        self.agent = None

    def build_agent(self, response_format: Any | None = None):
        
        self._client = self.gen_ai_provider.build_oci_client(
            model_id=self.model, model_kwargs={"temperature": 0.1}
        )

        create_agent_kwargs = {
            "model": self._client,
            "tools": self.tools,
            "system_prompt": self.system_prompt,
            "name": self.agent_name,
            "checkpointer": InMemorySaver(),
        }
        selected_response_format = (
            response_format if response_format is not None else self.response_format
        )
        if selected_response_format is not None:
            create_agent_kwargs["response_format"] = selected_response_format

        return create_agent(
            **create_agent_kwargs
        )
# endregion Classes
