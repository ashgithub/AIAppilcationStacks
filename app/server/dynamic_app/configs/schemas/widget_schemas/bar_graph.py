WIDGET_NAME = "bargraph"
WIDGET_DESCRIPTION = "component designed to compare using data bars with legend. Requires good data references and specifications."
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "energy-view","root": "main-column" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "energy-view",
      "components": [
        {{ "id": "main-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "energy-table"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Energy Usage and Outages Bar Chart" }} }} }} }},
        {{ "id": "energy-table", "component": {{ "EnergyBarChart": {{ "energy": {{ "path": "/energy" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "energy-view",
      "path": "/",
      "contents": [
        {{
          "key": "energy",
          "valueMap": [
            {{
              "key": "energy-1",
              "valueMap": [
                {{
                  "key": "region",
                  "valueString": "North District"
                }},
                {{
                  "key": "type",
                  "valueString": "Residential"
                }},
                {{
                  "key": "usage",
                  "valueNumber": 1500
                }},
                {{
                  "key": "outages",
                  "valueNumber": 2
                }},
                {{
                  "key": "description",
                  "valueString": "High residential energy consumption with minimal outages"
                }}
              ]
            }},
            {{
              "key": "energy-2",
              "valueMap": [
                {{
                  "key": "region",
                  "valueString": "Downtown"
                }},
                {{
                  "key": "type",
                  "valueString": "Commercial"
                }},
                {{
                  "key": "usage",
                  "valueNumber": 3200
                }},
                {{
                  "key": "outages",
                  "valueNumber": 5
                }},
                {{
                  "key": "description",
                  "valueString": "Heavy commercial usage with occasional outages"
                }}
              ]
            }},
            {{
              "key": "energy-3",
              "valueMap": [
                {{
                  "key": "region",
                  "valueString": "Industrial Zone"
                }},
                {{
                  "key": "type",
                  "valueString": "Industrial"
                }},
                {{
                  "key": "usage",
                  "valueNumber": 5000
                }},
                {{
                  "key": "outages",
                  "valueNumber": 8
                }},
                {{
                  "key": "description",
                  "valueString": "Intensive industrial operations with frequent outages"
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""
