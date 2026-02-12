COMPONENT_NAME = "Button"
COMPONENT_DESCRIPTION = "Interactive button component that can trigger client-side actions when clicked."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "button-demo","root": "button-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "button-demo",
      "components": [
        {{ "id": "button-comp", "component": {{ "Button": {{ "child": "btn-text", "primary": true, "action": {{ "name": "click_action" }} }} }} }},
        {{ "id": "btn-text", "component": {{ "Text": {{ "text": {{ "literalString": "Click Me" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "button-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""
