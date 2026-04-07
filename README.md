# AI Application Stacks

A comprehensive demonstration project showcasing the evolution of application development paradigms, from traditional static interfaces to dynamic AI-driven experiences.

## Overview

This project demonstrates three approaches to building modern applications over the same outage and energy domain:

### Traditional App
A conventional web application with static UI components and predefined workflows.

### LLM App
A conversational interface powered by Large Language Models (LLMs), enabling natural language interactions for information retrieval and assistance.

### Agentic App
An intelligent application that leverages AI agents to dynamically generate, modify, and adapt user interfaces in real time through the A2UI (Agent-to-UI) protocol.

## Local Notices And Compatibility

> [!IMPORTANT]
> For macOS/Linux, if dependencies were previously installed on Windows, delete `package-lock.json` and `node_modules` before reinstalling.
>
> If errors persist, check [MAC-LINUX.md](./MAC-LINUX.md) and start with a clean client dependency install.
>
> The project currently uses `shx` in client scripts. If cross-platform errors continue, review/remediate `shx` usage as described in [MAC-LINUX.md](./MAC-LINUX.md).

- Langfuse host (project reference): [host](https://apps.research-lab.ugbu.oraclepdemos.com/langfuse/organization/cmmwz8eo00138wp07y72jd9dh)

## Prerequisites

- Node.js 20+ and `npm`
- Python 3.13+
- `uv` package manager
- Git
- OCI account and credentials with Generative AI access (required for real LLM/agent execution)
- Oracle DB credentials/wallet (required for NL2SQL/RAG flows)

## Quick Start

This is the fastest complete setup for the full demo.

1. Install the local Python SDK used by server (`a2ui-agent` path dependency):
   ```bash
   cd libs/agent_sdks/python
   uv sync
   uv pip install -e .
   ```

2. Build renderer libraries:
   ```bash
   cd ../../renderers/web_core
   npm install
   npm run build

   cd ../lit
   npm install
   npm run build
   ```

3. Configure and install server dependencies:
   ```bash
   cd ../../../app/server
   uv sync
   cp .env.example .env
   ```

4. Install client dependencies:
   ```bash
   cd ../client
   npm install
   ```

5. Run both services from `app/client`:
   ```bash
   npm run demo:edge
   ```

6. Access the app at `http://localhost:5173`

7. Try queries from [DEMO.md](./DEMO.md)

## Environment Setup Notes (Server)

From `app/server/.env.example`, configure values like:

```env
COMPARTMENT_ID=<your-compartment-id>
AUTH_PROFILE=<oci-config-profile>
SERVICE_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com

DB_PASSWORD=<your-password>
DB_WALLET_PATH=<absolute-path-to-wallet>
DB_WALLET_PASSWORD=<wallet-password>
DB_USER=<db-user>
DB_DSN=<db-dsn>
```

Optional runtime mode:
- `uv run __main__.py --mock` starts credential-free mock executors for UI testing.

## Module Explanations

### Traditional Module
- Static, predefined payload-driven UI.
- Main server provider: `app/server/traditional_app/data_provider.py`
- Endpoints:
  - `GET /traditional`
  - `GET /traditional/energy`
  - `GET /traditional/trends`
  - `GET /traditional/timeline`
  - `GET /traditional/industry`

### Chat Module (LLM)
- A2A-backed conversational pipeline for outage and energy analysis.
- Main modules:
  - `app/server/chat_app/main_llm.py`
  - `app/server/chat_app/llm_executor.py`
  - `app/server/chat_app/nl2sql_agent.py`
  - `app/server/chat_app/rag_tool.py`
- Endpoint root: `POST /llm/*`

### Agent Module (Dynamic UI)
- Multi-agent graph that generates structured UI and custom widgets.
- Main orchestration modules:
  - `app/server/dynamic_app/dynamic_agents_graph.py`
  - `app/server/dynamic_app/dynamic_graph_executor.py`
  - `app/server/dynamic_app/back_agents_graph/`
  - `app/server/dynamic_app/ui_agents_graph/`
- Prompt/schema/config modules:
  - `app/server/core/dynamic_app/prompts/`
  - `app/server/core/dynamic_app/schemas/`
  - `app/server/core/dynamic_app/a2a_config_provider.py`
- Widget schemas include:
  - `kpi`, `line_graph`, `bar_graph`, `table`, `map`, `timeline`
- Endpoint root: `POST /agent/*`
- Runtime control endpoints:
  - `GET/POST/DELETE /agent/config`
- Semantic cache endpoints:
  - `GET /agent/cache/semantic`
  - `DELETE /agent/cache/semantic`

## Architecture

### Client Application (`app/client/`)
- Built with TypeScript and Lit web components
- Includes three runtime modules: `Traditional`, `Chat`, and `Agent`
- Uses HTTP/A2A communication with server endpoints
- Includes custom A2UI components under `app/client/shell/ui/custom-components/`

### Server Application (`app/server/`)
- Python backend built with Starlette + A2A SDK
- Mounts and serves:
  - `/agent` (dynamic graph agent)
  - `/llm` (LLM agent)
  - `/traditional*` (traditional REST payloads)
  - `/rag_docs/*` (static RAG source documents)
- Supports mock mode for credential-free UI testing

### Libraries (`libs/`)
- `libs/agent_sdks/python`: local A2UI agent SDK package (`a2ui-agent`)
- `libs/renderers/web_core`: renderer core
- `libs/renderers/lit`: Lit renderer package
- `libs/specification`: A2UI specification versions (`v0_8`, `v0_9`) and tests/eval tools

## Technology Stack

### Frontend
- TypeScript
- Lit
- Vite
- MapLibre GL

### Backend
- Python 3.13+
- Starlette/FastAPI ecosystem
- LangChain
- OCI Generative AI
- A2A SDK
- Oracle DB (`oracledb`)

### Development Tools
- UV
- npm
- Git

## Run Client (Detailed)

From `libs/renderers/web_core`:

```bash
npm install
npm run build
```

From `libs/renderers/lit`:

```bash
npm install
npm run build
```

From `app/client`:

```bash
npm install
npm run serve:shell
```

Expected local URL is usually `http://localhost:5173`.

## Run Server (Detailed)

From `app/server`:

```bash
uv sync

# Activate virtual env (optional but useful)
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Create/configure `.env` (use `.env.example` as reference), then run:

```bash
uv run __main__.py
```

Default server URL: `http://localhost:10002`

Alternative run modes:

```bash
uv run __main__.py --host localhost --port 10002 --mock
```

## VM Port Mapping (Shared Demo Instance)

For the Venus shared Nginx environment, this demo uses:

- Client static process: `127.0.0.1:6003` (mapped to `/edge_aistack/`)
- API server process: `127.0.0.1:10002` (mapped to `/edge_aistack/api/`)

This split-process mapping is used for isolation from other demos running on the same VM.

## API Endpoints

### Agent + Config
- `GET /agent/config`
- `POST /agent/config`
- `DELETE /agent/config`
- `GET /agent/cache/semantic`
- `DELETE /agent/cache/semantic`
- `POST /agent/*`

### LLM
- `POST /llm/*`

### Traditional
- `GET /traditional`
- `GET /traditional/energy`
- `GET /traditional/trends`
- `GET /traditional/timeline`
- `GET /traditional/industry`

### RAG Docs
- `GET /rag_docs/*`

## Development

### Project Structure

```text
app/
|-- client/
|   `-- shell/                       # Main shell and module views
`-- server/
    |-- __main__.py                  # Server entrypoint
    |-- chat_app/                    # LLM executor + tools (RAG + NL2SQL)
    |-- dynamic_app/                 # Dynamic multi-agent graph orchestration
    |-- traditional_app/             # Traditional payload providers
    |-- core/                        # Shared prompts/schemas/providers
    `-- database/                    # DB connections and semantic cache

libs/
|-- agent_sdks/python/               # Local a2ui-agent package
|-- renderers/web_core/              # Renderer core
|-- renderers/lit/                   # Lit renderer
`-- specification/                   # A2UI specs, tests, and eval tools
```

### Adding New Components
1. Create component in `app/client/shell/components/` or `app/client/shell/ui/custom-components/`
2. Register custom components in `app/client/shell/ui/custom-components/register-components.ts`
3. Wire the component into the target module view

### Extending Agents
1. Define/update capabilities and schema providers in `app/server/core/dynamic_app/`
2. Implement or adjust graph logic in `app/server/dynamic_app/`
3. Ensure routing/mount points in `app/server/__main__.py` are aligned

## Testing

### Server Tests

```bash
cd app/server
uv pip install -e ".[dev]"
uv run pytest tests -v
```

## Extra References

- Demo prompts: [DEMO.md](./DEMO.md)
- Cross-platform notes: [MAC-LINUX.md](./MAC-LINUX.md)
- Server-specific guide: [app/server/README.md](./app/server/README.md)
