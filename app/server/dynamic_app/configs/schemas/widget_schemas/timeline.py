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
        {{ "id": "event-timeline", "component": {{ "TimelineComponent": {{ "dataPath": {{ "path": "/events" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "timeline-view",
      "path": "/",
      "contents": [
        {{
          "key": "events",
          "valueMap": [
            {{
              "key": "event-1",
              "valueMap": [
                {{
                  "key": "date",
                  "valueString": "2023-01-15"
                }},
                {{
                  "key": "title",
                  "valueString": "Project Launch"
                }},
                {{
                  "key": "description",
                  "valueString": "Initial project kickoff meeting with stakeholders"
                }},
                {{
                  "key": "category",
                  "valueString": "Planning"
                }}
              ]
            }},
            {{
              "key": "event-2",
              "valueMap": [
                {{
                  "key": "date",
                  "valueString": "2023-03-22"
                }},
                {{
                  "key": "title",
                  "valueString": "First Milestone"
                }},
                {{
                  "key": "description",
                  "valueString": "Completed initial development phase"
                }},
                {{
                  "key": "category",
                  "valueString": "Development"
                }}
              ]
            }},
            {{
              "key": "event-3",
              "valueMap": [
                {{
                  "key": "date",
                  "valueString": "2023-06-10"
                }},
                {{
                  "key": "title",
                  "valueString": "Beta Release"
                }},
                {{
                  "key": "description",
                  "valueString": "Public beta version released for testing"
                }},
                {{
                  "key": "category",
                  "valueString": "Release"
                }}
              ]
            }},
            {{
              "key": "event-4",
              "valueMap": [
                {{
                  "key": "date",
                  "valueString": "2023-09-05"
                }},
                {{
                  "key": "title",
                  "valueString": "Final Launch"
                }},
                {{
                  "key": "description",
                  "valueString": "Official product launch and public announcement"
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
