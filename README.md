## Application to showcase benchmarking of applications

### Traditional app

Normal application as used to be before AI

### LLM app

Common LLM / Chatbot application current approach

### Agentic app

Future applications that use agents and dynamic UI

## RUN

First, set up the renderers:

Navigate to [renderers/web_core](./libs/renderers/web_core/) and run:

```bash
npm install
npm run build
```

Do the same on [renderers/lit](./libs/renderers/lit/) and run:

```bash
npm install
npm run build
```

#### Running server

Enter the server folder [server](./app/server/)
Set up the environment

```bash
uv run __main__.py
```