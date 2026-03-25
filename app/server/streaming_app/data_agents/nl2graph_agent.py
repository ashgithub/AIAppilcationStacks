import logging
import uuid
import asyncio

from langchain_core.messages import HumanMessage
from langchain.tools import tool

from database.connections import RAGDBConnection
from database.pgql_query_cache import PGQLQueryCache
from core.base_agent import BaseAgent
from core.langfuse_tracing import LangfuseTracingProvider
from core.dynamic_app.prompts.graph_agent import GRAPH_SCHEMA_DESCRIPTION, GRAPH_FEW_SHOT_EXAMPLES

logger = logging.getLogger(__name__)

#region Agent Definition
class NL2GraphAgent(BaseAgent):
    """Agent for natural language to PGQL translation and execution."""

    def __init__(self):
        super().__init__()
        self.agent_name = "nl2graph_agent"
        self.model = "xai.grok-4-fast-reasoning"
        self.system_prompt = f"{GRAPH_SCHEMA_DESCRIPTION}\n\n" + "\n\n".join(
            f"Q: {ex['q']}\nPGQL:\n{ex['pgql']}" for ex in GRAPH_FEW_SHOT_EXAMPLES
        )
        self.agent = self.build_agent()
        self.langfuse_tracing_provider = LangfuseTracingProvider()
        self.query_cache = PGQLQueryCache()

    @staticmethod
    def _format_rows(cols, rows) -> str:
        if not rows:
            return "Query executed successfully but returned no results."

        result_lines = []
        for row in rows:
            row_data = ", ".join(f"{col}: {val}" for col, val in zip(cols, row))
            result_lines.append(row_data)
        return f"Graph Query Results:\n" + "\n".join(result_lines)

    @staticmethod
    async def _store_query_in_cache(query_cache: PGQLQueryCache, question: str, pgql: str) -> None:
        try:
            await asyncio.to_thread(query_cache.store_successful_query, question, pgql, "llm_generated")
        except Exception:
            logger.exception("Failed to asynchronously store PGQL in cache.")

    async def call_nl2graphDB_agent(self, input: dict) -> dict:
        """Process the input question by generating PGQL and executing it."""
        question = input.get("input", "")
        original_question = question
        if not question:
            return {"output": "No question provided."}
        if input.get("reset_cache"):
            deleted_count = self.query_cache.clear()
            return {"output": f"PGQL cache reset complete. Deleted {deleted_count} cached entries."}

        inherited_session_id = self.langfuse_tracing_provider.get_current_session_id()
        session_id = str(input.get("session_id") or inherited_session_id or uuid.uuid4().hex)

        max_attempts = 2
        generated_pgql = ''
        last_error = None
        db_conn = RAGDBConnection()

        cache_hit = None
        try:
            cache_hit = self.query_cache.get_cached_pgql(original_question)
        except Exception:
            logger.exception("Failed to lookup PGQL cache for session_id=%s", session_id)
            logger.info("[PGQL_CACHE][LOOKUP_ERROR] session_id=%s -> generating with model", session_id)

        if cache_hit:
            try:
                cached_pgql = self.query_cache.normalize_pgql(cache_hit.pgql)
                with db_conn.get_connection() as conn:
                    cols, rows = db_conn.execute_query(conn, cached_pgql)
                try:
                    self.query_cache.register_execution_outcome(cache_hit.cache_id, succeeded=True)
                except Exception:
                    logger.exception("Failed to register successful cache execution for session_id=%s", session_id)
                logger.info(
                    "[PGQL_CACHE][HIT] strategy=%s session_id=%s distance=%s",
                    cache_hit.strategy,
                    session_id,
                    cache_hit.distance,
                )
                return {"output": self._format_rows(cols, rows)}
            except Exception as cache_error:
                try:
                    self.query_cache.register_execution_outcome(cache_hit.cache_id, succeeded=False)
                except Exception:
                    logger.exception("Failed to register failed cache execution for session_id=%s", session_id)
                logger.warning(
                    "[PGQL_CACHE][FAILED] session_id=%s strategy=%s error=%s -> generating with model",
                    session_id,
                    cache_hit.strategy,
                    cache_error,
                )
        else:
            logger.info("[PGQL_CACHE][MISS] session_id=%s -> generating with model", session_id)

        for attempt in range(max_attempts):
            try:
                logger.info("[PGQL_GEN][START] session_id=%s attempt=%s", session_id, attempt + 1)
                messages = [HumanMessage(content=question)]
                agent_input = {'messages': messages}
                response = await self.agent.ainvoke(agent_input)
                generated_pgql = self.query_cache.normalize_pgql(response['messages'][-1].content)

                logger.info("[PGQL_GEN][SUCCESS] session_id=%s attempt=%s pgql=%s", session_id, attempt + 1, generated_pgql)

                with db_conn.get_connection() as conn:
                    cols, rows = db_conn.execute_query(conn, generated_pgql)

                asyncio.create_task(self._store_query_in_cache(self.query_cache, original_question, generated_pgql))
                return {"output": self._format_rows(cols, rows)}
            except Exception as e:
                last_error = e
                logger.exception(
                    "NL2Graph attempt %s failed for session_id=%s",
                    attempt + 1,
                    session_id,
                )
                if attempt < max_attempts - 1:
                    question = f"Original question: {original_question}\n\nYour previous query:\n{generated_pgql}\n\nhad a mistake that resulted in an error: {e}. Fix the mistakes and consider the examples provided to solve the user question."
                    logger.warning(f"Retrying due to error: {e}")

        return {"output": f"Error executing NL2Graph after {max_attempts} attempts: {str(last_error)}"}
#endregion


#region Tool Wrapper
def create_nl2graph_agent():
    """Build an NL2Graph agent instance."""
    return NL2GraphAgent()

@tool()
async def call_graphDB(query: str) -> str:
    """Query the graph database for outage, grid, voltage, and customer information."""
    NL2Graph_agent_tool = create_nl2graph_agent()

    try:
        result = await NL2Graph_agent_tool.call_nl2graphDB_agent({"input": query})
        return result['output']
    except Exception as e:
        return f"There was an error with the Graph DB tool: {e}"

@tool()
async def reset_graphDB_cache() -> str:
    """Reset all persisted PGQL cache entries."""
    nl2graph_agent_tool = create_nl2graph_agent()
    try:
        result = await nl2graph_agent_tool.call_nl2graphDB_agent({"input": "__cache_reset__", "reset_cache": True})
        return result["output"]
    except Exception as e:
        return f"There was an error resetting Graph DB cache: {e}"

@tool()
async def graphDB_cache_stats() -> str:
    """Return PGQL cache health and usage statistics."""
    nl2graph_agent_tool = create_nl2graph_agent()
    try:
        stats = nl2graph_agent_tool.query_cache.stats()
        stats_items = ", ".join(f"{key}: {value}" for key, value in stats.items())
        return f"Graph DB cache stats -> {stats_items}"
    except Exception as e:
        return f"There was an error retrieving Graph DB cache stats: {e}"
#endregion
