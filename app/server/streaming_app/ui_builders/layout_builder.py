import json
import logging

from pydantic import BaseModel, Field, ConfigDict
from langchain.messages import AIMessage

from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.prompts import UI_PARALLEL_LAYOUT_PLANNER_INSTRUCTIONS
from core.dynamic_app.schemas.widget_schemas.a2ui_custom_catalog_list import CUSTOM_CATALOG
from dynamic_app.ui_agents_graph.widget_tools import (
    get_widget_catalog,
    get_native_component_catalog,
    get_native_component_example,
)

logger = logging.getLogger(__name__)

class ParallelWorkPackage(BaseModel):
    """Single unit of work for one widget worker."""
    package_id: str = Field(description="Unique package id, e.g., pkg-1")
    widgets: list[str] = Field(description="Assigned widgets in this package")
    target_component_ids: list[str] = Field(description="Component IDs this package owns")
    target_data_keys: list[str] = Field(description="Data model keys this package owns")
    priority: int = Field(description="1 high -> 3 lower")
    rationale: str = Field(description="Why this package grouping was chosen")


class ParallelSkeletonPlan(BaseModel):
    """Output model for parallel skeleton planner."""
    model_config = ConfigDict(extra="forbid")
    surface_id: str = Field(description="Target A2UI surface id")
    root_component_id: str = Field(description="Root component id for beginRendering")
    shell_messages: list[dict] = Field(description="A2UI messages for shell rendering")
    work_packages: list[ParallelWorkPackage] = Field(description="Parallel worker packages")


class LayoutBuilder(BaseAgent):
    """Single-step planner: select widgets + build shell + build work packages."""

    WIDGET_ALIASES = {
        "barchart": "BarGraph",
        "bargraph": "BarGraph",
        "linechart": "LineGraph",
        "linegraph": "LineGraph",
        "map": "MapComponent",
        "mapcomponent": "MapComponent",
        "timeline": "TimelineComponent",
        "timelinecomponent": "TimelineComponent",
        "kpi": "KpiCard",
        "kpicard": "KpiCard",
        "table": "Table",
    }

    def __init__(self):
        super().__init__()
        self.agent_name = "ui_parallel_skeleton_planner"
        self.system_prompt = UI_PARALLEL_LAYOUT_PLANNER_INSTRUCTIONS
        self.tools = [
            get_widget_catalog,
            get_native_component_catalog,
            get_native_component_example,
        ]
        self.response_format = ParallelSkeletonPlan
        self.agent = self.build_agent()

    @staticmethod
    def _is_valid_a2ui_message(message: dict) -> bool:
        if not isinstance(message, dict):
            return False
        keys = {"beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface"}
        return any(key in message and isinstance(message.get(key), dict) for key in keys)

    @staticmethod
    def _build_fallback_shell_messages(
        surface_id: str,
        root_component_id: str,
        work_packages: list[ParallelWorkPackage],
    ) -> list[dict]:
        # Build a minimal valid shell: root column + one loading placeholder per package target component.
        target_component_ids: list[str] = []
        for package in work_packages:
            for component_id in package.target_component_ids:
                if component_id not in target_component_ids:
                    target_component_ids.append(component_id)

        components: list[dict] = [
            {
                "id": root_component_id,
                "component": {
                    "Column": {
                        "children": {"explicitList": target_component_ids},
                        "distribution": "start",
                        "alignment": "stretch",
                    }
                },
            }
        ]
        for component_id in target_component_ids:
            components.append(
                {
                    "id": component_id,
                    "component": {
                        "Text": {
                            "text": {"literalString": f"Loading {component_id}..."},
                            "usageHint": "caption",
                        }
                    },
                }
            )

        return [
            {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": root_component_id,
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": components,
                }
            },
        ]

    def _normalize_shell_messages(self, structured: ParallelSkeletonPlan) -> ParallelSkeletonPlan:
        normalized_shell_messages: list[dict] = []
        for message in structured.shell_messages:
            if self._is_valid_a2ui_message(message):
                # Ensure surfaceId/root are present for beginRendering/surfaceUpdate when possible.
                begin = message.get("beginRendering")
                if isinstance(begin, dict):
                    begin.setdefault("surfaceId", structured.surface_id)
                    begin.setdefault("root", structured.root_component_id)
                surface_update = message.get("surfaceUpdate")
                if isinstance(surface_update, dict):
                    surface_update.setdefault("surfaceId", structured.surface_id)
                    surface_update.setdefault("components", [])
                normalized_shell_messages.append(message)
                continue

            # Fix shorthand forms like {"beginRendering": true} or {"surfaceUpdate": true}
            if isinstance(message, dict):
                if message.get("beginRendering") is True:
                    normalized_shell_messages.append(
                        {
                            "beginRendering": {
                                "surfaceId": structured.surface_id,
                                "root": structured.root_component_id,
                            }
                        }
                    )
                elif message.get("surfaceUpdate") is True:
                    normalized_shell_messages.append(
                        {
                            "surfaceUpdate": {
                                "surfaceId": structured.surface_id,
                                "components": [],
                            }
                        }
                    )

        # If shell is still invalid or empty, generate deterministic fallback.
        if not any(self._is_valid_a2ui_message(message) for message in normalized_shell_messages):
            normalized_shell_messages = self._build_fallback_shell_messages(
                surface_id=structured.surface_id,
                root_component_id=structured.root_component_id,
                work_packages=structured.work_packages,
            )

        structured.shell_messages = normalized_shell_messages
        return structured

    def _normalize_work_packages(self, structured: ParallelSkeletonPlan) -> ParallelSkeletonPlan:
        valid_widgets = {item["widget-name"] for item in CUSTOM_CATALOG}
        fallback_widget = "Text"

        for package in structured.work_packages:
            normalized_widgets: list[str] = []
            for widget in package.widgets:
                widget_key = str(widget).strip()
                alias_key = "".join(ch for ch in widget_key.lower() if ch.isalnum())
                normalized = self.WIDGET_ALIASES.get(alias_key, widget_key)
                if normalized in valid_widgets:
                    normalized_widgets.append(normalized)
                elif normalized == "Text":
                    normalized_widgets.append(normalized)

            if not normalized_widgets:
                # Preserve package integrity and avoid unknown widget names reaching workers.
                normalized_widgets = [fallback_widget]
                if "fallbackText" not in package.target_component_ids:
                    package.target_component_ids = package.target_component_ids or ["fallbackText"]

            # Remove duplicates while preserving order.
            package.widgets = list(dict.fromkeys(normalized_widgets))

        return structured

    async def __call__(self, state: DynamicGraphState):
        response = await self.agent.ainvoke(state)

        structured = response.get("structured_response")
        if not isinstance(structured, ParallelSkeletonPlan):
            # Fallback when adapter returns JSON in content instead of structured_response.
            latest_content = str(response["messages"][-1].content)
            structured = ParallelSkeletonPlan.model_validate_json(latest_content)

        structured = self._normalize_work_packages(structured)
        structured = self._normalize_shell_messages(structured)

        payload = structured.model_dump_json()
        logger.info("Parallel skeleton plan generated with %s package(s).", len(structured.work_packages))
        return {
            "messages": state["messages"] + [
                AIMessage(content=payload, name=self.agent_name)
            ]
        }

async def main():
    """Local smoke test."""
    from langchain.messages import HumanMessage

    agent = LayoutBuilder()
    state: DynamicGraphState = {
        "messages": [HumanMessage(content="Show KPI cards, table, and bar chart for top circuits by customers served.")],
        "suggestions": "",
    }
    result = await agent(state)
    print(json.dumps(json.loads(result["messages"][-1].content), indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
    WIDGET_ALIASES = {
        "barchart": "BarGraph",
        "bargraph": "BarGraph",
        "linechart": "LineGraph",
        "linegraph": "LineGraph",
        "map": "MapComponent",
        "mapcomponent": "MapComponent",
        "timeline": "TimelineComponent",
        "timelinecomponent": "TimelineComponent",
        "kpi": "KpiCard",
        "kpicard": "KpiCard",
        "table": "Table",
    }
