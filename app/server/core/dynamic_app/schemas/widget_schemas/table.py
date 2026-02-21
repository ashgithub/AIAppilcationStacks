WIDGET_NAME = "OutageTable"
WIDGET_DESCRIPTION = "component designed to display tabular data for outages with columns for ID, location, status, severity, start time, estimated restoration, and affected customers. Requires array of outage record objects."
WIDGET_SCHEMA = """
[
  {{ "beginRendering": {{ "surfaceId": "outage-table-view","root": "main-container" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "outage-table-view",
      "components": [
        {{ "id": "main-container", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "outage-table"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Active Outages" }} }} }} }},
        {{ "id": "outage-table", "component": {{ "OutageTable": {{
          "dataPath": "/outageData",
          "title": "Active Outages"
        }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "outage-table-view",
      "path": "/",
      "contents": [
        {{
          "key": "outageData",
          "valueMap": [
            {{
              "key": "0",
              "valueMap": [
                {{ "key": "id", "valueString": "OUT-2026-0218" }},
                {{ "key": "location", "valueString": "Downtown District" }},
                {{ "key": "status", "valueString": "Active" }},
                {{ "key": "severity", "valueString": "Critical" }},
                {{ "key": "startTime", "valueString": "2026-02-18T08:30:00" }},
                {{ "key": "estimatedRestoration", "valueString": "2026-02-18T14:00:00" }},
                {{ "key": "affectedCustomers", "valueNumber": 12500 }}
              ]
            }},
            {{
              "key": "1",
              "valueMap": [
                {{ "key": "id", "valueString": "OUT-2026-0217" }},
                {{ "key": "location", "valueString": "Industrial Park" }},
                {{ "key": "status", "valueString": "Investigating" }},
                {{ "key": "severity", "valueString": "High" }},
                {{ "key": "startTime", "valueString": "2026-02-17T22:15:00" }},
                {{ "key": "estimatedRestoration", "valueString": "2026-02-18T10:00:00" }},
                {{ "key": "affectedCustomers", "valueNumber": 4200 }}
              ]
            }},
            {{
              "key": "2",
              "valueMap": [
                {{ "key": "id", "valueString": "OUT-2026-0215" }},
                {{ "key": "location", "valueString": "Riverside Area" }},
                {{ "key": "status", "valueString": "Scheduled" }},
                {{ "key": "severity", "valueString": "Low" }},
                {{ "key": "startTime", "valueString": "2026-02-20T06:00:00" }},
                {{ "key": "estimatedRestoration", "valueString": "2026-02-20T12:00:00" }},
                {{ "key": "affectedCustomers", "valueNumber": 850 }}
              ]
            }},
            {{
              "key": "3",
              "valueMap": [
                {{ "key": "id", "valueString": "OUT-2026-0214" }},
                {{ "key": "location", "valueString": "North Suburbs" }},
                {{ "key": "status", "valueString": "Resolved" }},
                {{ "key": "severity", "valueString": "Medium" }},
                {{ "key": "startTime", "valueString": "2026-02-16T13:45:00" }},
                {{ "key": "estimatedRestoration", "valueString": "2026-02-16T18:30:00" }},
                {{ "key": "affectedCustomers", "valueNumber": 2100 }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""