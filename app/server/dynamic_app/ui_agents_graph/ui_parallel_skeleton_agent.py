"""Parallel UI shell/skeleton generation node."""

from __future__ import annotations

import logging

from langchain.messages import HumanMessage

from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.parallel_ui_shared import (
    extract_structured_result,
    is_no_data_or_out_of_domain,
)
from core.dynamic_app.prompts import UI_PARALLEL_SHELL_INSTRUCTIONS
from core.dynamic_app.schemas.structured_outputs import A2UIShellOutput, ParallelWidgetPlan
from dynamic_app.ui_agents_graph.ui_parallel_fragment_merge_agent import (
    UIParallelFragmentMergeAgent,
)

logger = logging.getLogger(__name__)


class UIShellStructuredAgent(BaseAgent):
    """Generate shell metadata from plan and data context."""

    def __init__(self):
        super().__init__()
        self.model = "xai.grok-4-fast-reasoning"
        self.agent_name = "ui_parallel_shell"
        self.system_prompt = UI_PARALLEL_SHELL_INSTRUCTIONS
        self.response_format = A2UIShellOutput
        self.agent = self.build_agent()

    async def generate_shell(
        self, plan: ParallelWidgetPlan, data_context: str
    ) -> A2UIShellOutput:
        task_labels = [task.slot_label or task.widget_name for task in plan.widget_tasks]
        mode = "guidance" if is_no_data_or_out_of_domain(data_context) else "data_visualization"
        prompt = (
            f"Mode: {mode}\n"
            "Native components available for shell: Text, Column, Row, Card, Button, Image, Icon.\n"
            f"Planner summary: {plan.summary}\n"
            f"Widget sections: {', '.join(task_labels)}\n"
            f"Data context:\n{data_context}"
        )
        response = await self.agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        structured = extract_structured_result(response, A2UIShellOutput)
        if structured is None:
            logger.warning("Shell structured extraction failed. Using default shell output.")
            return A2UIShellOutput()
        logger.info(
            "Shell success | root_id=%s title=%s section_titles=%s use_card_sections=%s layout=%s",
            structured.root_id,
            structured.surface_title,
            len(structured.section_titles),
            structured.use_card_sections,
            structured.layout_component,
        )
        return structured


class UIParallelSkeletonNode:
    """Graph node that creates the shell/skeleton response."""

    def __init__(self):
        self.agent_name = "ui_parallel_skeleton"
        self._shell = UIShellStructuredAgent()
        self._fragment_builder = UIParallelFragmentMergeAgent()

    async def __call__(self, state: DynamicGraphState) -> DynamicGraphState:
        plan_data = state.get("parallel_widget_plan") or {}
        plan = ParallelWidgetPlan.model_validate(plan_data)
        data_context = str(
            state.get("parallel_data_context")
            or (state["messages"][-1].content if state.get("messages") else "")
        )
        shell_output = await self._shell.generate_shell(plan, data_context)
        if is_no_data_or_out_of_domain(data_context):
            shell_output.use_card_sections = True
            if not shell_output.intro_text:
                shell_output.intro_text = (
                    "I can help you explore outage, energy, infrastructure, and disaster response data."
                )
            logger.info("Skeleton node forced guidance shell settings for no-data/out-of-scope.")
        tasks = list(state.get("parallel_execution_tasks") or [])
        if len(shell_output.section_titles) > len(tasks):
            shell_output.section_titles = shell_output.section_titles[: len(tasks)]
            logger.info(
                "Skeleton section_titles trimmed to task count | section_titles=%s tasks=%s",
                len(shell_output.section_titles),
                len(tasks),
            )
        shell_components, assistant_text = self._fragment_builder._build_shell_components(
            shell_output, tasks
        )
        surface_id = shell_output.surface_id or "dashboard"
        root_id = shell_output.root_id or "root-layout"

        fragment = {
            "surface_id": surface_id,
            "root_id": root_id,
            "assistant_text": assistant_text or "",
            "ordered_component_ids": [component["id"] for component in shell_components],
            "components": shell_components,
            "begin_rendering": {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": root_id,
                    "styles": {
                        "font": shell_output.style_font or "Arial",
                        "primaryColor": shell_output.style_primary_color or "#007bff",
                    },
                }
            },
            "initial_surface_update": {
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": shell_components,
                }
            },
        }

        return {
            "parallel_shell_output": shell_output.model_dump(),
            "parallel_skeleton_fragment": fragment,
        }
