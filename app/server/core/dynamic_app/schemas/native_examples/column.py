COMPONENT_NAME = "Column"
COMPONENT_DESCRIPTION = "Vertical layout container that arranges child components in a column with configurable distribution and alignment."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "column-demo","root": "column-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "column-demo",
      "components": [
        {{ "id": "column-comp", "component": {{ "Column": {{
          "children": {{ "explicitList": ["title", "subtitle", "content"] }},
          "distribution": "start",
          "alignment": "stretch"
        }} }} }},
        {{ "id": "title", "component": {{ "Text": {{ "text": {{ "literalString": "Main Title" }}, "usageHint": "h1" }} }} }},
        {{ "id": "subtitle", "component": {{ "Text": {{ "text": {{ "literalString": "Subtitle text here" }}, "usageHint": "h3" }} }} }},
        {{ "id": "content", "component": {{ "Text": {{ "text": {{ "literalString": "This is the main content area with more detailed information." }}, "usageHint": "body" }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "column-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""