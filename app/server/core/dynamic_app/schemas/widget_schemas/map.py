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
        {{ "id": "location-map", "component": {{ "MapComponent": {{
          "dataPath": "/mapData",
          "centerLat": 40.7128,
          "centerLng": -74.0060,
          "zoom": 10
        }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "map-view",
      "path": "/",
      "contents": [
        {{
          "key": "mapData",
          "valueMap": [
            {{
              "key": "0",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "New York"
                }},
                {{
                  "key": "latitude",
                  "valueNumber": 40.7128
                }},
                {{
                  "key": "longitude",
                  "valueNumber": -74.0060
                }},
                {{
                  "key": "description",
                  "valueString": "The Big Apple"
                }}
              ]
            }},
            {{
              "key": "1",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Boston"
                }},
                {{
                  "key": "latitude",
                  "valueNumber": 42.3601
                }},
                {{
                  "key": "longitude",
                  "valueNumber": -71.0589
                }},
                {{
                  "key": "description",
                  "valueString": "Historic city"
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""
