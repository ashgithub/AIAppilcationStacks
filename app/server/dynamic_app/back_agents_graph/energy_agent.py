import json
from langchain.tools import tool


@tool()
async def get_energy_data() -> str:
    """Get energy consumption and production statistics.

    Returns:
        JSON string containing energy data including consumption by source,
        production by type, and efficiency metrics.
    """
    energy_data = {
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

    return json.dumps(energy_data, indent=2)