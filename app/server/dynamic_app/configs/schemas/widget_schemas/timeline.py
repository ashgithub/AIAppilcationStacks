WIDGET_NAME = "TimelineComponent"
WIDGET_DESCRIPTION = "component designed to show the history of events ocurred over a time span. Requires good time definition and description of events."
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "timeline-view","root": "main-column" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "timeline-view",
      "components": [
        {{ "id": "main-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "event-timeline"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Event Timeline" }} }} }} }},
        {{ "id": "event-timeline", "component": {{ "TimelineComponent": {{ "dataPath": "/timelineData" }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "timeline-view",
      "path": "/",
      "contents": [
        {{
          "key": "timelineData",
          "valueMap": [
            {{
              "key": "0",
              "valueMap": [
                {{
                  "key": "date",
                  "valueString": "2023-01-15"
                }},
                {{
                  "key": "title",
                  "valueString": "Project Start"
                }},
                {{
                  "key": "description",
                  "valueString": "Initial project kickoff"
                }},
                {{
                  "key": "category",
                  "valueString": "Planning"
                }}
              ]
            }},
            {{
              "key": "1",
              "valueMap": [
                {{
                  "key": "date",
                  "valueString": "2023-06-01"
                }},
                {{
                  "key": "title",
                  "valueString": "First Release"
                }},
                {{
                  "key": "description",
                  "valueString": "Beta version released"
                }},
                {{
                  "key": "category",
                  "valueString": "Release"
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""
