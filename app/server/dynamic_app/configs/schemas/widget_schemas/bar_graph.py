BAR_GRAPH_EXAMPLE = """
[
  {{ "beginRendering": {{ "surfaceId": "restaurant-view","root": "main-column" }} }},
  {{ "surfaceUpdate": {{
    "surfaceId": "restaurant-view",
      "components": [
        {{ "id": "main-column", "component": {{ "Column": {{ "children": {{ "explicitList": ["title", "restaurant-table"] }} }} }} }},
        {{ "id": "title","component": {{ "Text": {{ "usageHint": "h2", "text": {{ "literalString": "Restaurant Rating Bar Chart" }} }} }} }},
        {{ "id": "restaurant-table", "component": {{ "RestaurantBarChart": {{ "restaurants": {{ "path": "/restaurants" }} }} }} }}
      ]
    }}
  }},
  {{ "dataModelUpdate": {{
      "surfaceId": "restaurant-view",
      "path": "/",
      "contents": [
        {{
          "key": "restaurants",
          "valueMap": [
            {{
              "key": "restaurant-1",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Mario's Italian Kitchen"
                }},
                {{
                  "key": "cuisine",
                  "valueString": "Italian"
                }},
                {{
                  "key": "rating",
                  "valueNumber": 4.5
                }},
                {{
                  "key": "priceRange",
                  "valueString": "$$$"
                }},
                {{
                  "key": "description",
                  "valueString": "Authentic Italian cuisine with fresh pasta and wood-fired pizzas"
                }}
              ]
            }},
            {{
              "key": "restaurant-2",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Golden Dragon"
                }},
                {{
                  "key": "cuisine",
                  "valueString": "Chinese"
                }},
                {{
                  "key": "rating",
                  "valueNumber": 4.2
                }},
                {{
                  "key": "priceRange",
                  "valueString": "$$"
                }},
                {{
                  "key": "description",
                  "valueString": "Traditional Chinese dishes with a modern twist"
                }}
              ]
            }},
            {{
              "key": "restaurant-3",
              "valueMap": [
                {{
                  "key": "name",
                  "valueString": "Taco Fiesta"
                }},
                {{
                  "key": "cuisine",
                  "valueString": "Mexican"
                }},
                {{
                  "key": "rating",
                  "valueNumber": 4.8
                }},
                {{
                  "key": "priceRange",
                  "valueString": "$"
                }},
                {{
                  "key": "description",
                  "valueString": "Authentic Mexican street food and fresh ingredients"
                }}
              ]
            }}
          ]
        }}
      ]
    }}
  }}
]"""