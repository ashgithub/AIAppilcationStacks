import textwrap

GRAPH_SCHEMA_DESCRIPTION = textwrap.dedent(
    """
    You are an expert Oracle SQL generator for property graphs using PGQL. The user asks questions about
    the outage_network property graph, which represents the electrical grid infrastructure and outages:

    Vertices (Nodes):
      • SUBSTATION(id, name, code, latitude, longitude, capacity_mva, status)
      • CIRCUIT(id, circuit_name, circuit_code, voltage_kv, customers_served, avg_load_mw, peak_load_mw, neighborhood)
      • ASSET(id, asset_id, asset_type, condition_score, health_index, status, criticality, latitude, longitude, next_maintenance_due)
      • CUSTOMER(id, account_number, name, customer_type, sla_priority, avg_monthly_usage_kwh, latitude, longitude)
      • OUTAGE(id, incident_code, cause_category, weather_condition, customers_affected, duration_minutes, saidi_minutes, safi_count, start_time, end_time)
      • WORK_ORDER(id, work_type, priority, status, labor_hours, material_cost, created_time, completed_time)
      • DOCUMENT(id, document_type, title, tags, source, author, document_date)

    Edges (Relationships):
      • ORIGINATES_FROM: substations -> circuits (circuits originate from substations)
      • LOCATED_ON: circuits -> assets (assets are located on circuits)
      • SERVED_BY: circuits -> customers (customers are served by circuits)
      • AFFECTED: outages -> circuits (outages affect circuits)
      • CAUSED_BY: outages -> assets (outages are caused by assets)
      • ADDRESSES: work_orders -> outages (work orders address outages)
      • SERVICES: work_orders -> assets (work orders service assets)
      • REFERENCES_OUTAGE: documents -> outages (documents reference outages)
      • REFERENCES_ASSET: documents -> assets (documents reference assets)

    The graph represents the electrical grid infrastructure, customer connections, outage incidents, maintenance work, and related documentation.

    Use graph_table function with PGQL MATCH syntax for queries on the outage_network graph. Always return valid SQL only. Your output will be directly fed to the Oracle database.
    Do not include backquotes.

    The examples below are for reference only - they demonstrate general PGQL patterns.
    The actual database schema and data is provided above on DB description.
    """
)

GRAPH_FEW_SHOT_EXAMPLES = [
    {
        "q": "How many cities are in the transportation graph?",
        "pgql": (
            "SELECT COUNT(*)\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (c IS City)\n"
            "  COLUMNS (c.id)\n"
            ");"
        ),
    },
    {
        "q": "Find all routes departing from a specific city",
        "pgql": (
            "SELECT route_name, city_name\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (c IS City) -[IS DEPARTS_FROM]-> (r IS Route)\n"
            "  WHERE c.name = 'New York'\n"
            "  COLUMNS (r.name AS route_name, c.name AS city_name)\n"
            ");"
        ),
    },
    {
        "q": "Find vehicles operating on routes from specific cities",
        "pgql": (
            "SELECT vehicle_type, route_name, city_name\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (c IS City) -[IS DEPARTS_FROM]-> (r IS Route) -[IS OPERATES_ON]-> (v IS Vehicle)\n"
            "  WHERE c.name = 'Los Angeles'\n"
            "  COLUMNS (v.type AS vehicle_type, r.name AS route_name, c.name AS city_name)\n"
            ");"
        ),
    },
    {
        "q": "Count routes originating from each city",
        "pgql": (
            "SELECT city_name, COUNT(DISTINCT route_id) AS route_count\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (c IS City) -[IS DEPARTS_FROM]-> (r IS Route)\n"
            "  COLUMNS (c.name AS city_name, r.id AS route_id)\n"
            ")\n"
            "GROUP BY city_name\n"
            "ORDER BY route_count DESC;"
        ),
    },
    {
        "q": "Find cities connected through shared routes",
        "pgql": (
            "SELECT DISTINCT city1, city2, shared_route\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (c1 IS City) -[IS DEPARTS_FROM]-> (r IS Route) <-[IS ARRIVES_AT]- (c2 IS City)\n"
            "  WHERE c1.id != c2.id\n"
            "  COLUMNS (c1.name AS city1, c2.name AS city2, r.name AS shared_route)\n"
            ");"
        ),
    },
    {
        "q": "Find authors who collaborated on the same paper",
        "pgql": (
            "SELECT DISTINCT author1, author2, paper_title\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (a1 IS Author) -[IS AUTHORED]-> (p IS Paper) <-[IS AUTHORED]- (a2 IS Author)\n"
            "  WHERE a1.id != a2.id\n"
            "  COLUMNS (a1.name AS author1, a2.name AS author2, p.title AS paper_title)\n"
            ");"
        ),
    },
    {
        "q": "Find papers presented at conferences by their authors",
        "pgql": (
            "SELECT paper_title, conference_name, author_name\n"
            "FROM graph_table (graph_name\n"
            "  MATCH (a IS Author) -[IS AUTHORED]-> (p IS Paper),\n"
            "        (p) -[IS PRESENTED_AT]-> (conf IS Conference)\n"
            "  COLUMNS (p.title AS paper_title, conf.name AS conference_name, a.name AS author_name)\n"
            ");"
        ),
    },
]
