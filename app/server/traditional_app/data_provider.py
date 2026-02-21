""" this file is for giving the client side the information about outages """
from core.traditional_data_provider import (
    get_traditional_outage_data,
    get_traditional_energy_data,
    get_traditional_industry_data
)

# Hardcoded coordinates for locations (lat, lng)
LOCATION_COORDINATES = {
    "Downtown Seattle, WA": (47.6062, -122.3321),
    "Portland Suburb, OR": (45.5152, -122.6784),
    "San Francisco Bay Area, CA": (37.7749, -122.4194),
    "Los Angeles Downtown, CA": (34.0522, -118.2437)
}

async def get_traditional_outage_messages():
    """Get formatted initial outage data as A2A ServerToClientMessage array"""

    data = await get_traditional_outage_data()

    outages = data["outages"]
    total_outages = data["total_outages"]

    outage_summary = [
        {"key": "0", "valueNumber": total_outages},
        {"key": "1", "valueNumber": 0},
        {"key": "2", "valueNumber": 0},
        {"key": "3", "valueNumber": 0}  
    ]

    outage_summary_labels = [
        {"key": "0", "valueString": "Active"},
        {"key": "1", "valueString": "Investigating"},
        {"key": "2", "valueString": "Resolved"},
        {"key": "3", "valueString": "Scheduled"}
    ]

    outage_table = []
    map_markers = []

    for i, outage in enumerate(outages):
        outage_id = f"OUT-{str(i+1).zfill(3)}"

        outage_table.append({
            "key": str(i),
            "valueMap": [
                {"key": "id", "valueString": outage_id},
                {"key": "location", "valueString": outage["location"]},
                {"key": "status", "valueString": "Active"},
                {"key": "severity", "valueString": "High"},  # Default severity
                {"key": "startTime", "valueString": outage["start_time"]},
                {"key": "estimatedRestoration", "valueString": outage["estimated_restoration"]},
                {"key": "affectedCustomers", "valueNumber": outage["affected_customers"]}
            ]
        })

        lat, lng = LOCATION_COORDINATES.get(outage["location"], (40.7589, -73.9851))
        map_markers.append({
            "key": str(i),
            "valueMap": [
                {"key": "name", "valueString": outage["location"]},
                {"key": "latitude", "valueNumber": lat},
                {"key": "longitude", "valueNumber": lng},
                {"key": "description", "valueString": f"Active outage affecting {outage['affected_customers']} customers"}
            ]
        })

    energy_data = await get_traditional_energy_data()

    energy_kpis = [
        {"key": "total", "valueMap": [
            {"key": "label", "valueString": "Total Consumption"},
            {"key": "value", "valueNumber": energy_data["consumption"]["total_mwh"]},
            {"key": "unit", "valueString": "MWh"},
            {"key": "icon", "valueString": "bolt"}
        ]},
        {"key": "renewable", "valueMap": [
            {"key": "label", "valueString": "Renewable"},
            {"key": "value", "valueNumber": energy_data["consumption"]["by_source"]["renewable"]},
            {"key": "unit", "valueString": "MWh"},
            {"key": "icon", "valueString": "energy"}
        ]},
        {"key": "fossil", "valueMap": [
            {"key": "label", "valueString": "Fossil Fuels"},
            {"key": "value", "valueNumber": energy_data["consumption"]["by_source"]["fossil"]},
            {"key": "unit", "valueString": "MWh"},
            {"key": "icon", "valueString": "factory"}
        ]},
        {"key": "nuclear", "valueMap": [
            {"key": "label", "valueString": "Nuclear"},
            {"key": "value", "valueNumber": energy_data["consumption"]["by_source"]["nuclear"]},
            {"key": "unit", "valueString": "MWh"},
            {"key": "icon", "valueString": "power"}
        ]}
    ]

    messages = [
        {
            "dataModelUpdate": {
                "surfaceId": "default",
                "path": "/",
                "contents": [
                    {
                        "key": "outageSummary",
                        "valueMap": outage_summary
                    },
                    {
                        "key": "outageSummaryLabels",
                        "valueMap": outage_summary_labels
                    },
                    {
                        "key": "outageTable",
                        "valueMap": outage_table
                    },
                    {
                        "key": "mapMarkers",
                        "valueMap": map_markers
                    },
                    {
                        "key": "energyKPIs",
                        "valueMap": energy_kpis
                    }
                ]
            }
        }
    ]

    return messages

async def get_traditional_energy_trends_messages():
    """Get formatted energy trends data as A2A ServerToClientMessage array"""
    energy_data = await get_traditional_energy_data()

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    base_production = energy_data["production"]
    energy_trend = [
        {"key": "solar", "valueMap": [
            {"key": "name", "valueString": "Solar"},
            {"key": "color", "valueString": "#FFE66D"},
            {"key": "values", "valueMap": [
                {"key": "0", "valueNumber": int(base_production["by_type"]["solar"] * 0.8)},
                {"key": "1", "valueNumber": int(base_production["by_type"]["solar"] * 0.9)},
                {"key": "2", "valueNumber": int(base_production["by_type"]["solar"] * 1.1)},
                {"key": "3", "valueNumber": int(base_production["by_type"]["solar"] * 1.2)},
                {"key": "4", "valueNumber": int(base_production["by_type"]["solar"] * 1.3)},
                {"key": "5", "valueNumber": int(base_production["by_type"]["solar"] * 1.4)},
                {"key": "6", "valueNumber": int(base_production["by_type"]["solar"] * 1.5)},
                {"key": "7", "valueNumber": int(base_production["by_type"]["solar"] * 1.3)},
                {"key": "8", "valueNumber": int(base_production["by_type"]["solar"] * 1.1)},
                {"key": "9", "valueNumber": int(base_production["by_type"]["solar"] * 0.9)},
                {"key": "10", "valueNumber": int(base_production["by_type"]["solar"] * 0.8)},
                {"key": "11", "valueNumber": int(base_production["by_type"]["solar"] * 0.7)}
            ]}
        ]},
        {"key": "wind", "valueMap": [
            {"key": "name", "valueString": "Wind"},
            {"key": "color", "valueString": "#4ECDC4"},
            {"key": "values", "valueMap": [
                {"key": "0", "valueNumber": int(base_production["by_type"]["wind"] * 0.9)},
                {"key": "1", "valueNumber": int(base_production["by_type"]["wind"] * 0.95)},
                {"key": "2", "valueNumber": int(base_production["by_type"]["wind"] * 1.0)},
                {"key": "3", "valueNumber": int(base_production["by_type"]["wind"] * 1.05)},
                {"key": "4", "valueNumber": int(base_production["by_type"]["wind"] * 1.1)},
                {"key": "5", "valueNumber": int(base_production["by_type"]["wind"] * 1.15)},
                {"key": "6", "valueNumber": int(base_production["by_type"]["wind"] * 1.1)},
                {"key": "7", "valueNumber": int(base_production["by_type"]["wind"] * 1.05)},
                {"key": "8", "valueNumber": int(base_production["by_type"]["wind"] * 1.0)},
                {"key": "9", "valueNumber": int(base_production["by_type"]["wind"] * 0.95)},
                {"key": "10", "valueNumber": int(base_production["by_type"]["wind"] * 0.9)},
                {"key": "11", "valueNumber": int(base_production["by_type"]["wind"] * 0.85)}
            ]}
        ]},
        {"key": "hydro", "valueMap": [
            {"key": "name", "valueString": "Hydro"},
            {"key": "color", "valueString": "#00D4FF"},
            {"key": "values", "valueMap": [
                {"key": "0", "valueNumber": int(base_production["by_type"]["hydro"] * 0.85)},
                {"key": "1", "valueNumber": int(base_production["by_type"]["hydro"] * 0.9)},
                {"key": "2", "valueNumber": int(base_production["by_type"]["hydro"] * 0.95)},
                {"key": "3", "valueNumber": int(base_production["by_type"]["hydro"] * 1.0)},
                {"key": "4", "valueNumber": int(base_production["by_type"]["hydro"] * 1.05)},
                {"key": "5", "valueNumber": int(base_production["by_type"]["hydro"] * 1.1)},
                {"key": "6", "valueNumber": int(base_production["by_type"]["hydro"] * 1.0)},
                {"key": "7", "valueNumber": int(base_production["by_type"]["hydro"] * 0.95)},
                {"key": "8", "valueNumber": int(base_production["by_type"]["hydro"] * 0.9)},
                {"key": "9", "valueNumber": int(base_production["by_type"]["hydro"] * 0.85)},
                {"key": "10", "valueNumber": int(base_production["by_type"]["hydro"] * 0.8)},
                {"key": "11", "valueNumber": int(base_production["by_type"]["hydro"] * 0.75)}
            ]}
        ]}
    ]

    messages = [
        {
            "dataModelUpdate": {
                "surfaceId": "default",
                "path": "/trends",
                "contents": [
                    {
                        "key": "energyTrend",
                        "valueMap": energy_trend
                    },
                    {
                        "key": "energyTrendLabels",
                        "valueMap": [{"key": str(i), "valueString": month} for i, month in enumerate(months)]
                    }
                ]
            }
        }
    ]

    return messages

async def get_traditional_timeline_messages():
    """Get formatted timeline data as A2A ServerToClientMessage array"""

    data = await get_traditional_outage_data()

    outages = data["outages"]

    timeline_events = []

    for i, outage in enumerate(outages):
        timeline_events.append({
            "key": str(i),
            "valueMap": [
                {"key": "date", "valueString": outage["start_time"]},
                {"key": "title", "valueString": f"Outage Reported in {outage['location']}"},
                {"key": "description", "valueString": outage["cause"]}
            ]
        })

    messages = [
        {
            "dataModelUpdate": {
                "surfaceId": "default",
                "path": "/timeline",
                "contents": [
                    {
                        "key": "timelineEvents",
                        "valueMap": timeline_events
                    }
                ]
            }
        }
    ]

    return messages

async def get_traditional_energy_messages():
    """Get formatted energy data as A2A ServerToClientMessage array"""
    data = await get_traditional_energy_data()

    messages = [
        {
            "dataModelUpdate": {
                "surfaceId": "default",
                "path": "/",
                "contents": [
                    {
                        "key": "energyConsumption",
                        "valueMap": [
                            {"key": "total", "valueNumber": data["consumption"]["total_mwh"]},
                            {"key": "renewable", "valueNumber": data["consumption"]["by_source"]["renewable"]},
                            {"key": "fossil", "valueNumber": data["consumption"]["by_source"]["fossil"]},
                            {"key": "nuclear", "valueNumber": data["consumption"]["by_source"]["nuclear"]}
                        ]
                    },
                    {
                        "key": "energyProduction",
                        "valueMap": [
                            {"key": "total", "valueNumber": data["production"]["total_mwh"]},
                            {"key": "solar", "valueNumber": data["production"]["by_type"]["solar"]},
                            {"key": "wind", "valueNumber": data["production"]["by_type"]["wind"]},
                            {"key": "hydro", "valueNumber": data["production"]["by_type"]["hydro"]},
                            {"key": "coal", "valueNumber": data["production"]["by_type"]["coal"]},
                            {"key": "natural_gas", "valueNumber": data["production"]["by_type"]["natural_gas"]},
                            {"key": "nuclear", "valueNumber": data["production"]["by_type"]["nuclear"]}
                        ]
                    }
                ]
            }
        }
    ]

    return messages

async def get_traditional_industry_messages():
    """Get formatted industry data as A2A ServerToClientMessage array"""
    data = await get_traditional_industry_data()

    industry_table = []
    for i, industry in enumerate(data["industries"]):
        industry_table.append({
            "key": str(i),
            "valueMap": [
                {"key": "id", "valueString": industry["name"]},
                {"key": "location", "valueString": f"Production Index: {industry['production_index']}"},
                {"key": "status", "valueString": f"Employment: {industry['employment']}"},
                {"key": "severity", "valueString": f"Growth Rate: {industry['growth_rate']}"},
                {"key": "startTime", "valueString": f"Output Value: {industry['key_metrics']['output_value']}"},
                {"key": "estimatedRestoration", "valueString": f"Efficiency Score: {industry['key_metrics']['efficiency_score']}"},
                {"key": "affectedCustomers", "valueNumber": 0}
            ]
        })

    messages = [
        {
            "dataModelUpdate": {
                "surfaceId": "default",
                "path": "/industry",
                "contents": [
                    {
                        "key": "industryTable",
                        "valueMap": industry_table
                    },
                    {
                        "key": "industryMetrics",
                        "valueMap": [
                            {"key": "total_employment", "valueNumber": data["overall_metrics"]["total_employment"]},
                            {"key": "average_growth", "valueNumber": data["overall_metrics"]["average_growth"]},
                            {"key": "top_performing_industry", "valueString": data["overall_metrics"]["top_performing_industry"]}
                        ]
                    }
                ]
            }
        }
    ]

    return messages
