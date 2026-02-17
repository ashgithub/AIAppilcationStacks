WIDGET_NAME = "MapComponent"
WIDGET_DESCRIPTION = "component designed to display pins over a map at a given location. Requires exact coordinates and exact coordinates placement for the place of interest"
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "map-view","root": "main-column" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "map-view",
      "components": [
        {{ "id": "main-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "location-map"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Location Map" }} }} }} }},
        {{ "id": "location-map", "component": {{ "MapComponent": {{ "dataPath": {{ "path": "/locations" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "map-view",
      "path": "/",
      "contents": [
        {{
          "key": "locations",
          "valueMap": [
            {{
              "key": "location-1",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Statue of Liberty"
                }},
                {{
                  "key": "lat",
                  "valueNumber": 40.6892
                }},
                {{
                  "key": "lng",
                  "valueNumber": -74.0445
                }},
                {{
                  "key": "description",
                  "valueString": "Iconic statue in New York Harbor"
                }}
              ]
            }},
            {{
              "key": "location-2",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Central Park"
                }},
                {{
                  "key": "lat",
                  "valueNumber": 40.7829
                }},
                {{
                  "key": "lng",
                  "valueNumber": -73.9654
                }},
                {{
                  "key": "description",
                  "valueString": "Large urban park in Manhattan"
                }}
              ]
            }},
            {{
              "key": "location-3",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Times Square"
                }},
                {{
                  "key": "lat",
                  "valueNumber": 40.758
                }},
                {{
                  "key": "lng",
                  "valueNumber": -73.9851
                }},
                {{
                  "key": "description",
                  "valueString": "Busy commercial intersection"
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""
