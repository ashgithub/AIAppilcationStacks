# Client Application (Lit + A2UI)

This folder contains the frontend workspace for the app shell and the scripts used to run it standalone or together with the Python backend.

## Prerequisites

- Node.js 20+
- npm
- Optional for full stack demo: `uv` (used by `app/server`)

## Run Modes

From `app/client`:

```bash
npm install
```

Client only:

```bash
npm run serve:shell
```

Full demo (client + server):

```bash
npm run demo:edge
```

## NPM Scripts (root `app/client/package.json`)

- `serve:shell`: starts Vite dev server in `shell` workspace (`cd shell && npm run dev`)
- `serve:agent:edge`: starts backend from `app/server` (`uv run __main__.py`)
- `demo:edge`: runs shell + backend in parallel via `concurrently`

## Client Architecture

Main entrypoint is [`shell/app.ts`](./shell/app.ts). It renders three modules that can be toggled independently:

- `Traditional` (`/traditional` endpoints)
- `Chat` (`/llm`)
- `Agent` (`/agent`)

Message routing and session handling are centralized in [`shell/services/a2ui-router.ts`](./shell/services/a2ui-router.ts), which dispatches normalized streaming events to modules.

Default backend origin is defined in [`shell/services/server-endpoints.ts`](./shell/services/server-endpoints.ts) as:

`http://localhost:10002`

## Folder Structure

```text
app/client
|- package.json                # workspace-level scripts (serve + demo)
|- README.md
`- shell                       # Lit app workspace
   |- app.ts                   # top-level container and module toggles
   |- index.html
   |- vite.config.ts           # Vite config + middleware plugin registration
   |- package.json             # shell-specific build/dev/test scripts (Wireit)
   |- components               # major UI modules and shared shell components
   |  |- main_traditional.ts
   |  |- main_chat.ts
   |  |- main_agent.ts
   |  |- chatTextArea.ts
   |  |- status_drawer.ts
   |  |- stat_bar.ts
   |  `- config_canvas.ts
   |- configs                  # app/module configuration models + defaults
   |  |- types.ts
   |  |- agent_config.ts
   |  |- chat_config.ts
   |  |- outage_config.ts
   |  |- traditional_config.ts
   |  |- restaurant.ts
   |  `- quick_queries.json
   |- middleware               # Vite middleware for A2A/A2UI request handling
   |  |- index.ts
   |  `- a2a.ts
   |- services                 # transport, routing, normalization, formatting
   |  |- a2ui-router.ts
   |  |- client.ts
   |  |- server-endpoints.ts
   |  |- stream-event-normalizer.ts
   |  |- stream-status.ts
   |  `- number-format.ts
   |- ui                       # UI exports and custom A2UI components
   |  |- ui.ts
   |  |- snackbar.ts
   |  `- custom-components
   |- theme                    # shared design tokens + theme definitions
   |- events                   # typed custom events used across components
   |- types                    # shared client-side types
   `- public                   # static assets (e.g., favicon)
```

## Key Integration Points

- A2A middleware endpoint: `shell/middleware/a2a.ts` handles `/a2a` POST traffic in dev.
- Component registration: `shell/ui/custom-components/register-components.ts`.
- Config contracts: `shell/configs/types.ts`.
- Quick query presets: `shell/configs/quick_queries.json`.

## Team Notes

- This workspace is Windows/PowerShell-friendly by default (`cd` style scripts in `package.json`).
- If backend host/port changes, update [`shell/services/server-endpoints.ts`](./shell/services/server-endpoints.ts).
