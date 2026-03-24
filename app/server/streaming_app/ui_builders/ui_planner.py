from dynamic_app.ui_agents_graph.widget_tools import get_widget_catalog, get_native_component_catalog
from core.base_agent import BaseAgent
from core.dynamic_app.dynamic_struct import UIOrchestratorOutput
from core.dynamic_app.prompts import UI_ORCHESTRATOR_INSTRUCTIONS

class UIPlanner(BaseAgent):
    """Selects UI components based on backend results and available widget tools."""

    def __init__(self):
        super().__init__()
        self.agent_name = "ui_planner"
        self.system_prompt = UI_ORCHESTRATOR_INSTRUCTIONS
        self.tools = [get_widget_catalog, get_native_component_catalog]
        self.response_format=UIOrchestratorOutput
        self.agent = self.build_agent()

    async def __call__(self, state):
        return await self.agent.ainvoke(state)

#region Local Test Harness
async def main():
    from langchain.messages import HumanMessage
    orchestrator = UIPlanner()
    payload = {
        "input": {"messages": [HumanMessage("What is my bill?")]},
        "config": {"configurable": {"thread_id": "test_ui_planner"}},
    }
    response = await orchestrator(payload)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
#endregion
