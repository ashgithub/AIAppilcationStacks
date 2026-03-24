"""Centralized prompts for dynamic app agents."""

from .backend_orchestrator import BACKEND_ORCHESTRATOR_INSTRUCTIONS
from .ui_orchestrator import UI_ORCHESTRATOR_INSTRUCTIONS
from .ui_assembly import get_ui_assembly_instructions
from .ui_parallel import (
    UI_PARALLEL_SKELETON_PLANNER_INSTRUCTIONS,
    UI_PARALLEL_LAYOUT_PLANNER_INSTRUCTIONS,
    UI_PARALLEL_FRAGMENT_MERGER_INSTRUCTIONS,
    get_ui_parallel_widget_worker_instructions,
)

__all__ = [
    'BACKEND_ORCHESTRATOR_INSTRUCTIONS',
    'UI_ORCHESTRATOR_INSTRUCTIONS',
    'get_ui_assembly_instructions',
    'UI_PARALLEL_SKELETON_PLANNER_INSTRUCTIONS',
    'UI_PARALLEL_LAYOUT_PLANNER_INSTRUCTIONS',
    'UI_PARALLEL_FRAGMENT_MERGER_INSTRUCTIONS',
    'get_ui_parallel_widget_worker_instructions',
]
