def get_sample_payload(self)->str:
        return """
Here's a dynamic dashboard visualizing the outage, energy, and industry data using a table for outages, a map for locations, and bar graphs for comparisons.
---a2ui_JSON---
[
  {
    "beginRendering": {
      "surfaceId": "test-dashboard",
      "root": "main-container",
      "styles": {
        "font": "Arial",
        "primaryColor": "#007bff"
      }
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "test-dashboard",
      "components": [
        {
          "id": "main-container",
          "component": {
            "Column": {
              "children": {
                "explicitList": ["title", "kpi-row", "bar-chart", "line-chart", "outage-table", "map-component", "timeline-component"]
              }
            }
          }
        },
        {
          "id": "title",
          "component": {
            "Text": {
              "text": { "literalString": "A2UI Components Test Dashboard" },
              "usageHint": "h2"
            }
          }
        },
        {
          "id": "kpi-row",
          "component": {
            "Row": {
              "children": {
                "explicitList": ["kpi-1", "kpi-2", "kpi-3", "kpi-4"]
              },
              "distribution": "spaceEvenly",
              "alignment": "stretch"
            }
          }
        },
        {
          "id": "kpi-1",
          "weight": 1,
          "component": {
            "KpiCard": {
              "dataPath": "/kpi/activeOutages"
            }
          }
        },
        {
          "id": "kpi-2",
          "weight": 1,
          "component": {
            "KpiCard": {
              "dataPath": "/kpi/customersAffected"
            }
          }
        },
        {
          "id": "kpi-3",
          "weight": 1,
          "component": {
            "KpiCard": {
              "dataPath": "/kpi/avgResolutionTime"
            }
          }
        },
        {
          "id": "kpi-4",
          "weight": 1,
          "component": {
            "KpiCard": {
              "dataPath": "/kpi/systemUptime"
            }
          }
        },
        {
          "id": "bar-chart",
          "component": {
            "BarGraph": {
              "dataPath": "/chartData",
              "labelPath": "/chartLabels"
            }
          }
        },
        {
          "id": "line-chart",
          "component": {
            "LineGraph": {
              "labelPath": "/lineLabels",
              "seriesPath": "/lineSeries",
              "showPoints": true,
              "showArea": true,
              "animated": true
            }
          }
        },
        {
          "id": "map-component",
          "component": {
            "MapComponent": {
              "dataPath": "/mapData",
              "centerLat": 40.7128,
              "centerLng": -74.0060,
              "zoom": 10
            }
          }
        },
        {
          "id": "timeline-component",
          "component": {
            "TimelineComponent": {
              "dataPath": "/timelineData"
            }
          }
        },
        {
          "id": "outage-table",
          "component": {
            "OutageTable": {
              "dataPath": "/outageData",
              "title": "Active Outages"
            }
          }
        }
      ]
    }
  },
  {
    "dataModelUpdate": {
      "surfaceId": "test-dashboard",
      "path": "/",
      "contents": [
        {
          "key": "kpi",
          "valueMap": [
            {
              "key": "activeOutages",
              "valueMap": [
                { "key": "label", "valueString": "Active Outages" },
                { "key": "value", "valueNumber": 3 },
                { "key": "icon", "valueString": "warning" },
                { "key": "change", "valueNumber": -25 },
                { "key": "changeLabel", "valueString": "vs yesterday" },
                { "key": "color", "valueString": "coral" }
              ]
            },
            {
              "key": "customersAffected",
              "valueMap": [
                { "key": "label", "valueString": "Customers Affected" },
                { "key": "value", "valueNumber": 17550 },
                { "key": "icon", "valueString": "warning" },
                { "key": "change", "valueNumber": -12 },
                { "key": "changeLabel", "valueString": "vs yesterday" },
                { "key": "color", "valueString": "yellow" }
              ]
            },
            {
              "key": "avgResolutionTime",
              "valueMap": [
                { "key": "label", "valueString": "Avg Resolution Time" },
                { "key": "value", "valueNumber": 4.2 },
                { "key": "unit", "valueString": "hrs" },
                { "key": "icon", "valueString": "warning" },
                { "key": "change", "valueNumber": 8 },
                { "key": "changeLabel", "valueString": "vs last week" },
                { "key": "color", "valueString": "teal" }
              ]
            },
            {
              "key": "systemUptime",
              "valueMap": [
                { "key": "label", "valueString": "System Uptime" },
                { "key": "value", "valueNumber": 99.7 },
                { "key": "unit", "valueString": "%" },
                { "key": "icon", "valueString": "warning" },
                { "key": "change", "valueNumber": 0.2 },
                { "key": "changeLabel", "valueString": "vs last month" },
                { "key": "color", "valueString": "cyan" }
              ]
            }
          ]
        },
        {
          "key": "chartData",
          "valueMap": [
            { "key": "0", "valueNumber": 150 },
            { "key": "1", "valueNumber": 200 },
            { "key": "2", "valueNumber": 100 },
            { "key": "3", "valueNumber": 300 }
          ]
        },
        {
          "key": "chartLabels",
          "valueMap": [
            { "key": "0", "valueString": "Q1" },
            { "key": "1", "valueString": "Q2" },
            { "key": "2", "valueString": "Q3" },
            { "key": "3", "valueString": "Q4" }
          ]
        },
        {
          "key": "lineLabels",
          "valueMap": [
            { "key": "0", "valueString": "Jan" },
            { "key": "1", "valueString": "Feb" },
            { "key": "2", "valueString": "Mar" },
            { "key": "3", "valueString": "Apr" },
            { "key": "4", "valueString": "May" },
            { "key": "5", "valueString": "Jun" }
          ]
        },
        {
          "key": "lineSeries",
          "valueMap": [
            {
              "key": "0",
              "valueMap": [
                { "key": "name", "valueString": "Revenue" },
                { "key": "color", "valueString": "#00D4FF" },
                {
                  "key": "values",
                  "valueMap": [
                    { "key": "0", "valueNumber": 45 },
                    { "key": "1", "valueNumber": 62 },
                    { "key": "2", "valueNumber": 58 },
                    { "key": "3", "valueNumber": 85 },
                    { "key": "4", "valueNumber": 78 },
                    { "key": "5", "valueNumber": 95 }
                  ]
                }
              ]
            },
            {
              "key": "1",
              "valueMap": [
                { "key": "name", "valueString": "Expenses" },
                { "key": "color", "valueString": "#FF6B6B" },
                {
                  "key": "values",
                  "valueMap": [
                    { "key": "0", "valueNumber": 30 },
                    { "key": "1", "valueNumber": 42 },
                    { "key": "2", "valueNumber": 35 },
                    { "key": "3", "valueNumber": 55 },
                    { "key": "4", "valueNumber": 48 },
                    { "key": "5", "valueNumber": 60 }
                  ]
                }
              ]
            },
            {
              "key": "2",
              "valueMap": [
                { "key": "name", "valueString": "Profit" },
                { "key": "color", "valueString": "#4ECDC4" },
                {
                  "key": "values",
                  "valueMap": [
                    { "key": "0", "valueNumber": 15 },
                    { "key": "1", "valueNumber": 20 },
                    { "key": "2", "valueNumber": 23 },
                    { "key": "3", "valueNumber": 30 },
                    { "key": "4", "valueNumber": 30 },
                    { "key": "5", "valueNumber": 35 }
                  ]
                }
              ]
            }
          ]
        },
        {
          "key": "mapData",
          "valueMap": [
            {
              "key": "0",
              "valueMap": [
                { "key": "name", "valueString": "New York" },
                { "key": "latitude", "valueNumber": 40.7128 },
                { "key": "longitude", "valueNumber": -74.0060 },
                { "key": "description", "valueString": "The Big Apple" }
              ]
            },
            {
              "key": "1",
              "valueMap": [
                { "key": "name", "valueString": "Boston" },
                { "key": "latitude", "valueNumber": 42.3601 },
                { "key": "longitude", "valueNumber": -71.0589 },
                { "key": "description", "valueString": "Historic city" }
              ]
            }
          ]
        },
        {
          "key": "timelineData",
          "valueMap": [
            {
              "key": "0",
              "valueMap": [
                { "key": "date", "valueString": "2023-01-15" },
                { "key": "title", "valueString": "Project Start" },
                { "key": "description", "valueString": "Initial project kickoff" },
                { "key": "category", "valueString": "Planning" }
              ]
            },
            {
              "key": "1",
              "valueMap": [
                { "key": "date", "valueString": "2023-06-01" },
                { "key": "title", "valueString": "First Release" },
                { "key": "description", "valueString": "Beta version released" },
                { "key": "category", "valueString": "Release" }
              ]
            }
          ]
        },
        {
          "key": "outageData",
          "valueMap": [
            {
              "key": "0",
              "valueMap": [
                { "key": "id", "valueString": "OUT-2026-0218" },
                { "key": "location", "valueString": "Downtown District" },
                { "key": "status", "valueString": "Active" },
                { "key": "severity", "valueString": "Critical" },
                { "key": "startTime", "valueString": "2026-02-18T08:30:00" },
                { "key": "estimatedRestoration", "valueString": "2026-02-18T14:00:00" },
                { "key": "affectedCustomers", "valueNumber": 12500 }
              ]
            },
            {
              "key": "1",
              "valueMap": [
                { "key": "id", "valueString": "OUT-2026-0217" },
                { "key": "location", "valueString": "Industrial Park" },
                { "key": "status", "valueString": "Investigating" },
                { "key": "severity", "valueString": "High" },
                { "key": "startTime", "valueString": "2026-02-17T22:15:00" },
                { "key": "estimatedRestoration", "valueString": "2026-02-18T10:00:00" },
                { "key": "affectedCustomers", "valueNumber": 4200 }
              ]
            },
            {
              "key": "2",
              "valueMap": [
                { "key": "id", "valueString": "OUT-2026-0215" },
                { "key": "location", "valueString": "Riverside Area" },
                { "key": "status", "valueString": "Scheduled" },
                { "key": "severity", "valueString": "Low" },
                { "key": "startTime", "valueString": "2026-02-20T06:00:00" },
                { "key": "estimatedRestoration", "valueString": "2026-02-20T12:00:00" },
                { "key": "affectedCustomers", "valueNumber": 850 }
              ]
            },
            {
              "key": "3",
              "valueMap": [
                { "key": "id", "valueString": "OUT-2026-0214" },
                { "key": "location", "valueString": "North Suburbs" },
                { "key": "status", "valueString": "Resolved" },
                { "key": "severity", "valueString": "Medium" },
                { "key": "startTime", "valueString": "2026-02-16T13:45:00" },
                { "key": "estimatedRestoration", "valueString": "2026-02-16T18:30:00" },
                { "key": "affectedCustomers", "valueNumber": 2100 }
              ]
            }
          ]
        }
      ]
    }
  }
]
"""