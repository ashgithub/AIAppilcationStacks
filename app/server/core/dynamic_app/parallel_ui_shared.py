"""Shared helpers for modular parallel UI generation nodes."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, get_args, get_origin

from core.dynamic_app.schemas.structured_outputs import (
    BarGraphWidgetOutput,
    CardWidgetOutput,
    KpiWidgetOutput,
    LineGraphWidgetOutput,
    MapWidgetOutput,
    ParallelWidgetPlan,
    TableWidgetOutput,
    TextWidgetOutput,
    TimelineWidgetOutput,
)

logger = logging.getLogger(__name__)


SUPPORTED_WIDGET_NAMES: tuple[str, ...] = (
    "BarGraph",
    "TimelineComponent",
    "KpiCard",
    "LineGraph",
    "MapComponent",
    "Table",
    "Text",
    "Card",
)


def slugify(value: str) -> str:
    lowered = (value or "widget").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "widget"


def normalize_widget_name(widget_name: str) -> str:
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


def is_supported_widget_name(widget_name: str) -> bool:
    canonical = normalize_widget_name(widget_name)
    return canonical in SUPPORTED_WIDGET_NAMES


def is_no_data_or_out_of_domain(data_context: str) -> bool:
    lowered = (data_context or "").lower()
    no_data_markers = [
        "no data available",
        "no relevant data",
        "cannot process",
        "out of scope",
    ]
    return any(marker in lowered for marker in no_data_markers)


def needs_timeline(data_context: str) -> bool:
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


def extract_structured_result(response: Any, model_cls: Any) -> Any | None:
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


def extract_response_content(response: Any) -> Any:
    if isinstance(response, dict):
        structured = response.get("structured_response")
        if structured is not None:
            return structured
        messages = response.get("messages") or []
        if messages:
            return getattr(messages[-1], "content", None)
        return None
    return getattr(response, "content", response)


def extract_first_json_object(raw_text: str) -> str | None:
    if not isinstance(raw_text, str):
        return None
    start = raw_text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(raw_text)):
        char = raw_text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw_text[start : index + 1]
    return None


def parse_json_loose(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None

    candidate = raw.strip()
    if not candidate:
        return None
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].strip()
    try:
        loaded = json.loads(candidate)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass

    object_slice = extract_first_json_object(raw)
    if not object_slice:
        return None
    try:
        loaded = json.loads(object_slice)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        return None
    return None


def _coerce_for_annotation(value: Any, annotation: Any) -> Any:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (list, list[Any]):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return [value]
    if origin in (dict, dict[Any, Any]):
        return value if isinstance(value, dict) else {}
    if origin is None and annotation in (list, dict):
        if annotation is list:
            return value if isinstance(value, list) else []
        return value if isinstance(value, dict) else {}
    if origin is None and annotation is str:
        return "" if value is None else str(value)
    if origin is None and annotation in (int, float):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", value)
            if match:
                try:
                    parsed = float(match.group(0))
                    return parsed if annotation is float else int(parsed)
                except Exception:
                    return 0
        return 0
    if origin is None and annotation is bool:
        return bool(value)
    if origin is None and annotation is Any:
        return value
    if origin is None and hasattr(annotation, "model_fields"):
        if isinstance(value, dict):
            return coerce_payload_generic(annotation, value)
        return {}
    if origin is not None and type(None) in args:
        inner_types = [arg for arg in args if arg is not type(None)]
        if value is None:
            return None
        for inner in inner_types:
            coerced = _coerce_for_annotation(value, inner)
            if coerced is not None:
                return coerced
        return value
    return value


def coerce_payload_generic(model_cls: Any, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    normalized: dict[str, Any] = {}
    for field_name, field_info in model_cls.model_fields.items():
        if field_name in payload:
            normalized[field_name] = _coerce_for_annotation(
                payload.get(field_name), field_info.annotation
            )
            continue
        if field_info.default_factory is not None:
            try:
                normalized[field_name] = field_info.default_factory()
            except Exception:
                normalized[field_name] = None
            continue
        if field_info.default is not None:
            normalized[field_name] = field_info.default
            continue
    return normalized


def default_from_json_schema(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return None
    if "default" in schema:
        return schema["default"]
    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        for option in schema["anyOf"]:
            if isinstance(option, dict) and option.get("type") == "null":
                continue
            candidate = default_from_json_schema(option)
            if candidate is not None:
                return candidate
    schema_type = schema.get("type")
    if schema_type == "object":
        properties = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        output: dict[str, Any] = {}
        for key, prop_schema in properties.items():
            if key in required or "default" in (prop_schema or {}):
                output[key] = default_from_json_schema(prop_schema)
        return output
    if schema_type == "array":
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 0) or 0
        count = max(1, int(min_items)) if min_items else 1
        return [default_from_json_schema(items_schema) for _ in range(count)]
    if schema_type == "string":
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]
        return ""
    if schema_type == "number":
        return 0.0
    if schema_type == "integer":
        return 0
    if schema_type == "boolean":
        return False
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    return None


def to_a2ui_value_entry(key: str, value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"key": key, "valueBoolean": value}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {"key": key, "valueNumber": float(value)}
    if isinstance(value, str):
        return {"key": key, "valueString": value}
    if isinstance(value, list):
        return {
            "key": key,
            "valueMap": [to_a2ui_value_entry(str(index), item) for index, item in enumerate(value)],
        }
    if isinstance(value, dict):
        return {
            "key": key,
            "valueMap": [to_a2ui_value_entry(str(item_key), item_value) for item_key, item_value in value.items()],
        }
    return {"key": key, "valueString": str(value)}


def get_widget_model_registry() -> dict[str, Any]:
    return {
        "BarGraph": BarGraphWidgetOutput,
        "TimelineComponent": TimelineWidgetOutput,
        "KpiCard": KpiWidgetOutput,
        "LineGraph": LineGraphWidgetOutput,
        "MapComponent": MapWidgetOutput,
        "Table": TableWidgetOutput,
        "Text": TextWidgetOutput,
        "Card": CardWidgetOutput,
    }


def build_widget_execution_tasks(plan: ParallelWidgetPlan) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    next_index = 1
    for selected in plan.widget_tasks:
        canonical_name = normalize_widget_name(selected.widget_name)
        if not is_supported_widget_name(canonical_name):
            logger.warning(
                "Dropping unsupported widget from execution tasks | original=%s canonical=%s",
                selected.widget_name,
                canonical_name,
            )
            continue
        slug = slugify(canonical_name)
        tasks.append(
            {
                "widget_name": canonical_name,
                "slot_label": selected.slot_label or canonical_name,
                "index": next_index,
                "section_id": f"section-{slug}-{next_index}",
                "section_title_id": f"section-title-{slug}-{next_index}",
                "widget_id": f"widget-{slug}-{next_index}",
            }
        )
        next_index += 1

    if not tasks:
        tasks.append(
            {
                "widget_name": "Table",
                "slot_label": "Details",
                "index": 1,
                "section_id": "section-table-1",
                "section_title_id": "section-title-table-1",
                "widget_id": "widget-table-1",
            }
        )
    return tasks
