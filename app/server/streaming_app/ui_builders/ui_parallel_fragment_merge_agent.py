"""Deterministic merger for parallel UI fragments."""
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class WorkerFragment:
    """Normalized worker fragment for merge stage."""
    package_id: str
    surface_messages: list[dict[str, Any]]
    estimated_complexity: str
    priority: int


class UIParallelFragmentMergeAgent:
    """
    Merge shell + worker fragments into ordered progressive messages.

    This merger is intentionally deterministic to keep token cost low and
    avoid post-generation drift.
    """

    complexity_rank = {"low": 0, "medium": 1, "high": 2}

    def _sort_fragments(self, fragments: list[WorkerFragment]) -> list[WorkerFragment]:
        return sorted(
            fragments,
            key=lambda f: (f.priority, self.complexity_rank.get(f.estimated_complexity, 1), f.package_id),
        )

    @staticmethod
    def _split_component_and_data(messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        component_messages: list[dict[str, Any]] = []
        data_messages: list[dict[str, Any]] = []
        for message in messages:
            if "surfaceUpdate" in message:
                component_messages.append(message)
            elif "dataModelUpdate" in message:
                data_messages.append(message)
        return component_messages, data_messages

    @staticmethod
    def _encode_value_entry(key: str, value: Any) -> dict[str, Any]:
        if isinstance(value, bool):
            return {"key": key, "valueBoolean": value}
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return {"key": key, "valueNumber": value}
        if isinstance(value, str):
            return {"key": key, "valueString": value}
        if isinstance(value, dict):
            return {
                "key": key,
                "valueMap": [
                    UIParallelFragmentMergeAgent._encode_value_entry(str(k), v)
                    for k, v in value.items()
                ],
            }
        if isinstance(value, list):
            return {
                "key": key,
                "valueMap": [
                    UIParallelFragmentMergeAgent._encode_value_entry(str(index), item)
                    for index, item in enumerate(value)
                ],
            }
        if value is None:
            return {"key": key, "valueString": ""}
        return {"key": key, "valueString": str(value)}

    @staticmethod
    def _normalize_data_model_update(message: dict[str, Any], default_surface_id: str) -> dict[str, Any]:
        update = message.get("dataModelUpdate")
        if not isinstance(update, dict):
            return message

        update.setdefault("surfaceId", default_surface_id)
        update.setdefault("path", "/")

        if isinstance(update.get("contents"), list):
            return message

        raw_data = update.get("data")
        if isinstance(raw_data, dict):
            update["contents"] = [
                UIParallelFragmentMergeAgent._encode_value_entry(str(key), value)
                for key, value in raw_data.items()
            ]
            update.pop("data", None)
        elif isinstance(raw_data, list):
            update["contents"] = [
                UIParallelFragmentMergeAgent._encode_value_entry(str(index), value)
                for index, value in enumerate(raw_data)
            ]
            update.pop("data", None)
        else:
            update["contents"] = []
        return message

    @staticmethod
    def _normalize_shell_message(message: dict[str, Any], default_surface_id: str) -> dict[str, Any]:
        begin = message.get("beginRendering")
        if isinstance(begin, dict):
            begin.setdefault("surfaceId", default_surface_id)
        surface_update = message.get("surfaceUpdate")
        if isinstance(surface_update, dict):
            surface_update.setdefault("surfaceId", default_surface_id)
            surface_update.setdefault("components", [])
        return message

    @staticmethod
    def _resolve_default_surface_id(shell_messages: list[dict[str, Any]]) -> str:
        for message in shell_messages:
            begin = message.get("beginRendering")
            if isinstance(begin, dict) and isinstance(begin.get("surfaceId"), str):
                return begin["surfaceId"]
            update = message.get("surfaceUpdate")
            if isinstance(update, dict) and isinstance(update.get("surfaceId"), str):
                return update["surfaceId"]
        return "dashboard"

    def merge(
        self,
        shell_messages: list[dict[str, Any]],
        worker_fragments: list[WorkerFragment],
    ) -> dict[str, Any]:
        default_surface_id = self._resolve_default_surface_id(shell_messages)
        shell_messages = [
            self._normalize_shell_message(message, default_surface_id)
            for message in shell_messages
            if isinstance(message, dict)
        ]
        for fragment in worker_fragments:
            fragment.surface_messages = [
                self._normalize_data_model_update(message, default_surface_id)
                for message in fragment.surface_messages
                if isinstance(message, dict)
            ]

        ordered_messages: list[dict[str, Any]] = []
        step_map: list[dict[str, Any]] = []

        # Shell always first.
        for message in shell_messages:
            ordered_messages.append(message)
            step_map.append({"step": len(ordered_messages), "source": "shell"})

        # Worker package order by priority and expected complexity.
        for fragment in self._sort_fragments(worker_fragments):
            component_messages, data_messages = self._split_component_and_data(fragment.surface_messages)

            for message in component_messages:
                ordered_messages.append(message)
                step_map.append({"step": len(ordered_messages), "source": fragment.package_id, "kind": "component"})

            for message in data_messages:
                ordered_messages.append(message)
                step_map.append({"step": len(ordered_messages), "source": fragment.package_id, "kind": "data"})

        return {
            "ordered_messages": ordered_messages,
            "step_map": step_map,
            "warnings": [],
        }

    @staticmethod
    def parse_worker_fragment(raw_payload: str, priority: int) -> WorkerFragment:
        data = json.loads(raw_payload)
        return WorkerFragment(
            package_id=str(data.get("package_id", "unknown")),
            surface_messages=data.get("surface_messages", []),
            estimated_complexity=str(data.get("estimated_complexity", "medium")).lower(),
            priority=priority,
        )
