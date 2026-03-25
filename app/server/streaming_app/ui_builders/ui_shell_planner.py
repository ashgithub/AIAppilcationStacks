"""Experimental shell planner with strict structured output binding."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from langgraph.checkpoint.memory import InMemorySaver

from core.base_agent import BaseAgent
from dynamic_app.ui_agents_graph.widget_tools import (
    get_native_component_catalog,
    get_native_component_example,
    get_widget_catalog,
)
from streaming_app.ui_builders.shell_output_schema import ShellMessage, validate_shell_messages, BeginRenderingPayload, SurfaceUpdatePayload


UI_SHELL_ONLY_PLANNER_INSTRUCTIONS = """
You are a shell-only A2UI planner used for testing.

GOAL:
- Return only surface shell messages used to initialize and layout the UI.
- Do not plan worker packages, data keys, or ownership metadata.

OUTPUT RULES:
- Return ONLY valid JSON (no markdown).
- Return exactly this structure:
{
  "shell_messages": [
    {"beginRendering": {"surfaceId": "dashboard", "root": "main-container"}},
    {"surfaceUpdate": {"surfaceId": "dashboard", "components": [...]}}
  ]
}

- Include at least:
1) one beginRendering
2) one surfaceUpdate
- Keep shell minimal and structural (Row/Column/Text/Card/placeholders).
- Do not include dataModelUpdate or deleteSurface.
"""


class ParallelShellPlan(BaseModel):
    """Minimal shell-only structured output for testing."""

    shell_messages: list[dict[str, Any]] = Field(
        description="A2UI shell messages (beginRendering + surfaceUpdate)"
    )

    @model_validator(mode="after")
    def validate_shell_contract(self) -> "ParallelShellPlan":
        validated = [ShellMessage.model_validate(message) for message in self.shell_messages]
        begin_messages = [
            message.beginRendering for message in validated if message.beginRendering is not None
        ]
        if not begin_messages:
            raise ValueError("shell_messages must include beginRendering")

        # Canonical surface/root are inferred from beginRendering so this schema
        # remains shell-only and does not require external worker metadata fields.
        surface_id = begin_messages[0].surfaceId
        root_component_id = begin_messages[0].root

        self.shell_messages = validate_shell_messages(
            shell_messages=[message.model_dump(mode="python") for message in validated],
            surface_id=surface_id,
            root_component_id=root_component_id,
        )
        return self


class UIShellPlanner(BaseAgent):
    """Testing-only planner that enforces strict shell validation via response_format."""

    def __init__(self):
        super().__init__()
        self.model = "xai.grok-4-fast-reasoning"
        self.model_kwargs = {"temperature": 0.1}
        self.agent_name = "ui_shell_planner"
        self.system_prompt = UI_SHELL_ONLY_PLANNER_INSTRUCTIONS
        self.tools = [
            get_widget_catalog,
            get_native_component_catalog,
            get_native_component_example,
        ]
        self.response_format = ParallelShellPlan
        self.checkpointer=InMemorySaver()
        self.agent = self.build_agent()

    async def __call__(self, state):
        for chunk in self.agent.stream(input=state["input"], config=state["config"]):
            print(chunk)

class BeginRenderingAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.model = "xai.grok-4-fast-reasoning"
        self.model_kwargs = {"temperature": 0.1}
        self.agent_name = "begin_rendering_agent"
        self.system_prompt = UI_SHELL_ONLY_PLANNER_INSTRUCTIONS
        self.tools = [
            get_widget_catalog,
            get_native_component_catalog,
            get_native_component_example,
        ]
        self.response_format = BeginRenderingPayload
        self.agent = self.build_agent()

    async def __call__(self, state):
        for chunk in self.agent.stream(input=state["input"], config=state["config"]):
            print(chunk)

class SurfaceUpdteAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.model = "xai.grok-4-fast-reasoning"
        self.model_kwargs = {"temperature": 0.1}
        self.agent_name = "surface_update_agent"
        self.system_prompt = UI_SHELL_ONLY_PLANNER_INSTRUCTIONS
        self.tools = [
            get_widget_catalog,
            get_native_component_catalog,
            get_native_component_example,
        ]
        self.response_format = SurfaceUpdatePayload
        self.agent = self.build_agent()

    async def __call__(self, state):
        for chunk in self.agent.stream(input=state["input"], config=state["config"]):
            print(chunk)

async def main():
    from langchain.messages import HumanMessage

    planner = UIShellPlanner()
    payload = {
        "input": {
            "messages": [
                HumanMessage(
                    "Show top outage causes with KPI summary and a chart for trend."
                )
            ]
        },
        "config": {"configurable": {"thread_id": "test_ui_shell_planner"}},
    }
    
    try: 
        await planner(payload)
    except Exception as e:
        payload = {
            "input": {
                "messages": [
                    HumanMessage(
                        f"Show top outage causes with KPI summary and a chart for trend. Try generating again payload, last time there was an error here: {e}"
                    )
                ]
            },
            "config": {"configurable": {"thread_id": "test_ui_shell_planner"}},
        }
        await planner(payload)



if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
