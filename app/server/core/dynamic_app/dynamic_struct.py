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
        "data_orchestrator_agent": AGENT_CONFIG_SCHEMA,
        "data_analyzer_agent": AGENT_CONFIG_SCHEMA,
        "ui_presenter_agent": AGENT_CONFIG_SCHEMA
    },
    "additionalProperties": False
}

# Default agent config
DEFAULT_CONFIG = {
        "data_orchestrator_agent": AgentConfig(
            model="xai.grok-4-fast-non-reasoning",
            temperature=0.7,
            name="data_orchestrator_agent",
            system_prompt="""You are an agent specialized in orchestrating data retrieval for energy and outage information.
            Based on user queries about power outages, energy statistics, and industry performance, determine what data is needed.
            Return your answer in the best way possible so other LLMs can read the information and proceed.
            Only return the types of data needed: outage_data, energy_data, or industry_data.""",
            tools_enabled=["get_outage_data", "get_energy_data", "get_industry_data"]
        ),
        "data_analyzer_agent": AgentConfig(
            model="xai.grok-4-fast-non-reasoning",
            temperature=0.7,
            name="data_analyzer_agent",
            system_prompt="""You are an agent expert in analyzing energy and outage data.
            You will receive information about power outages, energy statistics, and industry performance data.
            Your job is to analyze this data and provide insights, trends, and relevant information to help users understand the energy landscape.
            Important, consider including relevant metrics, trends, and UI data to be rendered during next steps.
            Ensure data analysis is accurate and comprehensive, using tools as required according to context.""",
            tools_enabled=["get_outage_data", "get_energy_data", "get_industry_data"]
        ),
        "ui_presenter_agent": AgentConfig(
            model="xai.grok-4",
            temperature=0.7,
            name="ui_presenter_agent",
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