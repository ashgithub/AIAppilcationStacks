WIDGET_NAME = "BarGraph"
WIDGET_DESCRIPTION = "component designed to display bar charts comparing data values with labels. Requires dataPath for values and labelPath for categories."
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "bar-chart-view","root": "main-container" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "bar-chart-view",
      "components": [
        {{ "id": "main-container", "component": {{ "Column": {{ "children": {{ "explicitList": ["bar-chart"] }} }} }} }},
        {{ "id": "bar-chart", "component": {{ "BarGraph": {{
          "dataPath": "/chartData",
          "labelPath": "/chartLabels",
          "title": "Outages comparison by regions"
        }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "bar-chart-view",
      "path": "/",
      "contents": [
        {{
          "key": "chartData",
          "valueMap": [
            {{ "key": "0", "valueNumber": 150 }},
            {{ "key": "1", "valueNumber": 200 }},
            {{ "key": "2", "valueNumber": 100 }},
            {{ "key": "3", "valueNumber": 300 }}
          ]
        }},
        {{
          "key": "chartLabels",
          "valueMap": [
            {{ "key": "0", "valueString": "Q1" }},
            {{ "key": "1", "valueString": "Q2" }},
            {{ "key": "2", "valueString": "Q3" }},
            {{ "key": "3", "valueString": "Q4" }}
          ]
        }}
      ]
    }}
  }}
]"""
