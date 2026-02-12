""" For providing the skills and schemas of the widgets """
import os
import yaml
from langchain.tools import tool
from langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware
from langchain.messages import SystemMessage
from typing import Callable

SKILLS_PATH = "dynamic_app/configs/schemas/widget_skills"

def readFile(skillPath):
    with open(skillPath, 'r', encoding='utf-8') as f:
        return f.read()

def extractYAMLFrontmatter(content):
    # Split by ---
    parts = content.split('---')
    if len(parts) >= 3:
        frontmatter_str = parts[1].strip()
        try:
            return yaml.safe_load(frontmatter_str)
        except yaml.YAMLError:
            return {}
    return {}

def parseMetadata(skillPath):
    content = readFile(skillPath)
    frontmatter = extractYAMLFrontmatter(content)

    return {
        "name": frontmatter.get("name", ""),
        "description": frontmatter.get("description", ""),
        "content": frontmatter.get("content", ""),
        "path": skillPath
    }

def loadSkills():
    skills = []
    if os.path.exists(SKILLS_PATH):
        for file in os.listdir(SKILLS_PATH):
            if file.endswith('.md'):
                skillPath = os.path.join(SKILLS_PATH, file)
                skill = parseMetadata(skillPath)
                if skill["name"]:  # Only add if name is present
                    skills.append(skill)
    return skills

SKILLS = loadSkills()

@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "expense_reporting", "travel_booking")
    """
    # Find and return the requested skill
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS)
    return f"Skill '{skill_name}' not found. Available skills: {available}"

class SkillSelectionMiddleware(AgentMiddleware):
    """Middleware that injects skill descriptions into the system prompt for selection."""

    def __init__(self):
        """Initialize and generate the skills prompt from SKILLS."""
        # Build skills prompt from the SKILLS list
        skills_list = []
        for skill in SKILLS:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        self.skills_prompt = "\n".join(skills_list)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Sync: Inject skill descriptions into system prompt."""
        # Build the skills addendum
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self.skills_prompt}\n\n"
            "Select the most suitable skills for the task."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Async: Inject skill descriptions into system prompt."""
        # Build the skills addendum
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self.skills_prompt}\n\n"
            "Select the most suitable skills for the task."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return await handler(modified_request)

class SkillExecutionMiddleware(AgentMiddleware):
    """Middleware that provides skill execution tools."""

    # Register the load_skill tool as a class variable
    tools = [load_skill]

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Sync: Provide execution context."""
        # Add minimal context about skill execution
        execution_addendum = (
            "\n\nYou can load skill content by name using the available tool load_skill."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": execution_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Async: Provide execution context."""
        # Add minimal context about skill execution
        execution_addendum = (
            "\n\nYou can load skill content by name using the available tool load_skill."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": execution_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return await handler(modified_request)
