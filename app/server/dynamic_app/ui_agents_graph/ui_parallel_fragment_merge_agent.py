"""Parallel UI fragment merge node."""

from __future__ import annotations

import logging
from typing import Any

from core.dynamic_app.parallel_ui_shared import (
    slugify,
    to_a2ui_value_entry,
)
from core.dynamic_app.schemas.structured_outputs import (
    A2UIShellOutput,
    BarGraphWidgetOutput,
    CardWidgetOutput,
    KpiWidgetOutput,
    LineGraphWidgetOutput,
    MapWidgetOutput,
    TableWidgetOutput,
    TextWidgetOutput,
    TimelineWidgetOutput,
)

logger = logging.getLogger(__name__)


class UIParallelFragmentMergeAgent:
    """Build shell and widget A2UI fragments for streaming nodes."""

    def __init__(self):
        self.agent_name = "parallel_structured_ui_assembly"

    def _build_shell_components(
        self, shell_output: A2UIShellOutput, tasks: list[dict[str, Any]]
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
            section_id = str(task["section_id"])
            section_title_id = str(task["section_title_id"])
            widget_id = str(task["widget_id"])
            slot_label = str(task.get("slot_label") or task.get("widget_name") or "Section")
            children.append(section_id)
            section_title = (
                shell_output.section_titles[index]
                if index < len(shell_output.section_titles)
                else slot_label
            )
            components.extend(
                [
                    {
                        "id": section_id,
                        "component": {
                            shell_output.layout_component: {
                                "children": {"explicitList": [section_title_id, widget_id]},
                                "distribution": shell_output.section_distribution,
                                "alignment": shell_output.section_alignment,
                            }
                        },
                    },
                    {
                        "id": section_title_id,
                        "component": {
                            "Text": {
                                "text": {"literalString": section_title},
                                "usageHint": "h4",
                            }
                        },
                    },
                    {
                        "id": widget_id,
                        "component": {
                            "Text": {
                                "text": {
                                    "literalString": f"Loading {slot_label.lower()}..."
                                },
                                "usageHint": shell_output.placeholder_usage_hint,
                            }
                        },
                    },
                ]
            )
            if shell_output.use_card_sections:
                inner_id = f"{section_id}-inner"
                components[-3] = {
                    "id": section_id,
                    "component": {"Card": {"child": inner_id}},
                }
                components.insert(
                    len(components) - 2,
                    {
                        "id": inner_id,
                        "component": {
                            shell_output.layout_component: {
                                "children": {"explicitList": [section_title_id, widget_id]},
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
        self, task: dict[str, Any], widget_output: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        widget_name = str(task.get("widget_name"))
        task_index = int(task.get("index", 1))
        widget_id = str(task.get("widget_id"))
        prefix = f"{slugify(widget_name)}-{task_index}"
        components: list[dict[str, Any]] = []
        contents: list[dict[str, Any]] = []

        if isinstance(widget_output, BarGraphWidgetOutput):
            labels_key = f"{prefix}-labels"
            values_key = f"{prefix}-values"
            details_key = f"{prefix}-details"
            components.append(
                {
                    "id": widget_id,
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
                    to_a2ui_value_entry(labels_key, [item.label for item in widget_output.data]),
                    to_a2ui_value_entry(values_key, [item.value for item in widget_output.data]),
                    to_a2ui_value_entry(details_key, [item.details for item in widget_output.data]),
                ]
            )
        elif isinstance(widget_output, TimelineWidgetOutput):
            timeline_key = f"{prefix}-timeline"
            details_key = f"{prefix}-details"
            components.append(
                {
                    "id": widget_id,
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
                to_a2ui_value_entry(
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
                to_a2ui_value_entry(details_key, [event.details for event in widget_output.data])
            )
        elif isinstance(widget_output, KpiWidgetOutput):
            kpi_key = f"{prefix}-kpi"
            card_ids = [f"{widget_id}-card-{index}" for index, _ in enumerate(widget_output.data)]
            components.append(
                {
                    "id": widget_id,
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
                        "component": {"KpiCard": {"dataPath": f"/{kpi_key}/{item.key}"}},
                    }
                )
            contents.append(
                to_a2ui_value_entry(
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
                    "id": widget_id,
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
                    to_a2ui_value_entry(labels_key, widget_output.labels),
                    to_a2ui_value_entry(
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
                    to_a2ui_value_entry(details_key, widget_output.details),
                ]
            )
        elif isinstance(widget_output, MapWidgetOutput):
            map_key = f"{prefix}-map"
            components.append(
                {
                    "id": widget_id,
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
                to_a2ui_value_entry(
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
                    "id": widget_id,
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
                    to_a2ui_value_entry(
                        table_key, [row.values | {"id": row.id} for row in widget_output.rows]
                    ),
                    to_a2ui_value_entry(table_details_key, [row.details for row in widget_output.rows]),
                ]
            )
        elif isinstance(widget_output, TextWidgetOutput):
            components.append(
                {
                    "id": widget_id,
                    "component": {
                        "Text": {
                            "text": {"literalString": widget_output.body or widget_output.title},
                            "usageHint": widget_output.usage_hint,
                        }
                    },
                }
            )
        elif isinstance(widget_output, CardWidgetOutput):
            title_id = f"{widget_id}-title"
            body_id = f"{widget_id}-body"
            children = [title_id, body_id]
            components.extend(
                [
                    {
                        "id": widget_id,
                        "component": {"Card": {"child": f"{widget_id}-content"}},
                    },
                    {
                        "id": f"{widget_id}-content",
                        "component": {"Column": {"children": {"explicitList": children}}},
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
                suggestions_id = f"{widget_id}-suggestions"
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
                    "id": widget_id,
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": f"No structured renderer available for {widget_name}."
                            },
                            "usageHint": "caption",
                        }
                    },
                }
            )
        return components, contents
