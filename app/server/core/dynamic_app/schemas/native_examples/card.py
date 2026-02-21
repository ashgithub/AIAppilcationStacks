COMPONENT_NAME = "Card"
COMPONENT_DESCRIPTION = "Container component that wraps content in a visually distinct card with padding and styling."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "card-demo","root": "card-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "card-demo",
      "components": [
        {{ "id": "card-comp", "component": {{ "Card": {{ "child": "content-column" }} }} }},
        {{ "id": "content-column", "component": {{ "Column": {{
          "children": {{ "explicitList": ["card-title", "card-text"] }}
        }} }} }},
        {{ "id": "card-title", "component": {{ "Text": {{ "text": {{ "literalString": "Card Title" }}, "usageHint": "h3" }} }} }},
        {{ "id": "card-text", "component": {{ "Text": {{ "text": {{ "literalString": "This is content inside a card component. Cards provide visual separation and grouping for related content." }}, "usageHint": "body" }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "card-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""