import os
import re
import json
import uuid
from collections.abc import AsyncIterable
from typing import Any
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langfuse import Langfuse, propagate_attributes

from core.chat_app.prompts import MAIN_LLM_INSTRUCTIONS
from core.langfuse_tracing import (
    LangfuseTracingProvider,
    extract_total_tokens_from_message,
)
from core.common_struct import SuggestionModel
from core.common_struct import SuggestedQuestions
from core.common_struct import SUGGESTION_QUERY
from core.gen_ai_provider import GenAIProvider
from chat_app.rag_tool import semantic_search
from chat_app.nl2sql_agent import call_SQL_DB

SOURCE_PATTERN = re.compile(r"\(Source:\s*([^)]+)\)")


#region Utilities
def extract_RAG_sources(semantic_result: str) -> list[str]:
    """Extract unique document names from semantic search tool output."""
    if not semantic_result:
        return []

    documents: list[str] = []
    seen: set[str] = set()

    for source in SOURCE_PATTERN.findall(semantic_result):
        filename = source.strip().replace("\\", "/").split("/")[-1]
        match = re.match(r"(.+?\.[A-Za-z0-9]+)(?:_start_\d+)?$", filename)
        doc_name = match.group(1) if match else filename

        if doc_name and doc_name not in seen:
            seen.add(doc_name)
            documents.append(doc_name)

    return documents

#endregion


#region Main Agent
class OCIOutageEnergyLLM:
    """LLM agent that handles outage and energy requests."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream", "application/json+a2ui"]

    #region Setup
    def __init__(self, langfuse_client: Langfuse):
        self._agent = self._build_agent()
        self._user_id = os.getenv("LANGFUSE_USER_ID")
        self._suggestion_out = SuggestionModel().build_suggestion_model()
        self._out_query = SUGGESTION_QUERY
        self.langfuse_client: Langfuse = langfuse_client
        self.langfuse_tracing_provider = LangfuseTracingProvider(langfuse_client=langfuse_client)

    def _build_agent(self) -> CompiledStateGraph:
        """Builds the LLM agent for the outage and energy agent."""
        oci_llm = GenAIProvider().build_oci_client(model_kwargs={"temperature":0.7})

        return create_agent(
            model=oci_llm,
            tools=[semantic_search, call_SQL_DB],
            system_prompt=MAIN_LLM_INSTRUCTIONS,
            name="outage_energy_llm",
            checkpointer= InMemorySaver()
        )

    async def _generate_suggestions(self, final_response_content: str | None) -> SuggestedQuestions:
        """Generate follow-up suggestions with a simple fallback for empty results."""
        suggestions = await self._suggestion_out.ainvoke(
            self._out_query + f"\n\nContext for question generation:\n{final_response_content}"
        )
        if not suggestions:
            suggestions = SuggestedQuestions(
                suggested_questions=[
                    "Tell me more details about first data",
                    "Make a summary of data given",
                ]
            )
        return suggestions
    #endregion
    
    #region Streaming
    async def oci_stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        """Call the agent and stream intermediate and final responses."""

        current_message = {"messages":[HumanMessage(query)]}
        request_id = uuid.uuid4().hex
        stable_session_id = str(session_id) if session_id else request_id

        final_response_content = None
        final_model_state = None
        model_token_count = 0
        source_documents: list[str] = []
        processed_messages = 0
        intermediate_updates: list[dict[str, Any]] = []

        with self.langfuse_client.start_as_current_observation(
            as_type="span",
            name="OutageEnergyLLM -> Agent Stream",
            input={"query": query},
            metadata=self.langfuse_tracing_provider.build_observation_metadata(
                session_id=stable_session_id,
                user_id=self._user_id,
                tags=["main_llm", "a2a"],
                extra={"request_id": request_id},
            ),
        ) as root_observation:
            session_token = self.langfuse_tracing_provider.set_current_session_id(stable_session_id)
            client_token = self.langfuse_tracing_provider.set_current_client(self.langfuse_client)

            config:RunnableConfig = self.langfuse_tracing_provider.build_runnable_config(
                run_id=request_id,
                session_id=stable_session_id,
                thread_id=stable_session_id,
                user_id=self._user_id,
                tags=["main_llm", "a2a"],
                extra_metadata={"request_id": request_id},
            )

            try:
                with propagate_attributes(
                    session_id=stable_session_id,
                    user_id=self._user_id,
                    tags=["main_llm", "a2a"],
                ):
                    async for event in self._agent.astream(
                        input=current_message,
                        stream_mode="values",
                        config=config
                    ):
                        messages = event.get("messages", [])
                        new_messages = messages[processed_messages:]
                        processed_messages = len(messages)

                        for latest_update in new_messages:
                            if isinstance(latest_update, AIMessage):
                                final_response_content = latest_update.content

                            if hasattr(latest_update, 'tool_calls') and latest_update.tool_calls:
                                if len(latest_update.tool_calls) == 1:
                                    tool_name = str(latest_update.tool_calls[0].get('name', ''))
                                    tool_args = str(latest_update.tool_calls[0].get('args', ''))
                                    update_text = f"Model calling tool: {tool_name} with args {tool_args}"
                                    intermediate_updates.append(
                                        {"type": "tool_call", "tool_name": tool_name, "args": tool_args}
                                    )
                                else:
                                    tool_names = [str(tc.get('name', '')) for tc in latest_update.tool_calls]
                                    update_text = f"Model called tools: {', '.join(tool_names)}"
                                    intermediate_updates.append(
                                        {"type": "tool_call_batch", "tools": tool_names}
                                    )
                            elif isinstance(latest_update, ToolMessage):
                                tool_name = str(latest_update.name)
                                status_content = str(latest_update.content)
                                update_text = f"Tool {tool_name} responded with:\n{status_content[:100]}...\n\nInformation passed to agent to build response"
                                intermediate_updates.append(
                                    {"type": "tool_result", "tool_name": tool_name, "preview": status_content[:300]}
                                )
                                if tool_name == "semantic_search":
                                    for document_name in extract_RAG_sources(status_content):
                                        if document_name not in source_documents:
                                            source_documents.append(document_name)
                            elif isinstance(latest_update, AIMessage):
                                status_content = str(latest_update.content)
                                model_id = str(latest_update.response_metadata.get("model_id", ""))
                                total_tokens_on_call = extract_total_tokens_from_message(latest_update)
                                model_token_count += total_tokens_on_call
                                agent_name = str(latest_update.name)
                                model_data = f"""
                                    model_id: {model_id},
                                    agent_name: {agent_name},
                                    total_tokens_on_call: {str(total_tokens_on_call)},
                                    aggregated_total_tokens: {str(model_token_count)}
                                """
                                update_text = f"Model responded:\n{status_content[:100]}...\n\nModel metadata:\n{model_data}"
                                final_model_state = update_text
                                intermediate_updates.append(
                                    {
                                        "type": "ai_message",
                                        "preview": status_content[:300],
                                        "tokens_on_call": total_tokens_on_call,
                                        "aggregated_total_tokens": model_token_count,
                                    }
                                )
                            else:
                                status_content = str(getattr(latest_update, "content", ""))
                                update_text = f"Model processing:\n{status_content[:100]}..."
                                intermediate_updates.append(
                                    {"type": "processing", "preview": status_content[:300]}
                                )

                            yield {
                                "is_task_complete": False,
                                "updates": update_text,
                                # Expose raw content for progressive downstream parsing (e.g. A2UI deltas).
                                "content": str(getattr(latest_update, "content", "") or ""),
                            }

                root_observation.update(
                    output={
                        "session_id": stable_session_id,
                        "request_id": request_id,
                        "final_response": final_response_content,
                        "message_count": processed_messages,
                        "token_count": model_token_count,
                        "sources": source_documents,
                        "intermediate_updates": intermediate_updates,
                    }
                )
            finally:
                self.langfuse_tracing_provider.reset_current_client(client_token)
                self.langfuse_tracing_provider.reset_current_session_id(session_token)

        suggestions = await self._generate_suggestions(final_response_content)
        
        yield {
            "is_task_complete": True,
            "content": f"{final_response_content}",
            "final_state": f"{str(final_response_content)[:100]}\n{final_model_state}",
            "token_count": str(model_token_count),
            "suggestions": suggestions.model_dump_json(),
            "sources": json.dumps(source_documents)
        }
    #endregion
#endregion
