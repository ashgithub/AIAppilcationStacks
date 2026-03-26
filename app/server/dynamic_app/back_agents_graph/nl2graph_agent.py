import logging
import uuid

from langchain_core.messages import HumanMessage
from langchain.tools import tool

from database.connections import RAGDBConnection
from database.semantic_cache import (
    GraphSemanticCache,
    clear_nl2graph_semantic_cache,
    reset_nl2graph_semantic_cache,
)
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
        self.model="xai.grok-4-fast-reasoning"
        self.system_prompt = f"{GRAPH_SCHEMA_DESCRIPTION}\n\n" + "\n\n".join(
            f"Q: {ex['q']}\nPGQL:\n{ex['pgql']}" for ex in GRAPH_FEW_SHOT_EXAMPLES
        )
        self.agent = self.build_agent()
        self.langfuse_tracing_provider = LangfuseTracingProvider()
        self.semantic_cache = GraphSemanticCache()

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

        return "Graph Query Results:\n" + "\n".join(result_lines)

    async def call_nl2graphDB_agent(self, input: dict) -> dict:
        """Process the input question by generating PGQL and executing it."""
        question = input.get("input", "")
        original_question = question
        if not question:
            return {"output": "No question provided."}
        inherited_session_id = self.langfuse_tracing_provider.get_current_session_id()
        session_id = str(input.get("session_id") or inherited_session_id or uuid.uuid4().hex)

        max_attempts = 2
        generated_pgql = ''
        last_error = None
        db_conn = RAGDBConnection()

        # Fast path: semantic cache lookup first.
        try:
            cached_matches = self.semantic_cache.search_similar_questions(
                question=question,
                top_k=2,
                max_distance=0.4,
            )
            if cached_matches:
                best_match = cached_matches[0]
                cached_pgql = best_match["pgql"]
                with db_conn.get_connection() as conn:
                    cols, rows = db_conn.execute_query(conn, cached_pgql)
                logger.info(
                    "NL2Graph semantic cache HIT: id=%s distance=%.4f",
                    best_match["id"],
                    best_match["distance"],
                )
                return {"output": self._format_query_rows(cols, rows)}
        except Exception as cache_exc:
            logger.info("Semantic cache lookup failed, falling back to LLM generation: %s", cache_exc)

        for attempt in range(max_attempts):
            try:
                messages = [HumanMessage(content=question)]
                agent_input = {'messages': messages}
                response = await self.agent.ainvoke(agent_input)
                generated_pgql = response['messages'][-1].content

                logger.info(f"GENERATED PGQL (attempt {attempt + 1}): {generated_pgql}")

                generated_pgql = self._strip_code_fences(generated_pgql)

                with db_conn.get_connection() as conn:
                    cols, rows = db_conn.execute_query(conn, generated_pgql)

                formatted_output = self._format_query_rows(cols, rows)

                # Successful generation/execution gets cached for future semantic reuse.
                try:
                    self.semantic_cache.upsert_successful_query(
                        question=original_question,
                        pgql=generated_pgql,
                        answer_preview=formatted_output,
                    )
                except Exception as cache_store_exc:
                    logger.info("Could not store NL2Graph semantic cache entry: %s", cache_store_exc)

                return {"output": formatted_output}
            except Exception as e:
                last_error = e
                logger.exception(
                    "NL2Graph attempt %s failed for session_id=%s",
                    attempt + 1,
                    session_id,
                )
                if attempt < max_attempts - 1:
                    question = f"Original question: {original_question}\n\nYour previous query:\n{generated_pgql}\n\nhad a mistake that resulted in an error: {e}. Fix the mistakes and consider the examples provided to solve the user question."
                    logger.info(f"Retrying due to error: {e}")

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
#endregion


#region Developer Utilities
def reset_graphdb_semantic_cache() -> str:
    """Developer helper: drop/recreate semantic cache table for clean tests."""
    reset_nl2graph_semantic_cache()
    return "NL2Graph semantic cache reset completed."


def clear_graphdb_semantic_cache() -> str:
    """Developer helper: delete all cached rows while keeping table."""
    clear_nl2graph_semantic_cache()
    return "NL2Graph semantic cache clear completed."
#endregion
