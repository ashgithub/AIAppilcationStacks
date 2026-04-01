""" File to store the common pydantic classes or struct configs """

# region Imports
from typing import Any
from langgraph.graph import MessagesState
# endregion Imports

# region Types
class DynamicGraphState(MessagesState, total=False):
    """ Class that holds the dynamic graph state """
    suggestions: str
    parallel_data_context: str
    parallel_widget_plan: dict[str, Any]
    parallel_execution_tasks: list[dict[str, Any]]
    parallel_shell_output: dict[str, Any]
    parallel_skeleton_fragment: dict[str, Any]
    parallel_widget_fragment_1: dict[str, Any]
    parallel_widget_fragment_2: dict[str, Any]
    parallel_widget_fragment_3: dict[str, Any]
    parallel_widget_fragment_4: dict[str, Any]

# endregion Types
