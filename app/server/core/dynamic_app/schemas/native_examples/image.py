COMPONENT_NAME = "Image"
COMPONENT_DESCRIPTION = "Displays images with configurable sizing, fitting options, and usage hints for different contexts."
EXAMPLE_A2UI_MESSAGE = """
[
  {{ "beginRendering": {{ "surfaceId": "image-demo","root": "image-comp" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "image-demo",
      "components": [
        {{ "id": "image-comp", "component": {{ "Image": {{ "url": {{ "literalString": "https://example.com/image.jpg" }}, "fit": "cover", "usageHint": "mediumFeature" }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "image-demo",
      "path": "/",
      "contents": []
    }}
  }}
]"""
