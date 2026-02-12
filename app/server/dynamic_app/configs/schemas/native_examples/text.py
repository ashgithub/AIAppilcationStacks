COMPONENT_NAME = "Text"
COMPONENT_DESCRIPTION = "Displays text content with various styling options like headings, body text, or captions."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "text-demo","root": "text-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "text-demo",
      "components": [
        {{ "id": "text-comp", "component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Hello World" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "text-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""
