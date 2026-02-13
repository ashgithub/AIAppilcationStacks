import json
from langchain.tools import tool


@tool()
async def get_industry_data() -> str:
    """Get industry performance and economic statistics.

    Returns:
        JSON string containing industry data including production indices,
        employment numbers, growth rates, and key metrics.
    """
    industry_data = {
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

    return json.dumps(industry_data, indent=2)