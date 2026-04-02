# App Server

Backend server for the Stack demo. It exposes:
- an A2A dynamic graph endpoint (`/agent`)
- an A2A LLM endpoint (`/llm`)
- traditional JSON endpoints (`/traditional/*`)
- semantic cache endpoints for dynamic graph NL2Graph flows (`/agent/cache/semantic`)

It is built with Starlette + A2A SDK, and uses OCI GenAI + Oracle DB for LLM, RAG, and NL2SQL capabilities.

## Requirements

- Python `>=3.13`
- `uv` package manager
- OCI credentials and access to GenAI endpoint
- Oracle DB credentials/wallet (required for RAG + NL2SQL tools)

## Environment Setup

1. From `app/server`, copy the env template:
```bash
cp .env.example .env
```

2. Fill in the values in `.env`:
```env
COMPARTMENT_ID=<your-compartment-id>
AUTH_PROFILE=<your-config-profile-id>
SERVICE_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com
GEN_AI_MODEL=<model-id>
OPENAI_INNO_DEV1=<openai-api-key-if-needed>
OCI_CONVERSATION_STORE_ID=<optional-conversation-store-id>

DB_PASSWORD=<your-db-password>
DB_WALLET_PATH=<absolute-path-to-wallet>
DB_WALLET_PASSWORD=<wallet-password>
DB_USER=<db-user>
DB_DSN=<db-dsn>
DB_CONNECTION_MODE=persistent

LANGFUSE_SECRET_KEY=<sk-langfuse-key>
LANGFUSE_PUBLIC_KEY=<pk-langfuse-key>
LANGFUSE_HOST=<langfuse-host>
LANGFUSE_USER_ID=<tracing-user-id>
APP_OBSERVABILITY_ENABLED=True
LANGFUSE_TRACING_ENABLED=True
```

## Install Dependencies

```bash
uv sync
```

## Run the Server

From `app/server`:

```bash
uv run __main__.py
```

Optional flags:

```bash
uv run __main__.py --host localhost --port 10002
```

## Key Routes

- `POST /agent/*`: A2A dynamic multi-agent graph endpoint
- `POST /llm/*`: A2A LLM endpoint
- `GET /agent/cache/semantic`: retrieve semantic cache summary (`?limit=25`, max 100)
- `DELETE /agent/cache/semantic`: clear semantic cache
- `GET /traditional`
- `GET /traditional/energy`
- `GET /traditional/trends`
- `GET /traditional/timeline`
- `GET /traditional/industry`
- `GET /rag_docs/*`: static access to source PDFs used by RAG

## Optional: Load RAG Documents Into DB

To load/index the PDFs in `core/rag_docs` into the Oracle vector store:

```bash
uv run core/setup_rag.py
```

## Tests

Current test scripts under `tests/`:
- `test_catalog.py`
- `test_suggested_questions.py`

Run with:

```bash
uv run pytest tests -v
```

## Project Structure

```text
app/server/
|-- __main__.py                         # Server entrypoint (mounts /agent, /llm, /traditional)
|-- pyproject.toml                      # Dependencies and project metadata
|-- mock_executors.py                   # Mock executors (available in repo, not wired in __main__.py)
|-- chat_app/                           # LLM runtime executors and tools
|   |-- llm_executor.py
|   |-- main_llm.py
|   |-- nl2sql_agent.py
|   `-- rag_tool.py
|-- dynamic_app/                        # Dynamic multi-agent graph orchestration runtime
|   |-- dynamic_agents_graph.py
|   |-- dynamic_graph_executor.py
|   |-- back_agents_graph/
|   `-- ui_agents_graph/
|-- core/                               # Shared prompts, schemas, providers, and structures
|   |-- base_agent.py
|   |-- common_struct.py
|   |-- gen_ai_provider.py
|   |-- langfuse_tracing.py
|   |-- setup_rag.py
|   |-- traditional_data_provider.py
|   |-- rag_docs/                       # Source PDFs exposed at /rag_docs
|   |-- chat_app/prompts/
|   `-- dynamic_app/
|       |-- a2a_config_provider.py
|       |-- dynamic_struct.py
|       |-- parallel_ui_shared.py
|       |-- schema_utils.py
|       |-- prompts/
|       |-- schemas/
|       `-- streaming/
|-- database/
|   |-- connections.py                  # Oracle DB connection/pool utilities
|   `-- semantic_cache.py               # Semantic cache storage for NL2Graph
|-- traditional_app/
|   `-- data_provider.py                # Traditional endpoint payload builders
`-- tests/
    |-- test_catalog.py
    `-- test_suggested_questions.py
```

## Notes for Contributors

- A2A capabilities and advertised skills are defined in `core/dynamic_app/a2a_config_provider.py`.
- Dynamic graph state model lives in `core/dynamic_app/dynamic_struct.py`.
- The app auto-loads `.env` at startup.
- RAG documents in `core/rag_docs` are served directly through `/rag_docs` when the folder exists.
