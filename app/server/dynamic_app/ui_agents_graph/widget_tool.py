from langchain.tools import tool
from dynamic_app.configs.gen_ai_provider import GenAIProvider

class WidgetAgent:
    def __init__(self):
        self.gen_ai_provider = GenAIProvider()
        self.gen_ai_client = self.gen_ai_provider.build_oci_client()
    
    async def call_widget_builder(self, query:str)->str:
        response = await self.gen_ai_client.ainvoke(query)
        return response.content
        
@tool()
async def build_widget_schema(widget:str, instructons:str, context:str)->str:
    """Generates a bar graph widget schema based on given context

    Args:
        widget: name of the widget to generate
        instructions: instructions about how to build the component
        context: required context such as data, examples, links, etc.
    """
    query = f"build the given widget with the data: instructions:{instructons} context:{context}"

    widget_agent = WidgetAgent()
    response = await widget_agent.call_widget_builder(query)

    return response