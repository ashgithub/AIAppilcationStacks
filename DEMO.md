## Demo queries

Current sample demo queries to call the different agent and LLM modes of the application.
Descriptions include general output responses and which use cases they cover.

This is just a sample, other queries are also supported.

### Stand alone *LLM application*

#### 1. Relational DB queries

- **Query:** Which work orders are still open and their associated asset types?
- **Query:** List assets that are currently in overwatch condition (condition_score < 4)
  - **Observed result:** LLM shows a table with assets listed, agent shwos a better table with data, a bar graph to show the assets condition by type and some key metrics with KPI cards.
- **Query:** Show circuits with their substation names and total customers served, ordered by customer count
  - **Observed result:** LLM some text, agent table with circuits presents, substation related and customers served, and a bar graph to show the demand of the circuit attached.
- **Query:** Find outages that lasted more than 2 hours and their associated root cause assets

#### 2. RAG queries

- **Query:** What are the EPA recommended actions for power outages in the US?
- **Query:** What immediate steps should be taken during a widespread power outage according to US guidelines?
- **Query:** Which are the protocols followed by mexican regulations for ambiental disaster attention?
  - **Observed result:** LLM bullet + text, Agent generates some text and a timeline to display the follow up of different steps and protocols.

#### 3. DB + RAG queries (mixed)

- **Query:** Map the outages in residential areas, and then explain, what recovery procedures does the disaster manual recommend?
  - **Observed result:** Bullet and text from LLM, agent shows a map with outages, a timeline with follow plans for procedures.
- **Query:** Compare average outage duration by cause category and reference relevant EPA guidelines
  - **Observed result:** LLM bullet points and a table, agent generates a bar graph for average duration by cause, a table with details about duration and key insights, overall view using KPI cards and a timeline showing the outages causes and time of outage

### Stand alone *Agent application*

#### 1. Graph DB queries

- **Query:** Visualize substation locations with capacity indicators
  - **Observed result:** LLM some MD graphs and maps, agent displays a KPI dashborad with general data and a table with substations, capacity and circuits.
- **Query:** Display asset health distribution by condition score, include names if possible.
  - **Observed result:** LLM produces text and some tables, agent generates a bar graph to show the distribution by condition score and a table with the detailed information by category.

#### 2. RAG queries

- **Query:** How do disaster response manuals address communication during outages?
  - **Observed result:** LLM tries to generate a MD flow and text, Agent produces KPI cards, and a table to show each one of the steps that the manual is recomending.
- **Query:** Create a timeline visualization of FEMA assistance steps for electrical outages
- **Query:** Give me some diagrams on how can we identify and evaluate risks according to mexican guidelines?
  - **Observed result:** LLM tries to emulate a graph flow with MD, agent generates a timeline to show the flow and some text explanation

#### 3. DB + RAG queries (mixed)

- **Query:** Map the outage locations and show also EPA recommended response zones
- **Query:** Generate a dashboard showing work order priorities with referenced manual safety protocols

### Side by side comparison

#### 1. Relational DB queries

- **Query:** What are the most common outage cause categories in the last 6 months?
  - **Observed result:** LLM produces some text and a list with causes. Agent mode shows a small text, a bar graph with causes, some KPI cards and a table with the numbers found.
- **Query:** Find circuits with the highest number of customers served
- **Query:** Show me the location of the main substations and circuits with characteristics.

#### 2. RAG queries

- **Query:** What immediate steps should be taken during a widespread power outage according to US guidelines?
  - **Observed result:** LLM shows some bullet points with the retrieved data, Agent displays a timeline with the steps to follow and some text with the explanation of documents.
- **Query:** What procedures are outlined in the Mexican disaster manual for infrastructure recovery compared to EPA and FEMA available procedures?
- **Query:** what are the recommended attencion guidelines for earthquakes at mexico?

#### 3. DB + RAG queries (mixed)

- **Query:** Compare outage resolution times for circuits originating from different substations, and what the disaster manual says about response times
  - **Observed result:** LLM generates a table with solution time, and some MD diagrams with time, the agent produces a bar graph with average solution time, a table to show the comparison and a timeline to share the information from disaster manual.
- **Query:** Analyze customer complaints by outage category and correlate with FEMA assistance guidelines
- **Query:** Show asset maintenance schedules alongside safety protocol requirements from manuals


## Additional queries to enrich agent visual outputs

Use these to push richer dashboards, especially trend and line-graph views.

### Line graph / trend-focused

- **Query:** Show monthly outage counts for the last 12 months by cause category using a line graph
- **Query:** Trend average outage duration per month over the last year, split by substations
    - **Observerd result**: Line grpah to show trend of data, KPI for summary of data and a table with extra details of each duration.
- **Query:** Plot the monthly number of open vs closed work orders for the last 6 months
- **Query:** Show tendencies on how average asset condition score has changed month by month by asset type
    -**Observerd result**: Line grpah to show trend of data, table with details about the specific sections and KPI to support change data
- **Query:** display the swing of weekly outage incidents for residential vs commercial areas
    -**Observerd result**: Line grpah to show trend of data, table with details about the specific sections and KPI to support change data

### Mixed data (DB + RAG) for richer layouts

- **Query:** Trend outage duration by month and explain which EPA actions are recommended when duration increases
- **Query:** Show substations with the highest outage frequency over time and map related FEMA response steps
    -**Observerd result**: KPI cards in general data, Trend line grpah for time outages, table for substation data and timeline for the procedure steps.
- **Query:** Compare quarterly outage causes and add Mexican manual recovery priorities for each top cause
- **Query:** Plot circuits with recurring outages over time and include corresponding safety protocol guidance from manuals

### Dashboard-style multi-widget prompts

- **Query:** Build a dashboard with KPIs, table, and trend line for outage volume, resolution time, and affected customers by month
- **Query:** Create a network reliability dashboard: top substations by outages, monthly outage trend line, and open work orders summary
- **Query:** Analyze assets in poor condition with a bar chart by type, line trend of failures over time, and recommended response actions
- **Query:** Show me location of outage hotspots, and explain the relation to monthly outage trends based on the response procedures recommended by manuals
    -**Observerd result**: map for outages and substation locations, line graph for the average outage duration by substation, timeline for steps on manuals and KPI cards for general metrics.