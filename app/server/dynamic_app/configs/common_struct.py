""" File to store the common pydantic classes or struct configs """
from typing import TypedDict, List, Any
from pydantic import BaseModel, Field

class Skill(TypedDict):  
    """A skill that can be progressively disclosed to the agent."""
    name: str  # Unique identifier for the skill
    description: str  # 1-2 sentence description to show in system prompt
    content: str  # Full skill content with detailed instructions