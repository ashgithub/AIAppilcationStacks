"""Experimental parallel UI agents using modular structured outputs."""

from __future__ import annotations

import json
import re
import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from langchain.messages import AIMessage, HumanMessage

from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.prompts import (
    UI_PARALLEL_ORCHESTRATOR_INSTRUCTIONS,
    UI_PARALLEL_SHELL_INSTRUCTIONS,
    UI_PARALLEL_WIDGET_INSTRUCTIONS,
    build_widget_structured_prompt,
)
from core.dynamic_app.schemas.structured_outputs import (
    A2UIShellOutput,
    BarGraphWidgetOutput,
    CardWidgetOutput,
    KpiWidgetOutput,
    LineGraphWidgetOutput,
    MapWidgetOutput,
    ParallelWidgetPlan,
    SuggestedWidgetTask,
    TableWidgetOutput,
    TextWidgetOutput,
    TimelineWidgetOutput,
)
from dynamic_app.ui_agents_graph.widget_tools import (
    get_native_component_catalog,
    get_widget_catalog,
)

MAX_PARALLEL_WIDGETS = 4
logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    lowered = (value or "widget").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "widget"


def _normalize_widget_name(widget_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", (widget_name or "").lower())
    aliases = {
        "bargraph": "BarGraph",
        "linegraph": "LineGraph",
        "timelinecomponent": "TimelineComponent",
        "timeline": "TimelineComponent",
        "kpicard": "KpiCard",
        "mapcomponent": "MapComponent",
        "table": "Table",
        "text": "Text",
        "card": "Card",
    }
    return aliases.get(normalized, widget_name)


def _is_no_data_or_out_of_domain(data_context: str) -> bool:
    lowered = (data_context or "").lower()
    no_data_markers = [
        "no data available",
        "no relevant data",
        "cannot process",
        "out of scope",
    ]
    return any(marker in lowered for marker in no_data_markers)


def _needs_timeline(data_context: str) -> bool:
    lowered = (data_context or "").lower()
    timeline_markers = [
        "timeline",
        "step",
        "procedure",
        "process",
        "manual",
        "sequence",
        "protocol",
        "guideline",
    ]
    return any(marker in lowered for marker in timeline_markers)


def _extract_structured_result(response: Any, model_cls: Any) -> Any | None:
    if isinstance(response, model_cls):
        return response

    if isinstance(response, dict):
        structured = response.get("structured_response")
        if isinstance(structured, model_cls):
            return structured
        if structured is not None:
            try:
                return model_cls.model_validate(structured)
            except Exception as exc:
                logger.warning(
                    "Failed to validate structured_response for %s: %s",
                    model_cls.__name__,
                    exc,
                )

        messages = response.get("messages") or []
        if messages:
            content = getattr(messages[-1], "content", "")
            if isinstance(content, str):
                try:
                    return model_cls.model_validate_json(content)
                except Exception as exc:
                    logger.warning(
                        "Failed to parse message content as %s JSON. Content preview=%s error=%s",
                        model_cls.__name__,
                        content[:300],
                        exc,
                    )

    return None


@dataclass
class WidgetExecutionTask:
    widget_name: str
    slot_label: str
    index: int
    section_id: str
    section_title_id: str
    widget_id: str


def _to_a2ui_value_entry(key: str, value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"key": key, "valueBoolean": value}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {"key": key, "valueNumber": float(value)}
    if isinstance(value, str):
        return {"key": key, "valueString": value}
    if isinstance(value, list):
        return {
            "key": key,
            "valueMap": [
                _to_a2ui_value_entry(str(index), item) for index, item in enumerate(value)
            ],
        }
    if isinstance(value, dict):
        return {
            "key": key,
            "valueMap": [_to_a2ui_value_entry(str(k), v) for k, v in value.items()],
        }
    return {"key": key, "valueString": str(value)}


class UIParallelOrchestratorAgent(BaseAgent):
    """Select widgets as a compact, structured plan."""

    def __init__(self):
        super().__init__()
        self.model="xai.grok-4-fast-non-reasoning"
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
            _is_no_data_or_out_of_domain(data_context),
        )
        if _is_no_data_or_out_of_domain(data_context):
            logger.info("Planner using guidance-mode static plan.")
            return ParallelWidgetPlan(
                summary="Guidance mode with native components.",
                widget_tasks=[
                    SuggestedWidgetTask(widget_name="Text", slot_label="Guidance", priority=1),
                    SuggestedWidgetTask(widget_name="Card", slot_label="Suggestions", priority=2),
                ],
            )

        raw = await self.agent.ainvoke(state)
        extracted = _extract_structured_result(raw, ParallelWidgetPlan)
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
                canonical = _normalize_widget_name(task.widget_name)
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

            if _needs_timeline(data_context) and "timelinecomponent" not in {
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


class UIShellStructuredAgent(BaseAgent):
    """Generate shell metadata from plan and data context."""

    def __init__(self):
        super().__init__()
        self.model="xai.grok-4-fast-reasoning"
        self.agent_name = "ui_parallel_shell"
        self.system_prompt = UI_PARALLEL_SHELL_INSTRUCTIONS
        self.response_format = A2UIShellOutput
        self.agent = self.build_agent()

    async def generate_shell(
        self, plan: ParallelWidgetPlan, data_context: str
    ) -> A2UIShellOutput:
        task_labels = [task.slot_label or task.widget_name for task in plan.widget_tasks]
        mode = "guidance" if _is_no_data_or_out_of_domain(data_context) else "data_visualization"
        prompt = (
            f"Mode: {mode}\n"
            "Native components available for shell: Text, Column, Row, Card, Button, Image, Icon.\n"
            f"Planner summary: {plan.summary}\n"
            f"Widget sections: {', '.join(task_labels)}\n"
            f"Data context:\n{data_context}"
        )
        response = await self.agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        structured = _extract_structured_result(response, A2UIShellOutput)
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


class UIWidgetStructuredAgent(BaseAgent):
    """Single reusable widget agent with dynamic structured output binding."""

    def __init__(self):
        super().__init__()
        self.model="xai.grok-4-fast-reasoning"
        self.agent_name = "ui_parallel_widget"
        self.system_prompt = UI_PARALLEL_WIDGET_INSTRUCTIONS
        self._model_registry: dict[str, Any] = {
            "BarGraph": BarGraphWidgetOutput,
            "TimelineComponent": TimelineWidgetOutput,
            "KpiCard": KpiWidgetOutput,
            "LineGraph": LineGraphWidgetOutput,
            "MapComponent": MapWidgetOutput,
            "Table": TableWidgetOutput,
            "Text": TextWidgetOutput,
            "Card": CardWidgetOutput,
        }
        self._agent_registry: dict[str, Any] = {}

    async def generate_widget(self, widget_name: str, data_context: str) -> Any:
        canonical_name = _normalize_widget_name(widget_name)
        model_cls = self._model_registry.get(canonical_name)
        if model_cls is None:
            logger.warning("Widget skipped: unsupported widget_name=%s", widget_name)
            return None
        agent = self._agent_registry.get(canonical_name)
        if agent is None:
            agent = self.build_agent(response_format=model_cls)
            self._agent_registry[canonical_name] = agent
        response = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=build_widget_structured_prompt(
                            canonical_name,
                            data_context,
                        )
                    )
                ]
            }
        )
        structured = _extract_structured_result(response, model_cls)
        if structured is None:
            logger.warning(
                "Widget structured extraction failed | widget=%s model=%s context_len=%s",
                canonical_name,
                model_cls.__name__,
                len(data_context),
            )
        else:
            logger.info(
                "Widget success | widget=%s model=%s",
                canonical_name,
                model_cls.__name__,
            )
        return structured


class ParallelUIStructuredAssembler:
    """
    Experimental assembler:
    1) planner picks widget list,
    2) shell and widget payloads are generated independently,
    3) final A2UI payload is composed in deterministic code.
    """

    def __init__(self):
        self.agent_name = "parallel_structured_ui_assembly"
        self._planner = UIParallelOrchestratorAgent()
        self._shell = UIShellStructuredAgent()
        self._widget = UIWidgetStructuredAgent()

    def _build_execution_tasks(self, plan: ParallelWidgetPlan) -> list[WidgetExecutionTask]:
        tasks: list[WidgetExecutionTask] = []
        for index, selected in enumerate(plan.widget_tasks, start=1):
            canonical_name = _normalize_widget_name(selected.widget_name)
            slug = _slugify(canonical_name)
            tasks.append(
                WidgetExecutionTask(
                    widget_name=canonical_name,
                    slot_label=selected.slot_label or canonical_name,
                    index=index,
                    section_id=f"section-{slug}-{index}",
                    section_title_id=f"section-title-{slug}-{index}",
                    widget_id=f"widget-{slug}-{index}",
                )
            )
        if not tasks:
            tasks.append(
                WidgetExecutionTask(
                    widget_name="Table",
                    slot_label="Details",
                    index=1,
                    section_id="section-table-1",
                    section_title_id="section-title-table-1",
                    widget_id="widget-table-1",
                )
            )
        return tasks

    def _build_shell_components(
        self, shell_output: A2UIShellOutput, tasks: list[WidgetExecutionTask]
    ) -> tuple[list[dict[str, Any]], str]:
        children = ["surface-title"]
        components: list[dict[str, Any]] = [
            {
                "id": "surface-title",
                "component": {
                    "Text": {
                        "text": {"literalString": shell_output.surface_title or "Dashboard"},
                        "usageHint": "h2",
                    }
                },
            }
        ]
        if shell_output.intro_text:
            children.append("surface-intro")
            components.append(
                {
                    "id": "surface-intro",
                    "component": {
                        "Text": {
                            "text": {"literalString": shell_output.intro_text},
                            "usageHint": "body",
                        }
                    },
                }
            )

        for index, task in enumerate(tasks):
            children.append(task.section_id)
            section_title = (
                shell_output.section_titles[index]
                if index < len(shell_output.section_titles)
                else task.slot_label
            )
            components.extend(
                [
                    {
                        "id": task.section_id,
                        "component": {
                            shell_output.layout_component: {
                                "children": {
                                    "explicitList": [task.section_title_id, task.widget_id]
                                },
                                "distribution": shell_output.section_distribution,
                                "alignment": shell_output.section_alignment,
                            }
                        },
                    },
                    {
                        "id": task.section_title_id,
                        "component": {
                            "Text": {
                                "text": {"literalString": section_title},
                                "usageHint": "h4",
                            }
                        },
                    },
                    {
                        "id": task.widget_id,
                        "component": {
                            "Text": {
                                "text": {
                                    "literalString": f"Loading {task.slot_label.lower()}..."
                                },
                                "usageHint": shell_output.placeholder_usage_hint,
                            }
                        },
                    },
                ]
            )
            if shell_output.use_card_sections:
                inner_id = f"{task.section_id}-inner"
                components[-3] = {
                    "id": task.section_id,
                    "component": {
                        "Card": {"child": inner_id}
                    },
                }
                components.insert(
                    len(components) - 2,
                    {
                        "id": inner_id,
                        "component": {
                            shell_output.layout_component: {
                                "children": {
                                    "explicitList": [task.section_title_id, task.widget_id]
                                },
                                "distribution": shell_output.section_distribution,
                                "alignment": shell_output.section_alignment,
                            }
                        },
                    },
                )

        root_component = {
            "id": shell_output.root_id,
            "component": {
                "Column": {
                    "children": {"explicitList": children},
                    "distribution": "start",
                    "alignment": "stretch",
                }
            },
        }
        return [root_component, *components], (shell_output.intro_text or shell_output.surface_title)

    def _build_widget_payload(
        self, task: WidgetExecutionTask, widget_output: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        prefix = f"{_slugify(task.widget_name)}-{task.index}"
        components: list[dict[str, Any]] = []
        contents: list[dict[str, Any]] = []

        if isinstance(widget_output, BarGraphWidgetOutput):
            labels_key = f"{prefix}-labels"
            values_key = f"{prefix}-values"
            details_key = f"{prefix}-details"
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "BarGraph": {
                            "dataPath": f"/{values_key}",
                            "labelPath": f"/{labels_key}",
                            "detailsPath": f"/{details_key}",
                            "title": widget_output.title,
                            "orientation": widget_output.orientation,
                            "interactive": True,
                            "colorful": True,
                        }
                    },
                }
            )
            contents.extend(
                [
                    _to_a2ui_value_entry(labels_key, [item.label for item in widget_output.data]),
                    _to_a2ui_value_entry(values_key, [item.value for item in widget_output.data]),
                    _to_a2ui_value_entry(details_key, [item.details for item in widget_output.data]),
                ]
            )

        elif isinstance(widget_output, TimelineWidgetOutput):
            timeline_key = f"{prefix}-timeline"
            details_key = f"{prefix}-details"
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "TimelineComponent": {
                            "dataPath": f"/{timeline_key}",
                            "detailsPath": f"/{details_key}",
                            "expandable": True,
                            "compactPreview": True,
                            "action": {"name": "queue_timeline_event"},
                        }
                    },
                }
            )
            contents.append(
                _to_a2ui_value_entry(
                    timeline_key,
                    [
                        {
                            "date": event.date,
                            "title": event.title,
                            "description": event.description,
                            "category": event.category,
                        }
                        for event in widget_output.data
                    ],
                )
            )
            contents.append(
                _to_a2ui_value_entry(details_key, [event.details for event in widget_output.data])
            )

        elif isinstance(widget_output, KpiWidgetOutput):
            kpi_key = f"{prefix}-kpi"
            card_ids = [f"{task.widget_id}-card-{index}" for index, _ in enumerate(widget_output.data)]
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "Row": {
                            "children": {"explicitList": card_ids},
                            "distribution": "spaceEvenly",
                            "alignment": "stretch",
                        }
                    },
                }
            )
            for index, item in enumerate(widget_output.data):
                components.append(
                    {
                        "id": card_ids[index],
                        "weight": 1,
                        "component": {
                            "KpiCard": {"dataPath": f"/{kpi_key}/{item.key}"}
                        },
                    }
                )
            contents.append(
                _to_a2ui_value_entry(
                    kpi_key,
                    {
                        item.key: {
                            "label": item.label,
                            "value": item.value,
                            "unit": item.unit,
                            "change": item.change,
                            "changeLabel": item.changeLabel,
                            "icon": item.icon,
                            "color": item.color,
                            **item.details,
                        }
                        for item in widget_output.data
                    },
                )
            )

        elif isinstance(widget_output, LineGraphWidgetOutput):
            labels_key = f"{prefix}-labels"
            series_key = f"{prefix}-series"
            details_key = f"{prefix}-details"
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "LineGraph": {
                            "labelPath": f"/{labels_key}",
                            "seriesPath": f"/{series_key}",
                            "detailsPath": f"/{details_key}",
                            "title": widget_output.title,
                            "showPoints": True,
                            "showArea": True,
                            "animated": True,
                        }
                    },
                }
            )
            contents.extend(
                [
                    _to_a2ui_value_entry(labels_key, widget_output.labels),
                    _to_a2ui_value_entry(
                        series_key,
                        [
                            {
                                "name": series.name,
                                "color": series.color,
                                "values": series.values,
                            }
                            for series in widget_output.series
                        ],
                    ),
                    _to_a2ui_value_entry(details_key, widget_output.details),
                ]
            )

        elif isinstance(widget_output, MapWidgetOutput):
            map_key = f"{prefix}-map"
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "MapComponent": {
                            "dataPath": f"/{map_key}",
                            "centerLat": widget_output.center_lat,
                            "centerLng": widget_output.center_lng,
                            "zoom": widget_output.zoom,
                            "showInfoPanel": True,
                            "action": {"name": "flag_circuit"},
                        }
                    },
                }
            )
            contents.append(
                _to_a2ui_value_entry(
                    map_key,
                    [
                        {
                            "name": marker.name,
                            "latitude": marker.latitude,
                            "longitude": marker.longitude,
                            **marker.details,
                        }
                        for marker in widget_output.markers
                    ],
                )
            )

        elif isinstance(widget_output, TableWidgetOutput):
            table_key = f"{prefix}-table"
            table_details_key = f"{prefix}-table-details"
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "Table": {
                            "dataPath": f"/{table_key}",
                            "detailsPath": f"/{table_details_key}",
                            "title": widget_output.title,
                            "columns": [col.model_dump() for col in widget_output.columns],
                        }
                    },
                }
            )
            contents.extend(
                [
                    _to_a2ui_value_entry(
                        table_key,
                        [row.values | {"id": row.id} for row in widget_output.rows],
                    ),
                    _to_a2ui_value_entry(
                        table_details_key, [row.details for row in widget_output.rows]
                    ),
                ]
            )
        elif isinstance(widget_output, TextWidgetOutput):
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "Text": {
                            "text": {"literalString": widget_output.body or widget_output.title},
                            "usageHint": widget_output.usage_hint,
                        }
                    },
                }
            )
        elif isinstance(widget_output, CardWidgetOutput):
            title_id = f"{task.widget_id}-title"
            body_id = f"{task.widget_id}-body"
            children = [title_id, body_id]
            components.extend(
                [
                    {
                        "id": task.widget_id,
                        "component": {"Card": {"child": f"{task.widget_id}-content"}},
                    },
                    {
                        "id": f"{task.widget_id}-content",
                        "component": {
                            "Column": {"children": {"explicitList": children}}
                        },
                    },
                    {
                        "id": title_id,
                        "component": {
                            "Text": {
                                "text": {"literalString": widget_output.title},
                                "usageHint": "h4",
                            }
                        },
                    },
                    {
                        "id": body_id,
                        "component": {
                            "Text": {
                                "text": {"literalString": widget_output.body},
                                "usageHint": "body",
                            }
                        },
                    },
                ]
            )
            if widget_output.suggestions:
                suggestions_id = f"{task.widget_id}-suggestions"
                children.append(suggestions_id)
                components.append(
                    {
                        "id": suggestions_id,
                        "component": {
                            "Text": {
                                "text": {
                                    "literalString": "Try asking: "
                                    + ", ".join(widget_output.suggestions[:3])
                                },
                                "usageHint": "caption",
                            }
                        },
                    }
                )

        if not components:
            components.append(
                {
                    "id": task.widget_id,
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": f"No structured renderer available for {task.widget_name}."
                            },
                            "usageHint": "caption",
                        }
                    },
                }
            )

        return components, contents

    async def __call__(self, state: DynamicGraphState) -> DynamicGraphState:
        data_context = str(state["messages"][-1].content if state["messages"] else "")
        logger.info("Parallel assembler start | data_context_len=%s", len(data_context))
        plan = await self._planner.generate_plan(state)
        tasks = self._build_execution_tasks(plan)
        logger.info(
            "Parallel assembler execution tasks | count=%s widgets=%s",
            len(tasks),
            [task.widget_name for task in tasks],
        )
        shell_output = await self._shell.generate_shell(plan, data_context)
        if _is_no_data_or_out_of_domain(data_context):
            shell_output.use_card_sections = True
            if not shell_output.intro_text:
                shell_output.intro_text = (
                    "I can help you explore outage, energy, infrastructure, and disaster response data."
                )
            logger.info("Parallel assembler forced guidance shell settings for no-data/out-of-scope.")

        shell_components, assistant_text = self._build_shell_components(shell_output, tasks)
        logger.info(
            "Shell components built | component_count=%s assistant_text_len=%s",
            len(shell_components),
            len(assistant_text or ""),
        )

        widget_outputs = await asyncio.gather(
            *[
                self._widget.generate_widget(task.widget_name, data_context)
                for task in tasks
            ],
            return_exceptions=True,
        )

        shell_components_by_id = {component["id"]: component for component in shell_components}
        ordered_component_ids = [component["id"] for component in shell_components]
        merged_data_contents: list[dict[str, Any]] = []
        widget_component_batches: list[list[dict[str, Any]] | None] = []

        for task, widget_output in zip(tasks, widget_outputs):
            if isinstance(widget_output, Exception):
                logger.error(
                    "Widget generation raised exception | widget=%s slot=%s",
                    task.widget_name,
                    task.slot_label,
                    exc_info=(
                        type(widget_output),
                        widget_output,
                        widget_output.__traceback__,
                    ),
                )
                widget_component_batches.append(None)
                continue
            if widget_output is None:
                logger.warning(
                    "Widget generation returned None | widget=%s slot=%s",
                    task.widget_name,
                    task.slot_label,
                )
            widget_components, widget_contents = self._build_widget_payload(task, widget_output)
            logger.info(
                "Widget payload built | widget=%s components=%s data_entries=%s",
                task.widget_name,
                len(widget_components),
                len(widget_contents),
            )
            widget_component_batches.append(widget_components)
            merged_data_contents.extend(widget_contents)

        surface_id = shell_output.surface_id or "dashboard"
        root_id = shell_output.root_id or "root-layout"
        messages_payload: list[dict[str, Any]] = [
            {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": root_id,
                    "styles": {
                        "font": shell_output.style_font or "Arial",
                        "primaryColor": shell_output.style_primary_color or "#007bff",
                    },
                }
            }
        ]

        # Step 1: Shell skeleton message (native layout + placeholders).
        progressive_state = {
            component_id: shell_components_by_id[component_id]
            for component_id in ordered_component_ids
        }
        messages_payload.append(
            {
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": list(progressive_state.values()),
                }
            }
        )

        # Step 2+: One update per widget replacement to keep stream chunks joinable.
        for _task, widget_components in zip(tasks, widget_component_batches):
            if not widget_components:
                continue
            touched = False
            for component in widget_components:
                component_id = component["id"]
                if component_id not in progressive_state:
                    ordered_component_ids.append(component_id)
                progressive_state[component_id] = component
                touched = True
            if touched:
                messages_payload.append(
                    {
                        "surfaceUpdate": {
                            "surfaceId": surface_id,
                            "components": [
                                progressive_state[component_id]
                                for component_id in ordered_component_ids
                                if component_id in progressive_state
                            ],
                        }
                    }
                )

        if merged_data_contents:
            messages_payload.append(
                {
                    "dataModelUpdate": {
                        "surfaceId": surface_id,
                        "path": "/",
                        "contents": merged_data_contents,
                    }
                }
            )
        else:
            logger.warning(
                "No merged data contents were generated for this response | tasks=%s",
                len(tasks),
            )

        content = (
            f"{assistant_text}\n---a2ui_JSON---\n"
            f"{json.dumps(messages_payload, ensure_ascii=False)}"
        )
        logger.info(
            "Parallel assembler final payload | messages=%s data_entries=%s surface_id=%s root_id=%s",
            len(messages_payload),
            len(merged_data_contents),
            surface_id,
            root_id,
        )
        return {
            "messages": state["messages"]
            + [AIMessage(content=content, name=self.agent_name)]
        }
