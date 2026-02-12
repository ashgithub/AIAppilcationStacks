## Stack App server

Manages the main applications server sides to connect with client
Sends A2UI and A2A events

## Set up. Requires UV manager to run.

1. Create .env file and set up GenAI credentials as the example [.env.example](./.env.example)

2. To confirm set up is ready you can run [oci_agent.py](./agent/oci_agent.py) using
```bash
uv run ./agent/oci_agent.py
```

3. Confirm LLM setup is ready wunning [oci_llm.py](./chat/oci_llm.py) using
```bash
uv run ./chat/oci_llm.py
```

3. Run the server with
```bash
uv run __main__.py
```

In case the project lock or toml file is broken, can reset using
```bash
uv init
uv sync
```
Add the dependencies from toml

Run server to test right setup. Make sure to have API key and also the toml file dependencies.
Path to a2ui tool.uv is required, if the default project is untouched no need to modify toml file.
```bash
uv run .
```

Add your OCI data on the ```.env``` file.

## Testing
```bash
uv pip install -e ".[dev]"
uv run pytest tests/test_ui_orchestrator_agent.py -v
```