# Scripts Folder

This folder contains local process-control scripts for running the demo without `systemd`.

Target runtime topology:

- API server on `127.0.0.1:10002`
- Client static server on `127.0.0.1:6003`

## Before first use

On Venus, make scripts executable:

```bash
chmod +x scripts/*.sh
```

## Script list

- `start_server_bg.sh`: starts API server in background (`nohup`), writes PID/log.
- `start_client_bg.sh`: starts static client server in background (`nohup`), writes PID/log.
- `start_all_bg.sh`: starts client + server.
- `stop_server.sh`: stops API server using PID file, then fallback process pattern.
- `stop_client.sh`: stops client server using PID file, then fallback process pattern.
- `stop_all.sh`: stops both services.
- `reset_all.sh`: stop both, clear stale PID files, start both again.
- `run_server_fg.sh`: runs API server in foreground (debug mode).
- `run_client_fg.sh`: runs client static server in foreground (debug mode).

## What `common.sh` is for

`common.sh` is a shared helper file sourced by the other scripts.  
It centralizes:

- project paths (`PROJECT_ROOT`, server/client folders)
- runtime folders (`run/`, `logs/`)
- default ports (`SERVER_PORT=10002`, `CLIENT_PORT=6003`)
- PID/log file paths
- utility helpers:
  - `ensure_runtime_dirs`
  - `is_pid_running`
  - `stop_from_pid_file`

## Generated files during execution

- PID files:
  - `run/edge-aistack-api-10002.pid`
  - `run/edge-aistack-client-6003.pid`
- Logs:
  - `logs/edge-aistack-api-10002.out`
  - `logs/edge-aistack-client-6003.out`

## Common workflows

Start both:

```bash
./scripts/start_all_bg.sh
```

Stop both:

```bash
./scripts/stop_all.sh
```

Reset both:

```bash
./scripts/reset_all.sh
```

Run in foreground for debugging:

```bash
./scripts/run_server_fg.sh
./scripts/run_client_fg.sh
```
