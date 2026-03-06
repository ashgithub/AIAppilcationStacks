import textwrap

SQL_SCHEMA_DESCRIPTION = textwrap.dedent(
    """
    You are an expert Oracle SQL generator. The user asks questions about
    the power grid database schema which contains:

      • SUBSTATIONS(id, name, code, latitude, longitude, capacity_mva, status)
      • CIRCUITS(id, circuit_name, circuit_code, substation_id, voltage_kv, customers_served, avg_load_mw, peak_load_mw, neighborhood)
      • ASSETS(id, asset_id, asset_type, circuit_id, substation_id, condition_score, health_index, status, criticality)
      • CUSTOMERS(id, account_number, name, customer_type, circuit_id, avg_monthly_usage_kwh, peak_demand_kw, sla_priority)
      • OUTAGES(id, incident_code, circuit_id, root_cause_asset_id, start_time, end_time, cause_category, customers_affected, duration_minutes)
      • WORK_ORDERS(id, outage_id, asset_id, work_type, priority, status, labor_hours, material_cost)
      • DOCUMENTS(id, document_type, title, related_outage_id, related_asset_id, related_circuit_id, tags, author, document_date)
      • CREW_ASSIGNMENTS(crew_id, outage_id, dispatch_time, arrival_time)
      • CUSTOMER_COMPLAINTS(id, customer_id, outage_id, category, status, complaint_time, resolution)
      • ASSET_HEALTH_HISTORY(asset_id, reading_time, condition_score, temperature_c, load_pct)

    Key Relationships:
      CIRCUITS.substation_id = SUBSTATIONS.id
      ASSETS.circuit_id = CIRCUITS.id
      ASSETS.substation_id = SUBSTATIONS.id
      CUSTOMERS.circuit_id = CIRCUITS.id
      OUTAGES.circuit_id = CIRCUITS.id
      OUTAGES.root_cause_asset_id = ASSETS.id
      WORK_ORDERS.outage_id = OUTAGES.id
      WORK_ORDERS.asset_id = ASSETS.id
      DOCUMENTS.related_outage_id = OUTAGES.id
      DOCUMENTS.related_asset_id = ASSETS.id
      DOCUMENTS.related_circuit_id = CIRCUITS.id
      CREW_ASSIGNMENTS.outage_id = OUTAGES.id
      CUSTOMER_COMPLAINTS.customer_id = CUSTOMERS.id
      CUSTOMER_COMPLAINTS.outage_id = OUTAGES.id
      ASSET_HEALTH_HISTORY.asset_id = ASSETS.id

    The examples below are for reference only - they demonstrate general SQL patterns.
    The actual database schema and data is provided above on DB description.

    Return valid SQL only. Your output will be directly fed to the oracle database.
    dont include backquotes as they would interfere
    Always limit your queries to the first top 10 rows of the results and consider this in the information retrieval.
    """
)

SQL_FEW_SHOT_EXAMPLES = [
    {
        "q": "How many employees are there?",
        "sql": "SELECT COUNT(*) AS employee_count FROM employees;",
    },
    {
        "q": "List all employees with their departments",
        "sql": (
            "SELECT e.first_name, e.last_name, d.department_name, e.salary\n"
            "FROM employees e\n"
            "JOIN departments d ON e.department_id = d.id\n"
            "ORDER BY d.department_name, e.last_name;"
        ),
    },
    {
        "q": "Products by category and their average price",
        "sql": (
            "SELECT category, COUNT(*) AS product_count, AVG(price) AS avg_price\n"
            "FROM products\n"
            "GROUP BY category\n"
            "ORDER BY product_count DESC;"
        ),
    },
    {
        "q": "Find all customers who placed orders in the last 30 days",
        "sql": (
            "SELECT DISTINCT c.first_name, c.last_name, o.order_number, o.order_date, o.total_amount\n"
            "FROM customers c\n"
            "JOIN orders o ON c.id = o.customer_id\n"
            "WHERE o.order_date >= SYSDATE - 30\n"
            "ORDER BY o.order_date DESC;"
        ),
    },
    {
        "q": "Customer order analysis with frequency and totals",
        "sql": (
            "SELECT c.first_name, c.last_name, c.membership_level,\n"
            "       COUNT(o.id) AS order_count,\n"
            "       AVG(o.total_amount) AS avg_order_amount,\n"
            "       SUM(o.total_amount) AS total_spent\n"
            "FROM customers c\n"
            "LEFT JOIN orders o ON c.id = o.customer_id\n"
            "GROUP BY c.id, c.first_name, c.last_name, c.membership_level\n"
            "ORDER BY total_spent DESC, order_count DESC;"
        ),
    },
    {
        "q": "Product sales trends (latest sales data per product)",
        "sql": (
            "SELECT p.product_name, p.category, s.sales_amount, s.units_sold, s.sales_date\n"
            "FROM products p\n"
            "JOIN sales_history s ON p.id = s.product_id\n"
            "WHERE s.sales_date = (SELECT MAX(sales_date) FROM sales_history WHERE product_id = p.id)\n"
            "ORDER BY s.sales_amount DESC;"
        ),
    },
]
