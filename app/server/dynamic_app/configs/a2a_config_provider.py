""" This file provides the agent a2a configurations for all the modules """

from a2a.types import AgentCapabilities, AgentSkill
from a2ui.extension.a2ui_extension import get_a2ui_agent_extension

dynamic_agent_capabilities = AgentCapabilities(
    streaming=True,
    push_notifications=True,
    extensions=[get_a2ui_agent_extension()],
)

get_widget_catalog = AgentSkill(
    id="get_widget_catalog",
    name="get_widget_catalog",
    description="Gathers the names of available components to use",
    tags=["catalog", "info"],
    examples=["Which are the widgets available"],
)

get_widget_schema = AgentSkill(
    id="get_widget_schema",
    name="get_widget_schema",
    description="Returns the template schema for a given widget requested",
    tags=["widget", "info"],
    examples=["Give me the template of bar-graph widget"],
)