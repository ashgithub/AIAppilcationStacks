## Client Deployment Guide (Dedicated Client Process on Port 6003)

This environment intentionally uses split upstreams for failure isolation:

- Public UI path: `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/`
- Public API path: `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api/`
- Internal client static process: `127.0.0.1:6003`
- Internal API process: `127.0.0.1:10002`

The client is served by a dedicated process on `6003` (not by Nginx static root).

---

## 1. Build-time env for client

Create/update:

- `app/client/shell/.env.production`

Content:

```env
VITE_APP_BASE_PATH=/edge_aistack/
VITE_SERVER_ORIGIN=https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api
```

---

## 2. Build client

From repo root:

```bash
cd app/client
npm install
npm run build:prod
```

Output:

- `app/client/shell/dist_web`

---

## 3. Publish build output to VM app path

The client service serves directly from:

- `/opt/edge_aistack/app/client/shell/dist_web`

Sync example:

```bash
rsync -av --delete app/client/shell/dist_web/ /opt/edge_aistack/app/client/shell/dist_web/
```

---

## 4. Client service (port 6003)

Use the draft service file:

- `app/server/deploy/edge-aistack-client-static.service`

Target path on VM:

- `/etc/systemd/system/edge-aistack-client-static.service`

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now edge-aistack-client-static
sudo systemctl status edge-aistack-client-static
```

---

## 5. Nginx routing for split upstreams

Use draft:

- `app/server/deploy/edge_aistack.nginx.conf`

Important:

- `location ^~ /edge_aistack/api/` must be declared before `location ^~ /edge_aistack/`.
- `/edge_aistack/api/` proxies to `127.0.0.1:10002`.
- `/edge_aistack/` proxies to `127.0.0.1:6003`.

Apply:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Verify routing

1. Client upstream:

```bash
curl -I http://127.0.0.1:6003/
```

Expected: `200`.

2. API upstream:

```bash
curl -I http://127.0.0.1:10002/agent/.well-known/agent-card.json
```

Expected: `200`.

3. Public endpoints:

- `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/`
- `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api/agent/.well-known/agent-card.json`
- `https://venus.aisandbox.ugbu.oraclepdemos.com/edge_aistack/api/llm/.well-known/agent-card.json`

4. Browser network checks:

- UI assets load from `/edge_aistack/...`
- API calls go to `/edge_aistack/api/...`
- Streaming responses are not cut by buffering/timeouts.

---

## 7. Failure-isolation checks

1. Stop client service only:

```bash
sudo systemctl stop edge-aistack-client-static
```

Expected: UI path fails, API service remains reachable.

2. Start client service and stop API service:

```bash
sudo systemctl start edge-aistack-client-static
sudo systemctl stop edge-aistack-api
```

Expected: UI shell loads, API calls fail (as expected), other demos stay independent.
