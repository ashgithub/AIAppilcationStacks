"""Centralized prompts for dynamic app agents."""

from .backend_orchestrator import BACKEND_ORCHESTRATOR_INSTRUCTIONS
from .ui_orchestrator import UI_ORCHESTRATOR_INSTRUCTIONS
from .ui_assembly import get_ui_assembly_instructions

__all__ = [
    'BACKEND_ORCHESTRATOR_INSTRUCTIONS',
    'UI_ORCHESTRATOR_INSTRUCTIONS',
    'get_ui_assembly_instructions'
]