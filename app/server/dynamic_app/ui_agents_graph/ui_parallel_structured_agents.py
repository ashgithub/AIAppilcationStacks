"""Compatibility wrapper for modular parallel structured UI nodes."""

from __future__ import annotations

from core.dynamic_app.dynamic_struct import DynamicGraphState
from dynamic_app.ui_agents_graph.ui_layout_planner import (
    UIParallelLayoutPlannerNode,
    UIParallelOrchestratorAgent,
)
from dynamic_app.ui_agents_graph.ui_parallel_fragment_merge_agent import (
    UIParallelFragmentMergeAgent,
)
from dynamic_app.ui_agents_graph.ui_parallel_skeleton_agent import (
    UIParallelSkeletonNode,
    UIShellStructuredAgent,
)
from dynamic_app.ui_agents_graph.ui_parallel_widget_worker_agent import (
    UIParallelWidgetWorkerNode,
    UIWidgetStructuredAgent,
)


class ParallelUIStructuredAssembler:
    """
    Backward-compatible sequential wrapper.

    Preferred runtime path is the multinode graph:
    planner -> (skeleton + widget_worker) -> fragment_merge.
    """

    def __init__(self):
        self.agent_name = "parallel_structured_ui_assembly"
        self._planner_node = UIParallelLayoutPlannerNode()
        self._skeleton_node = UIParallelSkeletonNode()
        self._widget_node = UIParallelWidgetWorkerNode()
        self._merge_node = UIParallelFragmentMergeAgent()

    async def __call__(self, state: DynamicGraphState) -> DynamicGraphState:
        planner_state = await self._planner_node(state)
        working_state = dict(state)
        working_state.update(planner_state)

        shell_state = await self._skeleton_node(working_state)
        widget_state = await self._widget_node(working_state)
        working_state.update(shell_state)
        working_state.update(widget_state)

        return await self._merge_node(working_state)


__all__ = [
    "ParallelUIStructuredAssembler",
    "UIParallelOrchestratorAgent",
    "UIShellStructuredAgent",
    "UIWidgetStructuredAgent",
]
