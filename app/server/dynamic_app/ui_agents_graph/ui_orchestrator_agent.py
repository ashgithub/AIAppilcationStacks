from langchain.agents import create_agent
from langchain.messages import AIMessage
from pydantic import BaseModel, Field

from dynamic_app.ui_agents_graph.widget_tools import get_widget_catalog, get_native_component_catalog
from core.gen_ai_provider import GenAIProvider
from core.dynamic_app.dynamic_struct import UIOrchestratorOutput
from core.dynamic_app.dynamic_struct import DynamicGraphState

class SuggestedQuestions(BaseModel):
    """ Structured output to capture suggested questions based on LLM response """
    suggested_questions: list[str] = Field(description="List of suggested questions based on context")

class SuggestionsReponseLLM:
    """ LLM that uses the structured response to provide some follow up questions """

    def __init__(self):
        self._suggestion_out = self._build_suggestion_model()
        self._out_query = "Based on the given context, generate a list of at least 1-3 suggested follow up questions that the user might want to ask next. These should be relevant to the information provided and help the user explore the topic further. Always provide suggestions, even if the information is limited. Consider questions will be shown in UI, in buttons, so build them short or clean to show good on UI."

    def _build_suggestion_model(self):
        genai_provider = GenAIProvider()
        suggestions_llm = genai_provider.build_oci_client()

        return suggestions_llm.with_structured_output(SuggestedQuestions)
    
    async def __call__(self, state: DynamicGraphState) -> DynamicGraphState:
        suggestions = await self._suggestion_out.ainvoke(self._out_query+f"\n\nContext for question generation:\n{state['messages'][-1].content}")

        if not suggestions: suggestions = SuggestedQuestions(suggested_questions=["Tell me more details about first data", "Make a summary of data given"])

        return {
            'messages': state['messages'] + [
                AIMessage(content=(
                    str(suggestions.model_dump_json())
                ))
            ],
            'suggestions': str(suggestions.model_dump_json())
        }

class UIOrchestrator:
    """ Orchestrator that receives the user query, the summary of data found and widget skills to select the suitable ones """

    AGENT_INSTRUCTIONS = """
    You are an orchestrator agent that selects suitable UI components for data visualization.

    TASK:
    - Analyze the user query and available data
    - Select 1-3 most appropriate UI components from the available catalogs
    - ALWAYS use 'get_widget_catalog' for custom visualization components (charts, tables, etc.)
    - Optionally use 'get_native_component_catalog' for basic UI components (Text, Button, etc.) if needed for layout
    - Return ONLY a simple list of component names in this format:

    COMPONENTS: component1, component2, component3

    EXAMPLE OUTPUT (confirm components available with the tools):
    COMPONENTS: bar-graph, table, text

    Do not include any other text or explanation. Just the component list.
    Focus on selecting the main visualization components, native components are supplementary.
    """

    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self._client = self.gen_ai_provider.build_oci_client(model_id="openai.gpt-4.1",model_kwargs={"temperature":0.7})
        self._output_client = self.gen_ai_provider.build_oci_client(model_id="openai.gpt-4.1",model_kwargs={"temperature":0.7})
        self.agent_name = "ui_orchestrator"
        self.agent = self._build_agent()
        self.output_response = self._build_output_llm()

    async def __call__(self, state: DynamicGraphState):
        response =  await self.agent.ainvoke(state)
        # To support structured output, seems langchain_oci has erro here
        structured_response = await self.output_response.ainvoke(f"Build the component list with the information on: {response['messages'][-1].content}")
        return {
            'messages': state['messages'] + [
                AIMessage(content=(
                    str(structured_response.model_dump_json())
                ))
            ]
        }
    
    def _build_agent(self):
        return create_agent(
            model=self._client,
            system_prompt=self.AGENT_INSTRUCTIONS,
            tools=[get_widget_catalog, get_native_component_catalog],
            name=self.agent_name
        )
    
    def _build_output_llm(self):
        return self._output_client.with_structured_output(UIOrchestratorOutput)
    
async def main():
    from langchain.messages import HumanMessage
    orchestrator = UIOrchestrator()
    messages:DynamicGraphState = {'messages':[HumanMessage("What is my bill?")]}
    response = await orchestrator(messages)
    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())