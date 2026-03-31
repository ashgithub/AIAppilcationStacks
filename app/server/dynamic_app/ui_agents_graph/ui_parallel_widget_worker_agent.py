"""Parallel UI widget worker node."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain.messages import HumanMessage

from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.parallel_ui_shared import (
    coerce_payload_generic,
    default_from_json_schema,
    extract_response_content,
    extract_structured_result,
    get_widget_model_registry,
    normalize_widget_name,
    parse_json_loose,
)
from core.dynamic_app.prompts import (
    UI_PARALLEL_WIDGET_INSTRUCTIONS,
    build_widget_structured_prompt,
)

MAX_WIDGET_GENERATION_ATTEMPTS = 2
MAX_RETRY_PAYLOAD_PREVIEW = 1200
logger = logging.getLogger(__name__)


class UIWidgetStructuredAgent(BaseAgent):
    """Single reusable widget agent with dynamic structured output binding."""

    def __init__(self):
        super().__init__()
        self.model = "xai.grok-4-fast-reasoning"
        self.agent_name = "ui_parallel_widget"
        self.system_prompt = UI_PARALLEL_WIDGET_INSTRUCTIONS
        self._model_registry = get_widget_model_registry()
        self._agent_registry: dict[str, Any] = {}
        self._freeform_agent = self.build_agent()

    def _build_minimal_widget_output(self, widget_name: str, model_cls: Any) -> Any:
        schema = model_cls.model_json_schema() if hasattr(model_cls, "model_json_schema") else {}
        seed_payload = default_from_json_schema(schema) or {}
        if isinstance(seed_payload, dict):
            if "title" in model_cls.model_fields and not seed_payload.get("title"):
                seed_payload["title"] = f"{widget_name} data"
        try:
            return model_cls.model_validate(seed_payload)
        except Exception:
            coerced = coerce_payload_generic(
                model_cls, seed_payload if isinstance(seed_payload, dict) else {}
            )
            try:
                return model_cls.model_validate(coerced)
            except Exception:
                return None

    def _build_retry_prompt(
        self,
        widget_name: str,
        data_context: str,
        previous_payload: str,
        previous_error: str,
    ) -> str:
        return (
            f"{build_widget_structured_prompt(widget_name, data_context)}\n\n"
            "Retry request: the previous response was invalid for the schema.\n"
            "Generate a corrected response.\n"
            f"Previous payload (possibly invalid):\n{previous_payload}\n\n"
            f"Validation/parsing error:\n{previous_error}\n\n"
            "Output must be only schema-valid JSON content."
        )

    def _validate_widget_output(
        self, model_cls: Any, candidate: Any
    ) -> tuple[Any | None, str | None]:
        if candidate is None:
            return None, "Candidate payload is empty."
        if isinstance(candidate, model_cls):
            return candidate, None
        try:
            validated = model_cls.model_validate(candidate)
            return validated, None
        except Exception as first_exc:
            if isinstance(candidate, dict):
                try:
                    coerced = coerce_payload_generic(model_cls, candidate)
                    validated = model_cls.model_validate(coerced)
                    return validated, None
                except Exception as second_exc:
                    return None, f"{first_exc}; after generic coercion: {second_exc}"
            return None, str(first_exc)

    async def _generate_widget_freeform(
        self,
        widget_name: str,
        model_cls: Any,
        data_context: str,
        previous_payload: str,
        previous_error: str,
    ) -> tuple[Any | None, str | None]:
        schema_keys = list((model_cls.model_json_schema() or {}).get("properties", {}).keys())
        strict_prompt = (
            "Return ONLY a valid JSON object for the requested widget schema.\n"
            "No markdown, no comments, no prose.\n"
            f"Widget: {widget_name}\n"
            f"Required top-level keys: {', '.join(schema_keys)}\n"
            f"Data context:\n{data_context}\n\n"
            "Correction context (previous invalid attempt):\n"
            f"Payload:\n{previous_payload}\n\n"
            f"Error:\n{previous_error}\n"
        )
        response = await self._freeform_agent.ainvoke(
            {"messages": [HumanMessage(content=strict_prompt)]}
        )
        raw = extract_response_content(response)
        payload = parse_json_loose(raw)
        if payload is None:
            return None, f"Freeform parse failed. Preview={str(raw)[:MAX_RETRY_PAYLOAD_PREVIEW]}"
        validated, error = self._validate_widget_output(model_cls, payload)
        return validated, error

    async def generate_widget(self, widget_name: str, data_context: str) -> Any:
        canonical_name = normalize_widget_name(widget_name)
        model_cls = self._model_registry.get(canonical_name)
        if model_cls is None:
            logger.warning("Widget skipped: unsupported widget_name=%s", widget_name)
            return None
        agent = self._agent_registry.get(canonical_name)
        if agent is None:
            agent = self.build_agent(response_format=model_cls)
            self._agent_registry[canonical_name] = agent
        last_payload_preview = "<empty>"
        last_error = "Unknown validation error."

        for attempt in range(1, MAX_WIDGET_GENERATION_ATTEMPTS + 1):
            if attempt == 1:
                prompt = build_widget_structured_prompt(canonical_name, data_context)
            else:
                prompt = self._build_retry_prompt(
                    canonical_name, data_context, last_payload_preview, last_error
                )
            try:
                #region agent invokation
                response = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
                structured = extract_structured_result(response, model_cls)
                if structured is not None:
                    logger.info(
                        "Widget success | widget=%s model=%s attempt=%s",
                        canonical_name,
                        model_cls.__name__,
                        attempt,
                    )
                    return structured

                raw = extract_response_content(response)
                candidate = parse_json_loose(raw) if isinstance(raw, str) else raw
                validated, validation_error = self._validate_widget_output(model_cls, candidate)
                if validated is not None:
                    logger.info(
                        "Widget success after loose parse | widget=%s model=%s attempt=%s",
                        canonical_name,
                        model_cls.__name__,
                        attempt,
                    )
                    return validated

                last_payload_preview = str(raw)[:MAX_RETRY_PAYLOAD_PREVIEW]
                last_error = validation_error or "Structured extraction failed."
                logger.warning(
                    "Widget attempt failed validation | widget=%s model=%s attempt=%s error=%s",
                    canonical_name,
                    model_cls.__name__,
                    attempt,
                    last_error,
                )
            except Exception as exc:
                last_error = str(exc)
                last_payload_preview = "<unavailable due to structured generation exception>"
                logger.warning(
                    "Widget structured generation exception | widget=%s model=%s attempt=%s error=%s",
                    canonical_name,
                    model_cls.__name__,
                    attempt,
                    exc,
                )

        recovered, recovery_error = await self._generate_widget_freeform(
            canonical_name,
            model_cls,
            data_context,
            previous_payload=last_payload_preview,
            previous_error=last_error,
        )
        if recovered is not None:
            logger.info(
                "Widget recovered via general post-retry check | widget=%s model=%s",
                canonical_name,
                model_cls.__name__,
            )
            return recovered

        logger.warning(
            "General post-retry check failed | widget=%s model=%s error=%s",
            canonical_name,
            model_cls.__name__,
            recovery_error,
        )
        logger.error(
            "Widget fallback exhausted; returning minimal payload | widget=%s model=%s",
            canonical_name,
            model_cls.__name__,
        )
        return self._build_minimal_widget_output(canonical_name, model_cls)


#region graph node
class UIParallelWidgetWorkerNode:
    """Graph node that generates all widget outputs in parallel."""

    def __init__(self):
        self.agent_name = "ui_parallel_widget_worker"
        self._widget = UIWidgetStructuredAgent()

    async def __call__(self, state: DynamicGraphState) -> DynamicGraphState:
        tasks = list(state.get("parallel_execution_tasks") or [])
        data_context = str(
            state.get("parallel_data_context")
            or (state["messages"][-1].content if state.get("messages") else "")
        )
        logger.info(
            "Widget worker start | task_count=%s widgets=%s",
            len(tasks),
            [task.get("widget_name") for task in tasks],
        )
        widget_outputs = await asyncio.gather(
            *[
                self._widget.generate_widget(str(task.get("widget_name", "")), data_context)
                for task in tasks
            ],
            return_exceptions=True,
        )

        serialized_outputs: list[dict[str, Any]] = []
        for task, widget_output in zip(tasks, widget_outputs):
            if isinstance(widget_output, Exception):
                logger.error(
                    "Widget generation raised exception | widget=%s slot=%s",
                    task.get("widget_name"),
                    task.get("slot_label"),
                    exc_info=(
                        type(widget_output),
                        widget_output,
                        widget_output.__traceback__,
                    ),
                )
                serialized_outputs.append(
                    {
                        "task_index": task.get("index"),
                        "widget_name": task.get("widget_name"),
                        "output_type": None,
                        "payload": None,
                        "error": str(widget_output),
                    }
                )
                continue

            if widget_output is None:
                logger.warning(
                    "Widget generation returned None | widget=%s slot=%s",
                    task.get("widget_name"),
                    task.get("slot_label"),
                )

            serialized_outputs.append(
                {
                    "task_index": task.get("index"),
                    "widget_name": task.get("widget_name"),
                    "output_type": (
                        widget_output.__class__.__name__ if widget_output is not None else None
                    ),
                    "payload": (
                        widget_output.model_dump()
                        if hasattr(widget_output, "model_dump")
                        else widget_output
                    ),
                    "error": None,
                }
            )
        return {"parallel_widget_outputs": serialized_outputs}
