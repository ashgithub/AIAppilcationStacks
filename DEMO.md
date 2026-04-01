## Demo queries

Current sample demo queries to call the different agent and LLM modes of the application
Descriptions include general output responses and which use cases they cover.

This is just a sample, other queries are also supported.

### Stand alone *LLM application*

1. Relational DB queries:
    - Which work orders are still open and their associated asset types?
    - List assets that are currently in overwatch condition (condition_score < 4)
    - Show circuits with their substation names and total customers served, ordered by customer count
    - Find outages that lasted more than 2 hours and their associated root cause assets
2. RAG queries:
    - What are the EPA recommended actions for power outages in the US?
    - What immediate steps should be taken during a widespread power outage according to US guidelines?
    - Which are the protocols followed by mexican regulations for ambiental disaster attention?
3. DB + RAG queries (mixed):
    - Look for the outages in residential areas, and then explain, what recovery procedures does the disaster manual recommend?
    - Compare average outage duration by cause category and reference relevant EPA guidelines

### Stand alone *Agent application*

1. Graph DB queries:
    - Visualize substation locations with capacity indicators
    - Display asset health distribution by condition score, include names if possible.
2. RAG queries:
    - How do disaster response manuals address communication during outages?
    - Create a timeline visualization of FEMA assistance steps for electrical outages
    - Give me some diagrams on how can we identify and evaluate risks according to mexican guidelines?
3. DB + RAG queries (mixed):
    - Map the outage locations and show also EPA recommended response zones
    - Generate a dashboard showing work order priorities with referenced manual safety protocols

### Side by side comparison

1. Relational DB queries:
    - What are the most common outage cause categories in the last 6 months?
    - Find circuits with the highest number of customers served
    - Show me the location of the main substations and circuits with characteristics.
2. RAG queries:
    - What immediate steps should be taken during a widespread power outage according to US guidelines?
    - What procedures are outlined in the Mexican disaster manual for infrastructure recovery compared to EPA and FEMA available procedures?
    - what are the recommended attencion guidelines for earthquakes at mexico?
3. DB + RAG queries (mixed):
    - Compare outage resolution times for circuits originating from different substations, and what the disaster manual says about response times
    - Analyze customer complaints by outage category and correlate with FEMA assistance guidelines
    - Show asset maintenance schedules alongside safety protocol requirements from manuals