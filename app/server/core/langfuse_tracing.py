import os
import logging
from contextvars import ContextVar, Token
from typing import Any

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

_LANGFUSE_SESSION_ID: ContextVar[str | None] = ContextVar(
    "langfuse_session_id",
    default=None,
)
_LANGFUSE_CLIENT: ContextVar[Langfuse | None] = ContextVar(
    "langfuse_client",
    default=None,
)
_LANGFUSE_TRACE_ID: ContextVar[str | None] = ContextVar(
    "langfuse_trace_id",
    default=None,
)
logger = logging.getLogger(__name__)


def _normalize_usage_payload(value: Any) -> Any:
    """Recursively normalize usage payload values so math ops are always safe."""
    if value is None:
        return 0
    if isinstance(value, dict):
        return {k: _normalize_usage_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_usage_payload(item) for item in value]
    return value


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def extract_total_tokens_from_message(message: Any) -> int:
    """Extract total tokens from common metadata formats used by providers."""
    usage_metadata = getattr(message, "usage_metadata", None) or {}
    if isinstance(usage_metadata, dict):
        total = _safe_int(usage_metadata.get("total_tokens"))
        if total > 0:
            return total

    response_metadata = getattr(message, "response_metadata", None) or {}
    if isinstance(response_metadata, dict):
        total = _safe_int(response_metadata.get("total_tokens"))
        if total > 0:
            return total

        usage = response_metadata.get("usage", {})
        if isinstance(usage, dict):
            total = _safe_int(usage.get("total_tokens"))
            if total > 0:
                return total

        token_usage = response_metadata.get("token_usage", {})
        if isinstance(token_usage, dict):
            total = _safe_int(token_usage.get("total_tokens"))
            if total > 0:
                return total

    return 0


def extract_total_tokens_from_response(response: dict[str, Any]) -> int:
    """Extract total tokens from the latest message of a LangChain response."""
    try:
        latest_message = response["messages"][-1]
    except (KeyError, IndexError, TypeError):
        return 0

    return extract_total_tokens_from_message(latest_message)


class SafeLangfuseCallbackHandler(CallbackHandler):
    """Langfuse handler that sanitizes usage payloads before parsing."""

    def _sanitize_response_usage(self, response: Any) -> None:
        if getattr(response, "llm_output", None):
            llm_output = response.llm_output
            for key in ("token_usage", "usage"):
                if key in llm_output and llm_output[key] is not None:
                    llm_output[key] = _normalize_usage_payload(llm_output[key])

        for generation in getattr(response, "generations", []) or []:
            for chunk in generation:
                generation_info = getattr(chunk, "generation_info", None)
                if (
                    isinstance(generation_info, dict)
                    and "usage_metadata" in generation_info
                    and generation_info["usage_metadata"] is not None
                ):
                    generation_info["usage_metadata"] = _normalize_usage_payload(
                        generation_info["usage_metadata"]
                    )

                message = getattr(chunk, "message", None)
                response_metadata = getattr(message, "response_metadata", None)

                if isinstance(response_metadata, dict):
                    if "usage" in response_metadata and response_metadata["usage"] is not None:
                        response_metadata["usage"] = _normalize_usage_payload(
                            response_metadata["usage"]
                        )
                    if (
                        "amazon-bedrock-invocationMetrics" in response_metadata
                        and response_metadata["amazon-bedrock-invocationMetrics"] is not None
                    ):
                        response_metadata["amazon-bedrock-invocationMetrics"] = _normalize_usage_payload(
                            response_metadata["amazon-bedrock-invocationMetrics"]
                        )

                usage_metadata = getattr(message, "usage_metadata", None)
                if usage_metadata is not None:
                    normalized_usage_metadata = _normalize_usage_payload(usage_metadata)
                    try:
                        setattr(message, "usage_metadata", normalized_usage_metadata)
                    except Exception:
                        pass

    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kwargs):
        self._sanitize_response_usage(response)
        return super().on_llm_end(
            response,
            run_id=run_id,
            parent_run_id=parent_run_id,
            **kwargs,
        )


class LangfuseTracingProvider:
    def __init__(self, langfuse_client: Langfuse | None = None):
        self.langfuse_instance = langfuse_client or Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
        )

    def set_current_session_id(self, session_id: str) -> Token:
        return _LANGFUSE_SESSION_ID.set(session_id)

    def reset_current_session_id(self, token: Token) -> None:
        try:
            _LANGFUSE_SESSION_ID.reset(token)
        except ValueError:
            # Async generators can be finalized in a different context.
            logger.debug(
                "Skipping session_id token reset across context boundary; clearing current context value instead."
            )
            _LANGFUSE_SESSION_ID.set(None)

    def get_current_session_id(self) -> str | None:
        return _LANGFUSE_SESSION_ID.get()

    def set_current_trace_id(self, trace_id: str) -> Token:
        return _LANGFUSE_TRACE_ID.set(trace_id)

    def reset_current_trace_id(self, token: Token) -> None:
        try:
            _LANGFUSE_TRACE_ID.reset(token)
        except ValueError:
            logger.debug(
                "Skipping trace_id token reset across context boundary; clearing current context value instead."
            )
            _LANGFUSE_TRACE_ID.set(None)

    def get_current_trace_context(self) -> dict[str, str] | None:
        trace_id = _LANGFUSE_TRACE_ID.get()
        if trace_id:
            return {"trace_id": trace_id}

        current_observation_id = self.langfuse_instance.get_current_observation_id()
        if not current_observation_id:
            return None

        current_trace_id = self.langfuse_instance.get_current_trace_id()
        if not current_trace_id:
            return None

        return {"trace_id": current_trace_id}

    def set_current_client(self, langfuse_client: Langfuse) -> Token:
        return _LANGFUSE_CLIENT.set(langfuse_client)

    def reset_current_client(self, token: Token) -> None:
        try:
            _LANGFUSE_CLIENT.reset(token)
        except ValueError:
            # Async generators can be finalized in a different context.
            logger.debug(
                "Skipping langfuse_client token reset across context boundary; clearing current context value instead."
            )
            _LANGFUSE_CLIENT.set(None)

    def get_current_client(self) -> Langfuse:
        return _LANGFUSE_CLIENT.get() or self.langfuse_instance

    def get_trace_handler(self, trace_context: dict[str, str] | None = None):
        if trace_context is None:
            return SafeLangfuseCallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            )
        return SafeLangfuseCallbackHandler(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            trace_context=trace_context,
        )

    def build_observation_metadata(
        self,
        *,
        session_id: str,
        tags: list[str] | None = None,
        user_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {"session_id": session_id}
        if tags:
            metadata["tags"] = tags
        if user_id:
            metadata["user_id"] = user_id
        if extra:
            metadata.update(extra)
        return metadata

    def build_runnable_config(
        self,
        *,
        run_id: str,
        session_id: str,
        thread_id: str | None = None,
        user_id: str | None = None,
        tags: list[str] | None = None,
        extra_metadata: dict[str, Any] | None = None,
        trace_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {"langfuse_session_id": session_id}
        if user_id:
            metadata["langfuse_user_id"] = user_id
        if tags:
            metadata["langfuse_tags"] = tags
        if extra_metadata:
            metadata.update(extra_metadata)

        return {
            "run_id": run_id,
            "configurable": {"thread_id": thread_id or session_id},
            "callbacks": [self.get_trace_handler(trace_context=trace_context)],
            "metadata": metadata,
        }
