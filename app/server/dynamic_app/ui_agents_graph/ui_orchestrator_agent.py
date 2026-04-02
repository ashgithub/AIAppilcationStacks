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
        self._out_query = """You generate follow-up question suggestions for a power outage analytics app UI.

AVAILABLE DATA CONTEXT (do not suggest outside this scope):
- GRAPH DATA: outages, circuits, substations, assets, customers served, work orders, condition scores, capacities, voltage/network infrastructure
- RAG DATA: EPA outage actions, FEMA outage assistance guidance, Mexican disaster manual procedures

SUGGESTION RULES:
- Return 1-3 short, button-friendly follow-up questions
- Keep each suggestion specific, actionable, and easy to visualize
- Prefer suggestions that can trigger rich UI widgets (KPI cards, table, bar graph, line graph, map, timeline)
- Include at least one trend/time-oriented question when possible to encourage line graphs
- If context is DB-heavy, prioritize comparisons, rankings, distributions, and trends over time
- If context is RAG-heavy, prioritize procedural sequencing, responsibilities, and timeline-style questions
- If context is mixed, propose at least one question that combines infrastructure data plus guideline/manual context
- Avoid generic prompts (for example: "tell me more")
- Never suggest unrelated domains (sports, finance, entertainment, personal life, etc.)

OUTPUT:
- Provide only the structured list of suggested questions
"""

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
