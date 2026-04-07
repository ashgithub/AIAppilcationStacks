# VM Deployment Drafts (Dedicated Client Process + API Process)

This environment uses split processes by design:

- Client static server: `127.0.0.1:6003`
- API server: `127.0.0.1:10002`
- Public UI: `/edge_aistack/`
- Public API: `/edge_aistack/api/`

This is intentionally non-standard to preserve demo isolation on the shared instance.

## Draft files

Use files under `app/server/deploy/`:

- `edge-aistack-api.service` -> `/etc/systemd/system/edge-aistack-api.service`
- `edge-aistack-client-static.service` -> `/etc/systemd/system/edge-aistack-client-static.service`
- `.env.production.example` -> `/opt/edge_aistack/app/server/.env.production`
- `edge_aistack.nginx.conf` -> `/etc/nginx/conf.d/edge_aistack.conf`

## 1) API service (port 10002)

```ini
[Unit]
Description=Edge AI Stack API (Starlette/A2A)
After=network.target

[Service]
Type=simple
User=<VM_USER>
Group=<VM_USER>
WorkingDirectory=/opt/edge_aistack/app/server
EnvironmentFile=/opt/edge_aistack/app/server/.env.production
ExecStart=/usr/local/bin/uv run __main__.py --host 127.0.0.1 --port 10002
Restart=always
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

## 2) Client static service (port 6003)

```ini
[Unit]
Description=Edge AI Stack Client Static Server (Port 6003)
After=network.target

[Service]
Type=simple
User=<VM_USER>
Group=<VM_USER>
WorkingDirectory=/opt/edge_aistack
ExecStart=/usr/bin/python3 -m http.server 6003 --bind 127.0.0.1 --directory /opt/edge_aistack/app/client/shell/dist_web
Restart=always
RestartSec=5
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

## 3) Server env file

```env
PUBLIC_BASE_URL=https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api
SERVER_BIND_HOST=127.0.0.1
SERVER_BIND_PORT=10002

# existing required vars:
COMPARTMENT_ID=...
AUTH_PROFILE=...
SERVICE_ENDPOINT=...
GEN_AI_MODEL=...
OPENAI_INNO_DEV1=...
OCI_CONVERSATION_STORE_ID=...

DB_PASSWORD=...
DB_WALLET_PATH=...
DB_WALLET_PASSWORD=...
DB_USER=...
DB_DSN=...
DB_CONNECTION_MODE=persistent

LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_HOST=...
LANGFUSE_USER_ID=...
APP_OBSERVABILITY_ENABLED=True
LANGFUSE_TRACING_ENABLED=True
```

## 4) Nginx routing (split upstreams)

```nginx
server {
    listen 443 ssl http2;
    server_name venus.aisandbox.ugbu.oraclepdemos.com;

    # ssl_certificate ...;
    # ssl_certificate_key ...;

    location = / {
        return 302 /edge_aistack/;
    }

    # Keep API block first (routing precedence).
    location ^~ /edge_aistack/api/ {
        proxy_pass http://127.0.0.1:10002/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location ^~ /edge_aistack/ {
        proxy_pass http://127.0.0.1:6003/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 5) Deploy and validate

1. Build client:
   - `cd app/client && npm run build:prod`
2. Ensure build is at:
   - `/opt/edge_aistack/app/client/shell/dist_web`
3. Install/refresh server dependencies:
   - `cd /opt/edge_aistack/app/server && uv sync`
4. Enable both services:
   - `sudo systemctl daemon-reload`
   - `sudo systemctl enable --now edge-aistack-api`
   - `sudo systemctl enable --now edge-aistack-client-static`
5. Apply Nginx config:
   - `sudo nginx -t`
   - `sudo systemctl reload nginx`
6. Smoke checks:
   - `curl -I http://127.0.0.1:6003/`
   - `curl -I http://127.0.0.1:10002/agent/.well-known/agent-card.json`
   - `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/`
   - `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api/agent/.well-known/agent-card.json`
   - `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api/llm/.well-known/agent-card.json`
