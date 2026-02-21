""" File to store the common pydantic classes or struct configs """
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass
from langgraph.graph import MessagesState

class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str  # Unique identifier for the skill
    description: str  # 1-2 sentence description to show in system prompt
    content: str  # Full skill content with detailed instructions

class UIOrchestratorOutput(BaseModel):
    """Output from UI Orchestrator containing selected widgets."""
    widgets: List[Skill] = Field(description="List of selected UI widgets (1-3 max)")

class DynamicGraphState(MessagesState):
    """ Class that holds the dynamic graph state """
    suggestions: str

# Data class for better json handling
@dataclass
class AgentConfig:
    """Configuration for an agent"""
    model: str
    temperature: float
    name: str
    system_prompt: Optional[str]
    tools_enabled: List[str]

# JSON Schema for validating AgentConfig
AGENT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "temperature": {"type": "number", "minimum": 0, "maximum": 2},
        "name": {"type": "string"},
        "system_prompt": {"type": ["string", "null"]},
        "tools_enabled": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["model", "temperature", "name", "tools_enabled"]
}

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "place_finder_agent": AGENT_CONFIG_SCHEMA,
        "data_finder_agent": AGENT_CONFIG_SCHEMA,
        "presenter_agent": AGENT_CONFIG_SCHEMA
    },
    "additionalProperties": False
}

# Default agent config
DEFAULT_CONFIG = {
        "place_finder_agent": AgentConfig(
            model="xai.grok-4-fast-non-reasoning",
            temperature=0.7,
            name="place_finder_agent",
            system_prompt="""You are and agent that is specialized on finding different restaurants/caffeterias depending on type of cuisine. 
            Return your answer in the best way possible so other LLM can read the information and proceed. 
            Only return a list of the names of restaurants/caffeterias found.""",
            tools_enabled=["get_restaurants", "get_caffeterias"]
        ),
        "data_finder_agent": AgentConfig(
            model="xai.grok-4-fast-non-reasoning",
            temperature=0.7,
            name="data_finder_agent",
            system_prompt="""You are an agent expert in finding restaurant data.
            You will receive the information about a list of restaurants or caffeterias to find information about.
            Your job is to gather that information and pass the full data to a new agent that will respond to the user.
            Important, consider including links, image references and other UI data to be rendered during next steps.
            Consider that caffeteria or restaurant data should be complete, use tools as required according to context.
            Make sure to use the exact restaurant names from information.""",
            tools_enabled=["get_restaurant_data", "get_cafe_data"]
        ),
        "presenter_agent": AgentConfig(
            model="xai.grok-4",
            temperature=0.7,
            name="presenter_agent",
            system_prompt=None,
            tools_enabled=[]
        )
    }

# Exception for the config graph
class AgentGraphException(Exception):
    """ Exception for missing graph configs """

    def __init__(self, message="Missing configuration dictionary for graph"):
        self.message = message
        super().__init__(self.message)