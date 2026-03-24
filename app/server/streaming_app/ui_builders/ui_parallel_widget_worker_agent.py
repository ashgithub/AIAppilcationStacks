"""Reusable parallel widget worker agent."""
import json
import logging
from typing import Any

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage

from core.gen_ai_provider import GenAIProvider
from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.prompts.ui_parallel import get_ui_parallel_widget_worker_instructions
from dynamic_app.ui_agents_graph.widget_tools import (
    create_custom_component_tools,
    get_native_component_catalog,
    get_native_component_example,
)

logger = logging.getLogger(__name__)

class WidgetWorkerOutput(BaseModel):
    """Structured output for one worker package."""
    package_id: str = Field(description="Package id from planner")
    surface_messages: list[dict] = Field(description="A2UI fragment messages for this package")
    target_component_ids: list[str] = Field(description="Owned component ids")
    target_data_keys: list[str] = Field(description="Owned data keys")
    estimated_complexity: str = Field(description="low | medium | high")
    warnings: list[str] = Field(description="Validation or coverage warnings")


class UIParallelWidgetWorkerAgent(BaseAgent):
    """Single worker implementation; instantiate/call in parallel across packages."""

    def __init__(self, inline_catalog: list | None = None):
        super().__init__()
        self.model="xai.grok-4-fast-reasoning"
        self.agent_name="widget_worker"
        self.gen_ai_provider = GenAIProvider()
        self.inline_catalog = inline_catalog or []
        self.response_format=WidgetWorkerOutput
        self.agent=None

    @staticmethod
    def _extract_component_type(component_entry: dict[str, Any]) -> str:
        component_wrapper = component_entry.get("component")
        if not isinstance(component_wrapper, dict) or not component_wrapper:
            return ""
        return str(next(iter(component_wrapper.keys())))

    @staticmethod
    def _extract_component_props(component_entry: dict[str, Any]) -> dict[str, Any]:
        component_wrapper = component_entry.get("component")
        if not isinstance(component_wrapper, dict) or not component_wrapper:
            return {}
        component_type = str(next(iter(component_wrapper.keys())))
        props = component_wrapper.get(component_type, {})
        return props if isinstance(props, dict) else {}

    @staticmethod
    def _path_to_segments(path: str) -> list[str]:
        if not isinstance(path, str):
            return []
        cleaned = path.strip().lstrip("/")
        if not cleaned:
            return []
        return [segment for segment in cleaned.split("/") if segment]

    @staticmethod
    def _value_map_to_keyed_dict(value_map: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for entry in value_map:
            if not isinstance(entry, dict):
                continue
            key = entry.get("key")
            if isinstance(key, str):
                result[key] = entry
        return result

    @staticmethod
    def _get_value(entry: dict[str, Any]) -> Any:
        for key in ("valueString", "valueNumber", "valueBoolean", "valueBool", "valueMap"):
            if key in entry:
                return entry.get(key)
        return None

    @staticmethod
    def _set_value(entry: dict[str, Any], value: Any) -> None:
        for key in ("valueString", "valueNumber", "valueBoolean", "valueBool", "valueMap"):
            entry.pop(key, None)
        if isinstance(value, bool):
            entry["valueBoolean"] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            entry["valueNumber"] = value
        elif isinstance(value, list):
            entry["valueMap"] = value
        else:
            entry["valueString"] = str(value)

    def _normalize_map_marker_value_map(self, marker_entries: list[dict[str, Any]], index: int) -> list[dict[str, Any]]:
        if not marker_entries:
            return marker_entries

        by_key: dict[str, dict[str, Any]] = {}
        for entry in marker_entries:
            key = str(entry.get("key", "")).strip()
            if key:
                by_key[key] = entry

        if "name" not in by_key and "location" in by_key:
            location_entry = by_key["location"]
            location_entry["key"] = "name"
            by_key["name"] = location_entry
            by_key.pop("location", None)

        if "latitude" not in by_key and "lat" in by_key:
            by_key["lat"]["key"] = "latitude"
            by_key["latitude"] = by_key["lat"]
            by_key.pop("lat", None)

        if "longitude" not in by_key and "lng" in by_key:
            by_key["lng"]["key"] = "longitude"
            by_key["longitude"] = by_key["lng"]
            by_key.pop("lng", None)

        if "name" not in by_key:
            marker_entries.append({"key": "name", "valueString": f"Outage Site {index + 1}"})
            by_key["name"] = marker_entries[-1]

        if "description" not in by_key:
            by_key["description"] = {"key": "description", "valueString": "Outage investigation area"}
            marker_entries.append(by_key["description"])

        if "status" not in by_key:
            by_key["status"] = {"key": "status", "valueString": "Investigating"}
            marker_entries.append(by_key["status"])

        # Ensure displayed name is meaningful, not a repeated generic label.
        name_value = str(self._get_value(by_key["name"]) or "").strip()
        if not name_value or name_value.lower() == "location":
            lat = self._get_value(by_key.get("latitude", {}))
            lon = self._get_value(by_key.get("longitude", {}))
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                name_value = f"Outage @ {lat:.3f},{lon:.3f}"
            else:
                name_value = f"Outage Site {index + 1}"
            self._set_value(by_key["name"], name_value)

        return marker_entries

    def _normalize_worker_output(
        self,
        output: WidgetWorkerOutput,
        widgets: list[str],
        target_component_ids: list[str],
        target_data_keys: list[str],
        context_text: str = "",
    ) -> WidgetWorkerOutput:
        allowed_component_ids = set(target_component_ids or [])
        allowed_data_keys = set(target_data_keys or [])
        has_map_widget = any(widget == "MapComponent" for widget in widgets)
        has_kpi_widget = any(widget == "KpiCard" for widget in widgets)

        normalized_messages: list[dict] = []
        for message in output.surface_messages:
            if not isinstance(message, dict):
                continue

            surface_update = message.get("surfaceUpdate")
            if isinstance(surface_update, dict):
                components = surface_update.get("components", [])
                if isinstance(components, list):
                    filtered_components: list[dict[str, Any]] = []
                    for component in components:
                        if not isinstance(component, dict):
                            continue
                        component_id = component.get("id")
                        if allowed_component_ids and isinstance(component_id, str) and component_id not in allowed_component_ids:
                            continue
                        filtered_components.append(component)
                    surface_update["components"] = filtered_components
                normalized_messages.append(message)
                continue

            data_update = message.get("dataModelUpdate")
            if isinstance(data_update, dict):
                contents = data_update.get("contents", [])
                if not isinstance(contents, list):
                    normalized_messages.append(message)
                    continue

                normalized_contents: list[dict[str, Any]] = []
                for content in contents:
                    if not isinstance(content, dict):
                        continue
                    content_key = content.get("key")
                    if allowed_data_keys and isinstance(content_key, str) and content_key not in allowed_data_keys:
                        continue

                    if has_map_widget and isinstance(content.get("valueMap"), list):
                        for idx, marker in enumerate(content["valueMap"]):
                            if not isinstance(marker, dict):
                                continue
                            if isinstance(marker.get("valueMap"), list):
                                marker["valueMap"] = self._normalize_map_marker_value_map(marker["valueMap"], idx)

                    if has_kpi_widget and isinstance(content.get("valueMap"), list):
                        # Ensure minimum KpiCard fields exist for top-level KPI entries.
                        for item in content["valueMap"]:
                            if not isinstance(item, dict) or not isinstance(item.get("valueMap"), list):
                                continue
                            item_entries = item["valueMap"]
                            by_key = {
                                str(entry.get("key", "")).strip(): entry
                                for entry in item_entries
                                if isinstance(entry, dict) and str(entry.get("key", "")).strip()
                            }
                            if "label" not in by_key:
                                item_entries.append({"key": "label", "valueString": "KPI"})
                            if "value" not in by_key:
                                item_entries.append({"key": "value", "valueNumber": 0})

                    normalized_contents.append(content)

                data_update["contents"] = normalized_contents
                normalized_messages.append(message)
                continue

            normalized_messages.append(message)

        output.surface_messages = normalized_messages
        if not output.warnings:
            output.warnings = []
        return self._ensure_required_payload(
            output=output,
            widgets=widgets,
            target_component_ids=target_component_ids,
            target_data_keys=target_data_keys,
            context_text=context_text,
        )

    @staticmethod
    def _humanize_key(data_key: str) -> str:
        tokens = []
        current = []
        for ch in data_key:
            if ch in "_-":
                if current:
                    tokens.append("".join(current))
                    current = []
            elif ch.isupper() and current:
                tokens.append("".join(current))
                current = [ch.lower()]
            else:
                current.append(ch)
        if current:
            tokens.append("".join(current))
        return " ".join(token.capitalize() for token in tokens if token) or data_key

    @staticmethod
    def _extract_first_number(context_text: str, fallback: float = 0) -> float:
        import re

        if not context_text:
            return fallback
        match = re.search(r"(-?\d+(?:\.\d+)?)", context_text.replace(",", ""))
        if not match:
            return fallback
        try:
            return float(match.group(1))
        except ValueError:
            return fallback

    def _build_fallback_content_for_key(
        self,
        data_key: str,
        widgets: list[str],
        context_text: str,
    ) -> dict[str, Any]:
        has_kpi_widget = any(widget == "KpiCard" for widget in widgets)
        has_map_widget = any(widget == "MapComponent" for widget in widgets)

        key_lower = data_key.lower()
        if has_kpi_widget or "kpi" in key_lower or "count" in key_lower or "total" in key_lower:
            value = self._extract_first_number(context_text, fallback=0)
            return {
                "key": data_key,
                "valueMap": [
                    {"key": "label", "valueString": self._humanize_key(data_key)},
                    {"key": "value", "valueNumber": int(value) if value.is_integer() else value},
                    {"key": "unit", "valueString": "customers" if "customer" in key_lower else ""},
                    {"key": "icon", "valueString": "users" if "customer" in key_lower else "chart-line"},
                    {"key": "change", "valueNumber": 0},
                    {"key": "changeLabel", "valueString": "latest snapshot"},
                ],
            }

        if has_map_widget or "map" in key_lower or "location" in key_lower:
            return {
                "key": data_key,
                "valueMap": [
                    {
                        "key": "0",
                        "valueMap": [
                            {"key": "name", "valueString": "Circuit 101 - East Substation"},
                            {"key": "latitude", "valueNumber": 40.7128},
                            {"key": "longitude", "valueNumber": -74.0060},
                            {"key": "description", "valueString": "Priority response zone"},
                            {"key": "status", "valueString": "Investigating"},
                        ],
                    }
                ],
            }

        return {
            "key": data_key,
            "valueMap": [
                {"key": "label", "valueString": self._humanize_key(data_key)},
                {"key": "value", "valueString": "Data pending"},
            ],
        }

    def _build_widget_fallback_content(
        self,
        widget_type: str,
        data_key: str,
        context_text: str,
    ) -> dict[str, Any]:
        if widget_type == "KpiCard":
            return self._build_fallback_content_for_key(data_key, ["KpiCard"], context_text)

        if widget_type == "MapComponent":
            return self._build_fallback_content_for_key(data_key, ["MapComponent"], context_text)

        if widget_type == "BarGraph":
            if "label" in data_key.lower():
                return {
                    "key": data_key,
                    "valueMap": [
                        {"key": "0", "valueString": "A"},
                        {"key": "1", "valueString": "B"},
                        {"key": "2", "valueString": "C"},
                    ],
                }
            if "detail" in data_key.lower():
                return {
                    "key": data_key,
                    "valueMap": [
                        {"key": "0", "valueMap": [{"key": "note", "valueString": "Auto-generated detail"}]},
                        {"key": "1", "valueMap": [{"key": "note", "valueString": "Auto-generated detail"}]},
                    ],
                }
            return {
                "key": data_key,
                "valueMap": [
                    {"key": "0", "valueNumber": 10},
                    {"key": "1", "valueNumber": 20},
                    {"key": "2", "valueNumber": 15},
                ],
            }

        if widget_type == "LineGraph":
            if "label" in data_key.lower():
                return {
                    "key": data_key,
                    "valueMap": [
                        {"key": "0", "valueString": "Jan"},
                        {"key": "1", "valueString": "Feb"},
                        {"key": "2", "valueString": "Mar"},
                    ],
                }
            if "series" in data_key.lower():
                return {
                    "key": data_key,
                    "valueMap": [
                        {
                            "key": "0",
                            "valueMap": [
                                {"key": "name", "valueString": "Series A"},
                                {"key": "color", "valueString": "#00D4FF"},
                                {
                                    "key": "values",
                                    "valueMap": [
                                        {"key": "0", "valueNumber": 12},
                                        {"key": "1", "valueNumber": 18},
                                        {"key": "2", "valueNumber": 14},
                                    ],
                                },
                            ],
                        }
                    ],
                }
            return {
                "key": data_key,
                "valueMap": [
                    {"key": "0", "valueMap": [{"key": "note", "valueString": "Auto-generated line detail"}]},
                ],
            }

        if widget_type == "Table":
            return {
                "key": data_key,
                "valueMap": [
                    {
                        "key": "0",
                        "valueMap": [
                            {"key": "id", "valueString": "1"},
                            {"key": "name", "valueString": "Item A"},
                            {"key": "value", "valueNumber": 10},
                            {"key": "status", "valueString": "Active"},
                        ],
                    }
                ],
            }

        if widget_type == "TimelineComponent":
            if "detail" in data_key.lower():
                return {
                    "key": data_key,
                    "valueMap": [
                        {
                            "key": "0",
                            "valueMap": [
                                {"key": "owner", "valueString": "Operations"},
                                {"key": "impact", "valueString": "Auto-generated timeline detail"},
                            ],
                        }
                    ],
                }
            return {
                "key": data_key,
                "valueMap": [
                    {
                        "key": "0",
                        "valueMap": [
                            {"key": "date", "valueString": "2026-01-01"},
                            {"key": "title", "valueString": "Event"},
                            {"key": "description", "valueString": "Auto-generated timeline event"},
                            {"key": "category", "valueString": "General"},
                        ],
                    }
                ],
            }

        return self._build_fallback_content_for_key(data_key, [], context_text)

    def _is_valid_widget_content(self, widget_type: str, content_entry: dict[str, Any]) -> bool:
        value_map = content_entry.get("valueMap")
        if not isinstance(value_map, list):
            return False

        if widget_type == "KpiCard":
            keys = {str(entry.get("key", "")) for entry in value_map if isinstance(entry, dict)}
            if {"label", "value"}.issubset(keys):
                return True
            # Alternate KPI shape: nested object under first index.
            if value_map and isinstance(value_map[0], dict) and isinstance(value_map[0].get("valueMap"), list):
                nested_keys = {
                    str(entry.get("key", ""))
                    for entry in value_map[0]["valueMap"]
                    if isinstance(entry, dict)
                }
                return {"label", "value"}.issubset(nested_keys)
            return False

        if widget_type == "MapComponent":
            if not value_map:
                return False
            first = value_map[0] if isinstance(value_map[0], dict) else {}
            marker_map = first.get("valueMap")
            if not isinstance(marker_map, list):
                return False
            marker_keys = {str(entry.get("key", "")) for entry in marker_map if isinstance(entry, dict)}
            return "name" in marker_keys and ("latitude" in marker_keys or "lat" in marker_keys) and ("longitude" in marker_keys or "lng" in marker_keys)

        if widget_type == "BarGraph":
            if not value_map:
                return False
            first = value_map[0] if isinstance(value_map[0], dict) else {}
            return "valueNumber" in first or isinstance(first.get("valueMap"), list)

        if widget_type == "LineGraph":
            if not value_map:
                return False
            if "series" in str(content_entry.get("key", "")).lower():
                first = value_map[0] if isinstance(value_map[0], dict) else {}
                series_map = first.get("valueMap")
                if not isinstance(series_map, list):
                    return False
                series_keys = {str(entry.get("key", "")) for entry in series_map if isinstance(entry, dict)}
                return "name" in series_keys and "values" in series_keys
            return True

        if widget_type in {"Table", "TimelineComponent"}:
            if not value_map:
                return False
            first = value_map[0] if isinstance(value_map[0], dict) else {}
            return isinstance(first.get("valueMap"), list)

        return True

    def _ensure_table_component_contract(self, component_entry: dict[str, Any]) -> None:
        props = self._extract_component_props(component_entry)
        if self._extract_component_type(component_entry) != "Table":
            return
        columns = props.get("columns")
        if isinstance(columns, list) and columns:
            return
        props["columns"] = [
            {"header": "ID", "field": "id", "type": "string"},
            {"header": "Name", "field": "name", "type": "string"},
            {"header": "Value", "field": "value", "type": "number"},
        ]

    def _ensure_widget_contracts(
        self,
        output: WidgetWorkerOutput,
        widgets: list[str],
        context_text: str,
    ) -> WidgetWorkerOutput:
        # Aggregate and index all data contents across messages.
        data_contents: list[dict[str, Any]] = []
        component_entries: list[dict[str, Any]] = []
        for message in output.surface_messages:
            if not isinstance(message, dict):
                continue
            surface_update = message.get("surfaceUpdate")
            if isinstance(surface_update, dict) and isinstance(surface_update.get("components"), list):
                component_entries.extend([c for c in surface_update["components"] if isinstance(c, dict)])
            data_update = message.get("dataModelUpdate")
            if isinstance(data_update, dict) and isinstance(data_update.get("contents"), list):
                data_contents.extend([c for c in data_update["contents"] if isinstance(c, dict)])

        data_index = {
            str(entry.get("key", "")): entry
            for entry in data_contents
            if isinstance(entry.get("key"), str)
        }

        missing_or_repaired: list[str] = []
        for component in component_entries:
            widget_type = self._extract_component_type(component)
            if widget_type not in set(widgets):
                continue

            if widget_type == "Table":
                self._ensure_table_component_contract(component)

            props = self._extract_component_props(component)
            path_props = []
            for prop_name in ("dataPath", "labelPath", "seriesPath", "detailsPath"):
                prop_value = props.get(prop_name)
                if isinstance(prop_value, str) and prop_value.strip():
                    path_props.append((prop_name, prop_value))

            for _, raw_path in path_props:
                segments = self._path_to_segments(raw_path)
                if not segments:
                    continue
                root_key = segments[0]

                existing = data_index.get(root_key)
                if existing is None or not self._is_valid_widget_content(widget_type, existing):
                    data_index[root_key] = self._build_widget_fallback_content(widget_type, root_key, context_text)
                    missing_or_repaired.append(f"{widget_type}:{root_key}")

        if missing_or_repaired:
            output.warnings.append(
                "widget_contract_filled_or_repaired:" + ",".join(sorted(set(missing_or_repaired)))
            )
            # Replace dataModelUpdate contents with the repaired index where keys overlap.
            for message in output.surface_messages:
                data_update = message.get("dataModelUpdate") if isinstance(message, dict) else None
                if not isinstance(data_update, dict):
                    continue
                contents = data_update.get("contents")
                if not isinstance(contents, list):
                    continue
                rebuilt: list[dict[str, Any]] = []
                seen: set[str] = set()
                for entry in contents:
                    key = str(entry.get("key", "")) if isinstance(entry, dict) else ""
                    if key and key in data_index:
                        rebuilt.append(data_index[key])
                        seen.add(key)
                    elif isinstance(entry, dict):
                        rebuilt.append(entry)
                # Add any repaired keys not previously present in this message.
                for key, entry in data_index.items():
                    if key not in seen and all(not (isinstance(e, dict) and e.get("key") == key) for e in rebuilt):
                        rebuilt.append(entry)
                data_update["contents"] = rebuilt

        return output

    def _ensure_required_payload(
        self,
        output: WidgetWorkerOutput,
        widgets: list[str],
        target_component_ids: list[str],
        target_data_keys: list[str],
        context_text: str,
    ) -> WidgetWorkerOutput:
        present_component_ids: set[str] = set()
        present_data_keys: set[str] = set()
        surface_id = "dashboard"

        for message in output.surface_messages:
            if not isinstance(message, dict):
                continue

            surface_update = message.get("surfaceUpdate")
            if isinstance(surface_update, dict):
                surface_id = str(surface_update.get("surfaceId", surface_id) or surface_id)
                components = surface_update.get("components", [])
                if isinstance(components, list):
                    for component in components:
                        if isinstance(component, dict) and isinstance(component.get("id"), str):
                            present_component_ids.add(component["id"])

            data_update = message.get("dataModelUpdate")
            if isinstance(data_update, dict):
                surface_id = str(data_update.get("surfaceId", surface_id) or surface_id)
                contents = data_update.get("contents", [])
                if isinstance(contents, list):
                    for content in contents:
                        if isinstance(content, dict) and isinstance(content.get("key"), str):
                            present_data_keys.add(content["key"])

        missing_component_ids = [
            component_id for component_id in target_component_ids
            if component_id not in present_component_ids
        ]
        missing_data_keys = [
            data_key for data_key in target_data_keys
            if data_key not in present_data_keys
        ]

        if missing_component_ids:
            output.warnings.append(f"missing_component_ids_filled:{','.join(missing_component_ids)}")
            fallback_components = []
            for component_id in missing_component_ids:
                fallback_components.append(
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
            output.surface_messages.append(
                {
                    "surfaceUpdate": {
                        "surfaceId": surface_id,
                        "components": fallback_components,
                    }
                }
            )

        if missing_data_keys:
            output.warnings.append(f"missing_data_keys_filled:{','.join(missing_data_keys)}")
            generated_contents = [
                self._build_fallback_content_for_key(data_key, widgets, context_text)
                for data_key in missing_data_keys
            ]
            output.surface_messages.append(
                {
                    "dataModelUpdate": {
                        "surfaceId": surface_id,
                        "path": "/",
                        "contents": generated_contents,
                    }
                }
            )

        return self._ensure_widget_contracts(
            output=output,
            widgets=widgets,
            context_text=context_text,
        )

    async def run_package(
        self,
        state: DynamicGraphState,
        package_id: str,
        widgets: list[str],
        target_component_ids: list[str],
        target_data_keys: list[str],
    ) -> WidgetWorkerOutput:
        """Run this worker for one package and return structured fragment output."""
        get_custom_component_catalog, get_custom_component_example = create_custom_component_tools(
            self.inline_catalog,
            allowed_components=widgets,
        )
        system_prompt = get_ui_parallel_widget_worker_instructions(
            package_id=package_id,
            widgets=widgets,
            target_component_ids=target_component_ids,
            target_data_keys=target_data_keys,
        )
        
        self.system_prompt=system_prompt
        self.tools = [
            get_custom_component_catalog,
            get_custom_component_example,
            get_native_component_catalog,
            get_native_component_example
        ]
        self.agent_name=f"widget_worker_{package_id}"
        agent = self.build_agent()

        # Use a dedicated user instruction so workers remain deterministic and independent.
        worker_request = HumanMessage(
            content=(
                f"Generate A2UI fragment for package '{package_id}'. "
                "Return only package-scoped messages. "
                "Use parallel tool calls: batch independent tool calls in the same assistant turn, "
                "avoid repeated calls with identical args, and keep tool rounds minimal."
            )
        )
        worker_state = {
            "messages": [*state["messages"], worker_request],
            "suggestions": state.get("suggestions", ""),
        }
        context_text = "\n".join(str(getattr(msg, "content", "")) for msg in state.get("messages", []))

        response = await agent.ainvoke(worker_state)
        structured = response["structured_response"]
        return self._normalize_worker_output(
            output=structured,
            widgets=widgets,
            target_component_ids=target_component_ids,
            target_data_keys=target_data_keys,
            context_text=context_text,
        )

    async def __call__(self, state: DynamicGraphState):
        """Compatibility call: expects package payload in latest message content."""
        latest_content = str(state["messages"][-1].content)
        package = json.loads(latest_content)
        output = await self.run_package(
            state=state,
            package_id=package["package_id"],
            widgets=package.get("widgets", []),
            target_component_ids=package.get("target_component_ids", []),
            target_data_keys=package.get("target_data_keys", []),
        )
        return {
            "messages": state["messages"] + [
                AIMessage(content=output.model_dump_json(), name=self.agent_name)
            ]
        }
