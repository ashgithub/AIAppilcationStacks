WIDGET_NAME = "LineGraph"
WIDGET_DESCRIPTION = "component designed to display line charts with multiple series, showing trends over time or categories. Requires x-axis labels and series data with names, colors, and value arrays."
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "line-chart-view","root": "main-container" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "line-chart-view",
      "components": [
        {{ "id": "main-container", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "line-chart"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Trend Analysis" }} }} }} }},
        {{ "id": "line-chart", "component": {{ "LineGraph": {{
          "labelPath": "/lineLabels",
          "seriesPath": "/lineSeries",
          "showPoints": true,
          "showArea": true,
          "animated": true
        }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "line-chart-view",
      "path": "/",
      "contents": [
        {{
          "key": "lineLabels",
          "valueMap": [
            {{ "key": "0", "valueString": "Jan" }},
            {{ "key": "1", "valueString": "Feb" }},
            {{ "key": "2", "valueString": "Mar" }},
            {{ "key": "3", "valueString": "Apr" }},
            {{ "key": "4", "valueString": "May" }},
            {{ "key": "5", "valueString": "Jun" }}
          ]
        }},
        {{
          "key": "lineSeries",
          "valueMap": [
            {{
              "key": "0",
              "valueMap": [
                {{ "key": "name", "valueString": "Revenue" }},
                {{ "key": "color", "valueString": "#00D4FF" }},
                {{
                  "key": "values",
                  "valueMap": [
                    {{ "key": "0", "valueNumber": 45 }},
                    {{ "key": "1", "valueNumber": 62 }},
                    {{ "key": "2", "valueNumber": 58 }},
                    {{ "key": "3", "valueNumber": 85 }},
                    {{ "key": "4", "valueNumber": 78 }},
                    {{ "key": "5", "valueNumber": 95 }}
                  ]
                }}
              ]
            }},
            {{
              "key": "1",
              "valueMap": [
                {{ "key": "name", "valueString": "Expenses" }},
                {{ "key": "color", "valueString": "#FF6B6B" }},
                {{
                  "key": "values",
                  "valueMap": [
                    {{ "key": "0", "valueNumber": 30 }},
                    {{ "key": "1", "valueNumber": 42 }},
                    {{ "key": "2", "valueNumber": 35 }},
                    {{ "key": "3", "valueNumber": 55 }},
                    {{ "key": "4", "valueNumber": 48 }},
                    {{ "key": "5", "valueNumber": 60 }}
                  ]
                }}
              ]
            }},
            {{
              "key": "2",
              "valueMap": [
                {{ "key": "name", "valueString": "Profit" }},
                {{ "key": "color", "valueString": "#4ECDC4" }},
                {{
                  "key": "values",
                  "valueMap": [
                    {{ "key": "0", "valueNumber": 15 }},
                    {{ "key": "1", "valueNumber": 20 }},
                    {{ "key": "2", "valueNumber": 23 }},
                    {{ "key": "3", "valueNumber": 30 }},
                    {{ "key": "4", "valueNumber": 30 }},
                    {{ "key": "5", "valueNumber": 35 }}
                  ]
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""