WIDGET_NAME = "KpiCard"
WIDGET_DESCRIPTION = "component designed to display key performance indicators in card format with values, labels, icons, and change indicators. Requires KPI data with label, value, and optional unit, change, icon, and color fields."
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "kpi-dashboard","root": "main-container" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "kpi-dashboard",
      "components": [
        {{ "id": "main-container", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "kpi-row"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Key Performance Indicators" }} }} }} }},
        {{ "id": "kpi-row", "component": {{ "Row": {{
          "children": {{ "explicitList": ["kpi-1", "kpi-2", "kpi-3", "kpi-4"] }},
          "distribution": "spaceEvenly",
          "alignment": "stretch"
        }} }} }},
        {{ "id": "kpi-1", "weight": 1, "component": {{ "KpiCard": {{ "dataPath": "/kpi/activeOutages" }} }} }},
        {{ "id": "kpi-2", "weight": 1, "component": {{ "KpiCard": {{ "dataPath": "/kpi/customersAffected" }} }} }},
        {{ "id": "kpi-3", "weight": 1, "component": {{ "KpiCard": {{ "dataPath": "/kpi/avgResolutionTime" }} }} }},
        {{ "id": "kpi-4", "weight": 1, "component": {{ "KpiCard": {{ "dataPath": "/kpi/systemUptime" }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "kpi-dashboard",
      "path": "/",
      "contents": [
        {{
          "key": "kpi",
          "valueMap": [
            {{
              "key": "activeOutages",
              "valueMap": [
                {{ "key": "label", "valueString": "Active Outages" }},
                {{ "key": "value", "valueNumber": 3 }},
                {{ "key": "icon", "valueString": "warning" }},
                {{ "key": "change", "valueNumber": -25 }},
                {{ "key": "changeLabel", "valueString": "vs yesterday" }},
                {{ "key": "color", "valueString": "coral" }}
              ]
            }},
            {{
              "key": "customersAffected",
              "valueMap": [
                {{ "key": "label", "valueString": "Customers Affected" }},
                {{ "key": "value", "valueNumber": 17550 }},
                {{ "key": "icon", "valueString": "users" }},
                {{ "key": "change", "valueNumber": -12 }},
                {{ "key": "changeLabel", "valueString": "vs yesterday" }},
                {{ "key": "color", "valueString": "yellow" }}
              ]
            }},
            {{
              "key": "avgResolutionTime",
              "valueMap": [
                {{ "key": "label", "valueString": "Avg Resolution Time" }},
                {{ "key": "value", "valueNumber": 4.2 }},
                {{ "key": "unit", "valueString": "hrs" }},
                {{ "key": "icon", "valueString": "clock" }},
                {{ "key": "change", "valueNumber": 8 }},
                {{ "key": "changeLabel", "valueString": "vs last week" }},
                {{ "key": "color", "valueString": "teal" }}
              ]
            }},
            {{
              "key": "systemUptime",
              "valueMap": [
                {{ "key": "label", "valueString": "System Uptime" }},
                {{ "key": "value", "valueNumber": 99.7 }},
                {{ "key": "unit", "valueString": "%" }},
                {{ "key": "icon", "valueString": "check" }},
                {{ "key": "change", "valueNumber": 0.2 }},
                {{ "key": "changeLabel", "valueString": "vs last month" }},
                {{ "key": "color", "valueString": "cyan" }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""