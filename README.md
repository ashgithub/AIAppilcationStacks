# AI Application Stacks

A comprehensive demonstration project showcasing the evolution of application development paradigms, from traditional static interfaces to dynamic AI-driven experiences.

## Overview

This project demonstrates three distinct approaches to building modern applications:

### Traditional App
A conventional web application with static UI components and predefined workflows, representing the pre-AI era of application development.

### LLM App
A conversational interface powered by Large Language Models (LLMs), enabling natural language interactions for information retrieval and assistance.

### Agentic App
An intelligent application that leverages AI agents to dynamically generate, modify, and adapt user interfaces in real-time through the A2UI (Agent-to-UI) protocol, representing the future of adaptive software systems.

## Quick Start

1. **Setup libraries:**
   ```bash
   # Build renderers
   cd libs/renderers/web_core && npm install && npm run build
   cd ../lit && npm install && npm run build
   ```

2. **Setup server:**
   ```bash
   cd ../../../app/server
   uv sync
   cp .env.example .env  # Configure OCI credentials
   ```

3. **Setup client:**
   ```bash
   cd ../client
   npm install
   ```

4. **Run both services:**
   ```bash
   npm run demo:edge  # Runs both client and server concurrently
   ```

## Architecture

The application stack consists of three main components:

### Client Application (`app/client/`)
- Built with TypeScript and Lit web components
- Provides three interactive modules: Traditional, Chat, and Dynamic Agent interfaces
- Communicates with the server via HTTP/WebSocket for real-time updates
- Uses A2UI protocol for dynamic UI generation and modification

### Server Application (`app/server/`)
- Python-based backend using FastAPI and Starlette
- Implements A2A (Agent-to-Agent) protocol for inter-agent communication
- Hosts two primary agents:
  - **Restaurant Agent**: Dynamic agent for restaurant discovery and recommendations
  - **Outage & Energy LLM Agent**: Specialized LLM agent for power outage and energy data analysis
- Integrates with OCI Generative AI services for LLM capabilities

### Libraries (`libs/`)
- **Renderers**: Web component renderers for UI elements (Lit and Web Core)
- **A2A Agents**: Agent-to-Agent communication protocols and implementations
- **Specifications**: A2UI protocol definitions and schemas

## Technology Stack

### Frontend
- **TypeScript**: Type-safe JavaScript development
- **Lit**: Lightweight web component library
- **Vite**: Fast build tool and development server
- **MapLibre GL**: Open-source mapping library

### Backend
- **Python 3.13+**: Core programming language
- **FastAPI/Starlette**: Modern async web frameworks
- **LangChain**: LLM integration and orchestration
- **OCI Generative AI**: Cloud-based AI services
- **A2A SDK**: Agent-to-Agent communication protocol

### Development Tools
- **UV**: Fast Python package manager
- **NPM/PNPM**: JavaScript package management
- **Git**: Version control

## Prerequisites

- **Node.js** (v18+)
- **Python** (3.13+)
- **UV** Python package manager
- **NPM** or **PNPM** package manager
- **Git** for version control
- **OCI Account** with Generative AI access (for LLM features)

## Run client

Make sure to have `npm` package manager and NodeJS itself

1. set up the renderers:

Navigate to [libs/renderers/web_core](./libs/renderers/web_core/) and run:

```bash
npm install
npm run build
```

Do the same on [libs/renderers/lit](./libs/renderers/lit/) and run:

```bash
npm install
npm run build
```

2. With the render ready, now go to [app/client](./app/client/) and run the shell:

```bash
npm install
npm run serve:shell
```

the terminal should open the port `5173` on local

```bash
✅ Ran 2 scripts and skipped 0 in 1.9s.     
✅ Ran 0 scripts and skipped 1 in 0s.       
[dotenv@17.2.3] injecting env (0) from .env -- tip: ⚙️  write to custom object with { processEnv: myObject }

  VITE v7.3.1  ready in 407 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

This is running on **DEV** mode

## Run server

Enter the server folder [server](./app/server/)
Set up the environment, make sure to have `uv` manager installed.

Install dependencies with:

```bash
uv sync

#activate the virtual environment

#windows
source .venv/Scripts/activate

#Linux
source .venv/bin/activate
```

Make sure to have the [.env](./app/server/) file created and with valid credentials that have access to OCI GenAI services.
Check out the `.env.example` as reference

Now run the server:

```bash
uv run __main__.py
```

Should open server connection at `10002`

```bash
INFO:oci.circuit_breaker:Default Auth client Circuit breaker strategy enabled
INFO:     Started server process [24020]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:10002 (Press CTRL+C to quit)
```

Access the application at `http://localhost:5173`

## API Endpoints

### Server Endpoints
- `GET/POST/DELETE /agent/config` - Dynamic agent configuration
- `/agent/*` - Restaurant agent endpoints
- `/llm/*` - Outage & Energy LLM agent endpoints

### Client Features
- **Traditional Module**: Static UI with predefined components
- **Chat Module**: LLM-powered conversational interface
- **Dynamic Module**: Agent-driven adaptive UI generation

## Development

### Project Structure
```
app/
├── client/          # Frontend TypeScript/Lit application
│   └── shell/       # Main application shell and components
└── server/          # Backend Python/FastAPI application
    ├── chat_app/    # LLM chat functionality
    ├── core/        # Core utilities and schemas
    ├── dynamic_app/ # Agent orchestration
    └── traditional_app/ # Static app data providers

libs/
├── renderers/       # UI component renderers
├── a2a_agents/      # Agent-to-Agent protocol implementations
└── specification/   # A2UI protocol specifications
```

### Adding New Components
1. Create component in `app/client/shell/components/`
2. Register in `app/client/shell/ui/custom-components/register-components.ts`
3. Import in main app file

### Extending Agents
1. Define agent capabilities in `app/server/core/dynamic_app/`
2. Implement agent logic in `app/server/dynamic_app/`
3. Add routing in `app/server/__main__.py`

## Testing

### Server Tests
```bash
cd app/server
uv pip install -e ".[dev]"
uv run pytest tests/ -v
```