"""Parallel UI layout planner node."""

from __future__ import annotations

import logging

from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.parallel_ui_shared import (
    build_widget_execution_tasks,
    extract_structured_result,
    is_no_data_or_out_of_domain,
    needs_timeline,
    normalize_widget_name,
)
from core.dynamic_app.prompts import UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS
from core.dynamic_app.schemas.structured_outputs import ParallelWidgetPlan, SuggestedWidgetTask
from dynamic_app.ui_agents_graph.widget_tools import (
    get_native_component_catalog,
    get_widget_catalog,
)

MAX_PARALLEL_WIDGETS = 4
logger = logging.getLogger(__name__)


class UIParallelOrchestratorAgent(BaseAgent):
    """Select widgets as a compact, structured plan."""

    def __init__(self):
        super().__init__()
        self.model = "xai.grok-4-fast-non-reasoning"
        self.agent_name = "ui_parallel_orchestrator"
        self.system_prompt = UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS
        self.tools = [get_widget_catalog, get_native_component_catalog]
        self.response_format = ParallelWidgetPlan
        self.agent = self.build_agent()

    async def generate_plan(self, state: DynamicGraphState) -> ParallelWidgetPlan:
        data_context = str(state["messages"][-1].content if state["messages"] else "")
        logger.info(
            "Planner start | data_context_len=%s no_data_or_oos=%s",
            len(data_context),
            is_no_data_or_out_of_domain(data_context),
        )
        if is_no_data_or_out_of_domain(data_context):
            logger.info("Planner using guidance-mode static plan.")
            return ParallelWidgetPlan(
                summary="Guidance mode with native components.",
                widget_tasks=[
                    SuggestedWidgetTask(widget_name="Text", slot_label="Guidance", priority=1),
                    SuggestedWidgetTask(widget_name="Card", slot_label="Suggestions", priority=2),
                ],
            )

        raw = await self.agent.ainvoke(state)
        extracted = extract_structured_result(raw, ParallelWidgetPlan)
        if extracted is None:
            logger.warning("Planner structured extraction failed. Using fallback plan.")
            return ParallelWidgetPlan(
                summary="Generated fallback widget plan.",
                widget_tasks=[
                    SuggestedWidgetTask(
                        widget_name="KpiCard",
                        slot_label="Highlights",
                        priority=1,
                    ),
                    SuggestedWidgetTask(
                        widget_name="Table",
                        slot_label="Details",
                        priority=2,
                    ),
                ],
            )

        if extracted.widget_tasks:
            normalized: list[SuggestedWidgetTask] = []
            seen: set[str] = set()
            for task in sorted(extracted.widget_tasks, key=lambda item: item.priority):
                canonical = normalize_widget_name(task.widget_name)
                key = canonical.lower()
                if key in seen:
                    continue
                seen.add(key)
                normalized.append(
                    SuggestedWidgetTask(
                        widget_name=canonical,
                        slot_label=task.slot_label or canonical,
                        priority=task.priority,
                    )
                )
                if len(normalized) >= MAX_PARALLEL_WIDGETS:
                    break

            if needs_timeline(data_context) and "timelinecomponent" not in {
                task.widget_name.lower() for task in normalized
            }:
                if len(normalized) >= MAX_PARALLEL_WIDGETS:
                    normalized[-1] = SuggestedWidgetTask(
                        widget_name="TimelineComponent",
                        slot_label="Timeline",
                        priority=MAX_PARALLEL_WIDGETS,
                    )
                else:
                    normalized.append(
                        SuggestedWidgetTask(
                            widget_name="TimelineComponent",
                            slot_label="Timeline",
                            priority=len(normalized) + 1,
                        )
                    )
            if normalized:
                logger.info(
                    "Planner success | summary_len=%s widget_count=%s widgets=%s",
                    len(extracted.summary or ""),
                    len(normalized),
                    [task.widget_name for task in normalized],
                )
                return ParallelWidgetPlan(summary=extracted.summary, widget_tasks=normalized)

        logger.warning("Planner produced empty widget_tasks after normalization. Using fallback.")
        return ParallelWidgetPlan(
            summary="Generated fallback widget plan.",
            widget_tasks=[
                SuggestedWidgetTask(widget_name="KpiCard", slot_label="Highlights", priority=1),
                SuggestedWidgetTask(widget_name="Table", slot_label="Details", priority=2),
            ],
        )


class UIParallelLayoutPlannerNode:
    """Graph node that generates the layout plan and execution task metadata."""

    def __init__(self):
        self.agent_name = "ui_parallel_layout_planner"
        self._planner = UIParallelOrchestratorAgent()

    async def __call__(self, state: DynamicGraphState) -> DynamicGraphState:
        data_context = str(state["messages"][-1].content if state["messages"] else "")
        plan = await self._planner.generate_plan(state)
        tasks = build_widget_execution_tasks(plan)
        logger.info(
            "Planner node output | tasks=%s widgets=%s",
            len(tasks),
            [task["widget_name"] for task in tasks],
        )
        return {
            "parallel_data_context": data_context,
            "parallel_widget_plan": plan.model_dump(),
            "parallel_execution_tasks": tasks,
        }
