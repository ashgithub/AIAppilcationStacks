import logging
import os
from collections.abc import AsyncIterable
from typing import Any
from langchain.agents import create_agent
from langchain_oci import ChatOCIGenAI
from langchain.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

from chat_app.langchain_tools import get_outage_data, get_energy_data, get_industry_data

logger = logging.getLogger(__name__)

class OCIOutageEnergyLLM:
    """ Agent using OCI libraries to provide outage and energy information """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain", "text/event-stream"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_llm"

    def _build_agent(self) -> CompiledStateGraph:
        """Builds the LLM agent for the outage and energy agent."""
        oci_llm = ChatOCIGenAI(
            model_id="xai.grok-4-fast-non-reasoning",
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs={"temperature":0.7},
            auth_profile=os.getenv("AUTH_PROFILE"),
        )

        return create_agent(
            model=oci_llm,
            tools=[get_outage_data, get_energy_data, get_industry_data],
            system_prompt="You are an outage and energy assistant that helps users get information about power outages, energy statistics, and industry performance. You MUST use the available tools to retrieve data before providing any answers. Always call the relevant tools first: get_outage_data for outage information, get_energy_data for energy statistics, and get_industry_data for industry performance data. Do not ask the user questions or seek clarification - instead, use the tools to gather all necessary information. Present your findings in well-formatted markdown responses. Never respond without first using the appropriate tools to fetch current data.",
            name="outage_energy_llm"
        )
    
    async def oci_stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        """ Function to call agent and stream responses """
        
        current_message = {"messages":[HumanMessage(query)]}
        print("="*50)
        print(current_message)
        config:RunnableConfig = {"run_id":str(session_id)}
        final_response_content = None
        final_model_state = None
        model_token_count = 0

        async for event in self._agent.astream(
            input=current_message,
            stream_mode="values",
            config=config
        ):
            latest_update:AnyMessage = event['messages'][-1]
            final_response_content = latest_update.content

            if hasattr(latest_update, 'tool_calls') and latest_update.tool_calls:
                tool_name = str(latest_update.tool_calls[0].get('name'))
                tool_args = str(latest_update.tool_calls[0].get('args'))
                latest_update = f"Model calling tool: {tool_name} with args {tool_args}"
            elif isinstance(latest_update,ToolMessage):
                tool_name = str(latest_update.name)
                status_content = str(latest_update.content)
                latest_update = f"Tool {tool_name} responded with:\n{status_content[:100]}...\n\nInformation passed to agent to build response"
            elif isinstance(latest_update, AIMessage):
                status_content = str(latest_update.content)
                model_id = str(latest_update.response_metadata.get("model_id"))
                total_tokens_on_call = int(latest_update.response_metadata.get("total_tokens"))
                model_token_count = model_token_count + total_tokens_on_call
                agent_name = str(latest_update.name)
                model_data = f"""
                    model_id: {model_id},
                    agent_name: {agent_name},
                    total_tokens_on_call: {str(model_token_count)}
                """
                latest_update = f"Agent current response:\n{status_content[:100]}...\n\nAgent metadata:\n{model_data}"
                final_model_state = latest_update
            else:
                status_content = str(latest_update.content)
                latest_update = f"Processing task, current state:\n{status_content[:100]}..."

            # Yield intermediate updates on every attempt
            yield {
                "is_task_complete": False,
                "updates": latest_update
            }
        
        yield {
            "is_task_complete": True,
            "content": f"{final_response_content}",
            "final_state": f"{str(final_response_content)[:100]}\n{final_model_state}"
        }