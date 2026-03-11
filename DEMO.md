## Demo queries

This file includes different options to test out the LLM and Agent applications alone or side by side, highlighting the difference and main strengths of each application.

### Stand alone *LLM application*

1. Relational DB queries:
    - Which work orders are still open and their associated asset types? (passed)
    - List assets that are currently in overwatch condition (condition_score < 4) (passed)
    - Show circuits with their substation names and total customers served, ordered by customer count (passed)
    - Find outages that lasted more than 2 hours and their associated root cause assets (passed)
2. RAG queries:
    - What are the EPA recommended actions for power outages in the US? (passed)
    - What immediate steps should be taken during a widespread power outage according to US guidelines? (passed)
    - Summarize key communication protocols from disaster response manuals during outages (passed)
3. DB + RAG queries (mixed):
    - Look for the outages in residential areas, and then explain, what recovery procedures does the disaster manual recommend? (passed)
    - Compare average outage duration by cause category and reference relevant EPA guidelines (passed)

### Stand alone *Agent application*

1. Graph DB queries:
    - Show me all substations and their capacity in descending order (poor results)
    - Visualize substation locations with capacity indicators (bar graph most)
    - Display asset health distribution by condition score, include names if possible. (bar grpah + dashboard)
2. RAG queries:
    - How do disaster response manuals address communication during outages? (text)
    - Create a timeline visualization of FEMA assistance steps for electrical outages (timeline most)
3. DB + RAG queries (mixed):
    - Map outage locations and overlay EPA recommended response zones (map dashboard)
    - Generate a dashboard showing work order priorities with referenced manual safety protocols (Not working - orchestrator decided not to call)

### Side by side comparison

1. Relational DB queries:
    - What are the most common outage cause categories in the last 6 months? (good text vs bar graph approach)
    - Find circuits with the highest number of customers served (agent fails on retrieve data sometimes)
    - location of the main substations and circuits
2. RAG queries:
    - What are the EPA recommended actions for power outages in the US? (Text vs text)
    - What immediate steps should be taken during a widespread power outage according to US guidelines? (text vs text)
3. DB + RAG queries (mixed):
    - Compare outage resolution times for circuits originating from different substations, and what the disaster manual says about response times (bar grpah vs md chart)
    - Analyze customer complaints by outage category and correlate with FEMA assistance guidelines (agent sometimes fails)
    - Show asset maintenance schedules alongside safety protocol requirements from manuals (agent missing to retrieve the right information)

### Queries to test
b. RAG-only queries:
   6. What are the EPA recommended actions for power outages in the US?
   7. How does FEMA assist with electrical outages?
   8. What procedures are outlined in the Mexican disaster manual for infrastructure recovery?
   9. What immediate steps should be taken during a widespread power outage according to US guidelines?
   10. How do disaster response manuals address communication during outages?
c. Mixed queries:
   11. For outages caused by assets in poor condition, what EPA actions are recommended?
   12. How should work orders be prioritized for assets that serve customers in critical infrastructure?
   13. What FEMA procedures apply to outages affecting commercial customers during weather events?
   14. Compare outage resolution times for circuits originating from different substations, and what the disaster manual says about response times
   15. For assets requiring maintenance in the next 30 days, what safety protocols from the manuals should be followed?