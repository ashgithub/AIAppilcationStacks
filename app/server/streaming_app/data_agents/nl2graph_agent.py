import logging
import uuid

from langchain_core.messages import HumanMessage
from langchain.tools import tool

from database.connections import RAGDBConnection
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
        self.system_prompt = f"{GRAPH_SCHEMA_DESCRIPTION}\n\n" + "\n\n".join(
            f"Q: {ex['q']}\nPGQL:\n{ex['pgql']}" for ex in GRAPH_FEW_SHOT_EXAMPLES
        )
        self.agent = self.build_agent()
        self.langfuse_tracing_provider = LangfuseTracingProvider()

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

        for attempt in range(max_attempts):
            try:
                messages = [HumanMessage(content=question)]
                agent_input = {'messages': messages}
                response = await self.agent.ainvoke(agent_input)
                generated_pgql = response['messages'][-1].content

                logger.info(f"GENERATED PGQL (attempt {attempt + 1}): {generated_pgql}")

                if generated_pgql.startswith("```"):
                    lines = generated_pgql.split("\n")
                    generated_pgql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

                db_conn = RAGDBConnection()

                with db_conn.get_connection() as conn:
                    cols, rows = db_conn.execute_query(conn, generated_pgql)

                if not rows:
                    return {"output": "Query executed successfully but returned no results."}

                result_lines = []
                for row in rows:
                    row_data = ", ".join(f"{col}: {val}" for col, val in zip(cols, row))
                    result_lines.append(row_data)

                return {"output": f"Graph Query Results:\n" + "\n".join(result_lines)}
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
#endregion
