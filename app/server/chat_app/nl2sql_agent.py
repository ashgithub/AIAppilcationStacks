import logging
import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langfuse import propagate_attributes

from database.connections import RAGDBConnection
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

    async def call_nl2sql_agent(self, input: dict) -> dict:
        """Process the input question by generating SQL and executing it."""
        question = input.get("input", "")
        original_question = question
        if not question:
            return {"output": "No question provided."}

        inherited_session_id = self.langfuse_tracing_provider.get_current_session_id()
        session_id = str(input.get("session_id") or inherited_session_id or uuid.uuid4().hex)
        langfuse_client = self.langfuse_tracing_provider.get_current_client()

        max_attempts = 2
        generated_sql = ''
        last_error = None

        for attempt in range(max_attempts):
            try:
                with langfuse_client.start_as_current_observation(
                    as_type="generation",
                    name="OutageEnergyLLM -> NL2SQL Agent",
                    input={"question": question, "attempt": attempt + 1},
                    metadata=self.langfuse_tracing_provider.build_observation_metadata(
                        session_id=session_id,
                        tags=["nl2sql"],
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
                    )

                    with propagate_attributes(session_id=session_id, tags=["nl2sql"]):
                        response = await self.agent.ainvoke(agent_input, config)
                    generated_sql = response['messages'][-1].content

                    logger.info(f"GENERATED SQL (attempt {attempt + 1}): {generated_sql}")

                    if generated_sql.startswith("```"):
                        lines = generated_sql.split("\n")
                        generated_sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

                    db_conn = RAGDBConnection()

                    with db_conn.get_connection() as conn:
                        cols, rows = db_conn.execute_query(conn, generated_sql)

                    if not rows:
                        observation.update(
                            output={
                                "generated_sql": generated_sql,
                                "rows_returned": 0,
                                "token_count": extract_total_tokens_from_response(response),
                            }
                        )
                        return {"output": "Query executed successfully but returned no results."}

                    result_lines = []
                    for row in rows:
                        row_data = ", ".join(f"{col}: {val}" for col, val in zip(cols, row))
                        result_lines.append(row_data)

                    observation.update(
                        output={
                            "generated_sql": generated_sql,
                            "rows_returned": len(rows),
                            "columns": cols,
                            "token_count": extract_total_tokens_from_response(response),
                        }
                    )
                    return {"output": f"Query Results:\n" + "\n".join(result_lines)}
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

    try:
        result = await NL2SQL_agent_tool.call_nl2sql_agent({"input": query})
        return result['output']
    except Exception as e:
        return f"There was an error with the SQL DB tool: {e}"
#endregion
