COMPONENT_NAME = "Row"
COMPONENT_DESCRIPTION = "Horizontal layout container that arranges child components side by side with configurable distribution and alignment."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "row-demo","root": "row-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "row-demo",
      "components": [
        {{ "id": "row-comp", "component": {{ "Row": {{
          "children": {{ "explicitList": ["text-1", "text-2", "text-3"] }},
          "distribution": "spaceEvenly",
          "alignment": "center"
        }} }} }},
        {{ "id": "text-1", "component": {{ "Text": {{ "text": {{ "literalString": "Left" }} }} }} }},
        {{ "id": "text-2", "component": {{ "Text": {{ "text": {{ "literalString": "Center" }}, "usageHint": "h2" }} }} }},
        {{ "id": "text-3", "component": {{ "Text": {{ "text": {{ "literalString": "Right" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "row-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""