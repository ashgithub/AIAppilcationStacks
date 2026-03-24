"""Reusable parallel widget worker agent."""
import json
import logging

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage

from core.gen_ai_provider import GenAIProvider
from core.dynamic_app.dynamic_struct import DynamicGraphState
from core.dynamic_app.prompts.ui_parallel import get_ui_parallel_widget_worker_instructions
from dynamic_app.ui_agents_graph.widget_tools import (
    create_custom_component_tools,
    get_native_component_catalog,
    get_native_component_example,
)

logger = logging.getLogger(__name__)

class WidgetWorkerOutput(BaseModel):
    """Structured output for one worker package."""
    package_id: str = Field(description="Package id from planner")
    surface_messages: list[dict] = Field(description="A2UI fragment messages for this package")
    target_component_ids: list[str] = Field(description="Owned component ids")
    target_data_keys: list[str] = Field(description="Owned data keys")
    estimated_complexity: str = Field(description="low | medium | high")
    warnings: list[str] = Field(description="Validation or coverage warnings")


class UIParallelWidgetWorkerAgent:
    """Single worker implementation; instantiate/call in parallel across packages."""

    def __init__(self, inline_catalog: list | None = None):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(
            model_id="xai.grok-4-fast-reasoning",
            model_kwargs={"temperature": 0.25},
        )
        self._output_client = self.gen_ai_provider.build_oci_client(
            model_id="xai.grok-4-fast-reasoning",
            model_kwargs={"temperature": 0.1},
        )
        self.inline_catalog = inline_catalog or []
        self.agent_name = "ui_parallel_widget_worker"
        self.output_response = self._output_client.with_structured_output(WidgetWorkerOutput, method='function_calling')

    async def run_package(
        self,
        state: DynamicGraphState,
        package_id: str,
        widgets: list[str],
        target_component_ids: list[str],
        target_data_keys: list[str],
    ) -> WidgetWorkerOutput:
        """Run this worker for one package and return structured fragment output."""
        get_custom_component_catalog, get_custom_component_example = create_custom_component_tools(
            self.inline_catalog,
            allowed_components=widgets,
        )
        system_prompt = get_ui_parallel_widget_worker_instructions(
            package_id=package_id,
            widgets=widgets,
            target_component_ids=target_component_ids,
            target_data_keys=target_data_keys,
        )
        agent = create_agent(
            model=self._client,
            system_prompt=system_prompt,
            tools=[
                get_custom_component_catalog,
                get_custom_component_example,
                get_native_component_catalog,
                get_native_component_example,
            ],
            name=f"{self.agent_name}_{package_id}",
        )

        # Use a dedicated user instruction so workers remain deterministic and independent.
        worker_request = HumanMessage(
            content=(
                f"Generate A2UI fragment for package '{package_id}'. "
                "Return only package-scoped messages."
            )
        )
        worker_state = {
            "messages": [*state["messages"], worker_request],
            "suggestions": state.get("suggestions", ""),
        }

        response = await agent.ainvoke(worker_state)
        unstructured_content = str(response["messages"][-1].content)
        structured = await self.output_response.ainvoke(
            "Convert to valid WidgetWorkerOutput JSON:\n"
            f"{unstructured_content}"
        )
        logger.info(
            "Worker %s produced %s message(s), complexity=%s.",
            package_id,
            len(structured.surface_messages),
            structured.estimated_complexity,
        )
        return structured

    async def __call__(self, state: DynamicGraphState):
        """Compatibility call: expects package payload in latest message content."""
        latest_content = str(state["messages"][-1].content)
        package = json.loads(latest_content)
        output = await self.run_package(
            state=state,
            package_id=package["package_id"],
            widgets=package.get("widgets", []),
            target_component_ids=package.get("target_component_ids", []),
            target_data_keys=package.get("target_data_keys", []),
        )
        return {
            "messages": state["messages"] + [
                AIMessage(content=output.model_dump_json(), name=self.agent_name)
            ]
        }

