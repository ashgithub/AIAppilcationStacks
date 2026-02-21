from pydantic import BaseModel, Field
from core.gen_ai_provider import GenAIProvider

class SuggestedQuestions(BaseModel):
    """ Structured output to capture suggested questions based on LLM response """
    suggested_questions: list[str] = Field(description="List of suggested questions based on context")

class SuggestionModel:
    
    def build_suggestion_model(self):
        suggestions_llm = GenAIProvider().build_oci_client()

        return suggestions_llm.with_structured_output(SuggestedQuestions)