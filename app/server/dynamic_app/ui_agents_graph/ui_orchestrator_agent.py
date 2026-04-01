from langchain.messages import AIMessage
from pydantic import BaseModel, Field

from core.gen_ai_provider import GenAIProvider
from core.dynamic_app.dynamic_struct import DynamicGraphState

class SuggestedQuestions(BaseModel):
    """Structured output for follow-up question suggestions."""
    suggested_questions: list[str] = Field(description="List of suggested questions based on context")

#region Suggestions
class SuggestionsReponseLLM:
    """LLM wrapper that generates follow-up questions in structured format."""

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
                ), name="suggestions_agent")
            ],
            'suggestions': str(suggestions.model_dump_json())
        }
#endregion
