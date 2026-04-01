"""Centralized prompts for dynamic app agents."""

from .backend_orchestrator import BACKEND_ORCHESTRATOR_INSTRUCTIONS
from .ui_structured_parallel import (
    UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS,
    UI_PARALLEL_SHELL_INSTRUCTIONS,
    UI_PARALLEL_WIDGET_INSTRUCTIONS,
    build_widget_structured_prompt,
)

__all__ = [
    'BACKEND_ORCHESTRATOR_INSTRUCTIONS',
    'UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS',
    'UI_PARALLEL_SHELL_INSTRUCTIONS',
    'UI_PARALLEL_WIDGET_INSTRUCTIONS',
    'build_widget_structured_prompt',
]
