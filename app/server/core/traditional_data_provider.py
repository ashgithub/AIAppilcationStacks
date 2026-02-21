"""Data provider for traditional application - contains comprehensive data independently"""

# Outage data for traditional application
OUTAGE_DATA = {
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

# Energy data for traditional application
ENERGY_DATA = {
    "consumption": {
        "total_mwh": 850000,
        "by_source": {
            "renewable": 420000,
            "fossil": 380000,
            "nuclear": 50000
        }
    },
    "production": {
        "total_mwh": 880000,
        "by_type": {
            "solar": 180000,
            "wind": 150000,
            "hydro": 120000,
            "coal": 200000,
            "natural_gas": 180000,
            "nuclear": 50000
        }
    },
    "efficiency_metrics": {
        "grid_efficiency": 94.2,
        "renewable_percentage": 49.5
    }
}

# Industry data for traditional application
INDUSTRY_DATA = {
    "industries": [
        {
            "name": "Manufacturing",
            "production_index": 112.5,
            "employment": 125000,
            "growth_rate": 3.2,
            "key_metrics": {
                "output_value": 450000000,
                "efficiency_score": 87.3
            }
        },
        {
            "name": "Technology",
            "production_index": 145.8,
            "employment": 98000,
            "growth_rate": 8.7,
            "key_metrics": {
                "output_value": 380000000,
                "efficiency_score": 92.1
            }
        },
        {
            "name": "Healthcare",
            "production_index": 118.3,
            "employment": 156000,
            "growth_rate": 4.1,
            "key_metrics": {
                "output_value": 520000000,
                "efficiency_score": 89.5
            }
        },
        {
            "name": "Energy",
            "production_index": 108.9,
            "employment": 67000,
            "growth_rate": 2.8,
            "key_metrics": {
                "output_value": 290000000,
                "efficiency_score": 85.7
            }
        },
        {
            "name": "Transportation",
            "production_index": 115.2,
            "employment": 89000,
            "growth_rate": 3.9,
            "key_metrics": {
                "output_value": 340000000,
                "efficiency_score": 88.2
            }
        }
    ],
    "overall_metrics": {
        "total_employment": 535000,
        "average_growth": 4.5,
        "top_performing_industry": "Technology"
    }
}

async def get_traditional_outage_data():
    """Get traditional outage data - independent from other applications"""
    # Return a copy to prevent external modifications
    import json
    return json.loads(json.dumps(OUTAGE_DATA))

async def get_traditional_energy_data():
    """Get traditional energy data - independent from other applications"""
    import json
    return json.loads(json.dumps(ENERGY_DATA))

async def get_traditional_industry_data():
    """Get traditional industry data - independent from other applications"""
    import json
    return json.loads(json.dumps(INDUSTRY_DATA))
