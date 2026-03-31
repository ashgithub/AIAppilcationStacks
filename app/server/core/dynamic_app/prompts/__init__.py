"""Centralized prompts for dynamic app agents."""

from .backend_orchestrator import BACKEND_ORCHESTRATOR_INSTRUCTIONS
from .ui_orchestrator import UI_ORCHESTRATOR_INSTRUCTIONS
from .ui_assembly import get_ui_assembly_instructions
from .ui_structured_parallel import (
    UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS,
    UI_PARALLEL_SHELL_INSTRUCTIONS,
    UI_PARALLEL_WIDGET_INSTRUCTIONS,
    build_widget_structured_prompt,
)

__all__ = [
    'BACKEND_ORCHESTRATOR_INSTRUCTIONS',
    'UI_ORCHESTRATOR_INSTRUCTIONS',
    'get_ui_assembly_instructions',
    'UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS',
    'UI_PARALLEL_SHELL_INSTRUCTIONS',
    'UI_PARALLEL_WIDGET_INSTRUCTIONS',
    'build_widget_structured_prompt',
]
