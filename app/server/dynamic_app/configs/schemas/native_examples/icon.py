COMPONENT_NAME = "Icon"
COMPONENT_DESCRIPTION = "Displays predefined icons for visual elements and user interface indicators."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "icon-demo","root": "icon-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "icon-demo",
      "components": [
        {{ "id": "icon-comp", "component": {{ "Icon": {{ "name": {{ "literalString": "info" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "icon-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""