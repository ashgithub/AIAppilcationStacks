import logging

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool

from database.connections import RAGDBConnection
from core.base_agent import BaseAgent
from core.chat_app.prompts.sql_agent import SQL_SCHEMA_DESCRIPTION, SQL_FEW_SHOT_EXAMPLES

logger = logging.getLogger(__name__)

class NL2SQLAgent(BaseAgent):
    """Agent for natural language to SQL translation and execution."""

    def __init__(self):
        super().__init__()
        self.agent_name = "nl2sql_agent"
        self.system_prompt = f"{SQL_SCHEMA_DESCRIPTION}\n\n" + "\n\n".join(
            f"Q: {ex['q']}\nSQL:\n{ex['sql']}" for ex in SQL_FEW_SHOT_EXAMPLES
        )
        self.agent = self.build_agent()

    async def call_nl2sql_agent(self, input: dict) -> dict:
        """Process the input question by generating SQL and executing it."""
        question = input.get("input", "")
        original_question = question
        if not question:
            return {"output": "No question provided."}
        
        max_attempts = 2
        generated_sql = ''
        last_error = None

        for attempt in range(max_attempts):
            try:
                messages = [HumanMessage(content=question)]

                agent_input = {'messages': messages}
                config:RunnableConfig = {"configurable": {"thread_id": "1234"}}

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
                    return {"output": "Query executed successfully but returned no results."}

                result_lines = []
                for row in rows:
                    row_data = ", ".join(f"{col}: {val}" for col, val in zip(cols, row))
                    result_lines.append(row_data)

                return {"output": f"Query Results:\n" + "\n".join(result_lines)}
            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    # Help model to remember query with error information
                    question = f"Original question: {original_question}\n\nYour previous query:\n{generated_sql}\n\nhad a mistake that resulted in an error: {e}. Fix the mistakes and consider the examples provided to solve the user question."
                    logger.warning(f"Retrying due to error: {e}")
        
        return {"output": f"Error executing NL2SQL after {max_attempts} attempts: {str(last_error)}"}


def create_nl2sql_agent():
    """Instantiate to call"""
    return NL2SQLAgent()

@tool()
async def call_SQL_DB(query: str) -> str:
    """ Tool to call the SQL DB with information about outage network, grid, voltaje, customers, etc. using NL to query"""
    NL2SQL_agent_tool = create_nl2sql_agent()

    try:
        result = await NL2SQL_agent_tool.call_nl2sql_agent({"input": query})
        return result['output']
    except Exception as e:
        return f"There was an error with the SQL DB tool: {e}"