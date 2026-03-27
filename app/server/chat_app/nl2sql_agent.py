import logging
import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langfuse import propagate_attributes

from database.connections import RAGDBConnection
from database.semantic_cache import SQLSemanticCache
from core.langfuse_tracing import (
    LangfuseTracingProvider,
    extract_total_tokens_from_response,
)
from core.base_agent import BaseAgent
from core.chat_app.prompts.sql_agent import SQL_SCHEMA_DESCRIPTION, SQL_FEW_SHOT_EXAMPLES

logger = logging.getLogger(__name__)


#region Agent Definition
class NL2SQLAgent(BaseAgent):
    """Agent for natural language to SQL translation and execution."""

    def __init__(self):
        super().__init__()
        self.agent_name = "nl2sql_agent"
        self.model="xai.grok-4-fast-reasoning"
        self.system_prompt = f"{SQL_SCHEMA_DESCRIPTION}\n\n" + "\n\n".join(
            f"Q: {ex['q']}\nSQL:\n{ex['sql']}" for ex in SQL_FEW_SHOT_EXAMPLES
        )
        self.agent = self.build_agent()
        self.langfuse_tracing_provider = LangfuseTracingProvider()
        self.semantic_cache = SQLSemanticCache()

    @staticmethod
    def _strip_code_fences(query_text: str) -> str:
        if not query_text.startswith("```"):
            return query_text
        lines = query_text.split("\n")
        return "\n".join(lines[1:-1] if lines and lines[-1] == "```" else lines[1:])

    @staticmethod
    def _format_query_rows(cols, rows) -> str:
        if not rows:
            return "Query executed successfully but returned no results."

        result_lines = []
        for row in rows:
            row_data = ", ".join(f"{col}: {val}" for col, val in zip(cols, row))
            result_lines.append(row_data)

        return "Query Results:\n" + "\n".join(result_lines)

    async def call_nl2sql_agent(self, input: dict) -> dict:
        """Process the input question by generating SQL and executing it."""
        question = input.get("input", "")
        original_question = question
        if not question:
            return {"output": "No question provided."}

        inherited_session_id = self.langfuse_tracing_provider.get_current_session_id()
        session_id = str(input.get("session_id") or inherited_session_id or uuid.uuid4().hex)
        langfuse_client = self.langfuse_tracing_provider.get_current_client()
        trace_context = self.langfuse_tracing_provider.get_current_trace_context()

        max_attempts = 2
        cache_top_k = 2
        cache_max_distance = 0.35
        generated_sql = ''
        last_error = None
        db_conn = RAGDBConnection()
        cache_status = "miss"

        with langfuse_client.start_as_current_observation(
            as_type="span",
            name="OutageEnergyLLM -> NL2SQL Agent",
            input={"question": question},
            metadata=self.langfuse_tracing_provider.build_observation_metadata(
                session_id=session_id,
                tags=["nl2sql"],
                extra={
                    "max_attempts": max_attempts,
                    "cache_top_k": cache_top_k,
                    "cache_max_distance": cache_max_distance,
                },
            ),
        ) as root_observation:
            try:
                with langfuse_client.start_as_current_observation(
                    as_type="span",
                    name="NL2SQL Semantic Cache Lookup",
                    input={"question": original_question},
                    metadata=self.langfuse_tracing_provider.build_observation_metadata(
                        session_id=session_id,
                        tags=["nl2sql", "cache_lookup"],
                        extra={"top_k": cache_top_k, "max_distance": cache_max_distance},
                    ),
                ) as cache_observation:
                    cached_matches = self.semantic_cache.search_similar_questions(
                        question=original_question,
                        top_k=cache_top_k,
                        max_distance=cache_max_distance,
                    )
                    cache_candidates = [
                        {"id": row["id"], "distance": row["distance"]}
                        for row in cached_matches
                    ]

                    if cached_matches:
                        cache_status = "hit"
                        best_match = cached_matches[0]
                        cached_sql = best_match["sql_query"]
                        with db_conn.get_connection() as conn:
                            cols, rows = db_conn.execute_query(conn, cached_sql)

                        formatted_output = self._format_query_rows(cols, rows)
                        cache_observation.update(
                            output={
                                "cache_status": cache_status,
                                "best_match_id": best_match["id"],
                                "best_distance": best_match["distance"],
                                "matched_candidates": cache_candidates,
                                "rows_returned": len(rows),
                            }
                        )
                        root_observation.update(
                            output={
                                "cache_status": cache_status,
                                "cache_best_distance": best_match["distance"],
                                "generated_sql": cached_sql,
                                "rows_returned": len(rows),
                            }
                        )
                        logger.info(
                            "NL2SQL semantic cache HIT: id=%s distance=%.4f",
                            best_match["id"],
                            best_match["distance"],
                        )
                        return {"output": formatted_output}

                    cache_observation.update(
                        output={
                            "cache_status": cache_status,
                            "matched_candidates": [],
                        }
                    )
                    logger.info("NL2SQL semantic cache MISS")
            except Exception as cache_exc:
                cache_status = "error"
                logger.info("NL2SQL semantic cache lookup failed, falling back to LLM generation: %s", cache_exc)

            for attempt in range(max_attempts):
                try:
                    with langfuse_client.start_as_current_observation(
                        as_type="generation",
                        name="NL2SQL Generate + Execute",
                        input={"question": question, "attempt": attempt + 1, "cache_status": cache_status},
                        metadata=self.langfuse_tracing_provider.build_observation_metadata(
                            session_id=session_id,
                            tags=["nl2sql", "generation"],
                            extra={"max_attempts": max_attempts},
                        ),
                    ) as observation:
                        messages = [HumanMessage(content=question)]
                        agent_input = {'messages': messages}
                        config:RunnableConfig = self.langfuse_tracing_provider.build_runnable_config(
                            run_id=uuid.uuid4().hex,
                            session_id=session_id,
                            thread_id=session_id,
                            tags=["nl2sql"],
                            trace_context=trace_context,
                        )

                        with propagate_attributes(session_id=session_id, tags=["nl2sql"]):
                            response = await self.agent.ainvoke(agent_input, config)
                        generated_sql = response['messages'][-1].content

                        logger.info(f"GENERATED SQL (attempt {attempt + 1}): {generated_sql}")
                        generated_sql = self._strip_code_fences(generated_sql)

                        with db_conn.get_connection() as conn:
                            cols, rows = db_conn.execute_query(conn, generated_sql)

                        formatted_output = self._format_query_rows(cols, rows)
                        rows_returned = len(rows)

                        # Successful generation/execution gets cached for future semantic reuse.
                        try:
                            self.semantic_cache.upsert_successful_query(
                                question=original_question,
                                sql_query=generated_sql,
                                answer_preview=formatted_output,
                            )
                        except Exception as cache_store_exc:
                            logger.info("Could not store NL2SQL semantic cache entry: %s", cache_store_exc)

                        observation.update(
                            output={
                                "generated_sql": generated_sql,
                                "rows_returned": rows_returned,
                                "columns": cols if rows_returned > 0 else [],
                                "token_count": extract_total_tokens_from_response(response),
                                "cache_status": cache_status,
                            }
                        )
                        root_observation.update(
                            output={
                                "generated_sql": generated_sql,
                                "rows_returned": rows_returned,
                                "cache_status": cache_status,
                                "attempts_used": attempt + 1,
                            }
                        )
                        return {"output": formatted_output}
                except Exception as e:
                    last_error = e
                    logger.exception(
                        "NL2SQL attempt %s failed for session_id=%s",
                        attempt + 1,
                        session_id,
                    )
                    if attempt < max_attempts - 1:
                        question = f"Original question: {original_question}\n\nYour previous query:\n{generated_sql}\n\nhad a mistake that resulted in an error: {e}. Fix the mistakes and consider the examples provided to solve the user question."
                        logger.warning(f"Retrying due to error: {e}")

            root_observation.update(
                output={
                    "cache_status": cache_status,
                    "error": str(last_error) if last_error else "unknown",
                }
            )
            return {"output": f"Error executing NL2SQL after {max_attempts} attempts: {str(last_error)}"}

#endregion


#region Tool Wrapper
def create_nl2sql_agent():
    """Build an NL2SQL agent instance."""
    return NL2SQLAgent()

@tool()
async def call_SQL_DB(query: str) -> str:
    """Query the SQL DB for outage, grid, voltage, and customer information."""
    NL2SQL_agent_tool = create_nl2sql_agent()
    tracing_provider = LangfuseTracingProvider()
    session_id = tracing_provider.get_current_session_id()

    try:
        result = await NL2SQL_agent_tool.call_nl2sql_agent({"input": query, "session_id": session_id})
        return result['output']
    except Exception as e:
        return f"There was an error with the SQL DB tool: {e}"
#endregion
