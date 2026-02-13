import json
from langchain.tools import tool


@tool()
async def get_outage_data() -> str:
    """Get current power outage information and statistics.

    Returns:
        JSON string containing outage data including locations, times, affected customers, and causes.
    """
    outage_data = {
        "outages": [
            {
                "location": "Downtown Seattle, WA",
                "start_time": "2024-02-12 14:30",
                "estimated_restoration": "2024-02-12 18:00",
                "affected_customers": 2500,
                "cause": "Transformer failure due to storm damage"
            },
            {
                "location": "Portland Suburb, OR",
                "start_time": "2024-02-12 13:15",
                "estimated_restoration": "2024-02-12 16:30",
                "affected_customers": 1800,
                "cause": "Tree branch on power lines"
            },
            {
                "location": "San Francisco Bay Area, CA",
                "start_time": "2024-02-12 12:00",
                "estimated_restoration": "2024-02-12 15:00",
                "affected_customers": 3200,
                "cause": "Equipment malfunction"
            },
            {
                "location": "Los Angeles Downtown, CA",
                "start_time": "2024-02-12 11:45",
                "estimated_restoration": "2024-02-12 14:30",
                "affected_customers": 4100,
                "cause": "Cable damage during construction"
            }
        ],
        "total_outages": 4,
        "total_affected": 11600
    }

    return json.dumps(outage_data, indent=2)