import logging
import httpx
import os
from pathlib import Path

import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, BasePushNotificationSender, InMemoryPushNotificationConfigStore
from a2a.types import AgentCard
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from langfuse import Langfuse
from opentelemetry.sdk.trace import TracerProvider

from chat_app.llm_executor import OutageEnergyLLMExecutor
from chat_app.main_llm import OCIOutageEnergyLLM
from dynamic_app.dynamic_agents_graph import DynamicGraph
from dynamic_app.dynamic_graph_executor import DynamicGraphExecutor
from streaming_app.streaming_graph import StreamingDynamicApp
from streaming_app.streaming_executor import StreamingGraphExecutor
from mock_executors import MockDynamicExecutor, MockLLMExecutor
from core.dynamic_app.a2a_config_provider import (
    dynamic_agent_capabilities,
    get_widget_catalog,
    get_widget_schema
)
from traditional_app.data_provider import (
    get_traditional_outage_messages,
    get_traditional_energy_messages,
    get_traditional_energy_trends_messages,
    get_traditional_timeline_messages,
    get_traditional_industry_messages
)

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
@click.option("--mock", is_flag=True, default=False, help="Run credential-free mock executors for UI testing")
@click.option(
    "--agent-backend",
    type=click.Choice(["dynamic", "streaming"], case_sensitive=False),
    default="dynamic",
    show_default=True,
    help="Select which backend is mounted at /agent.",
)
def main(host, port, mock, agent_backend):
    try:
        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            timeout=60,
            tracer_provider=TracerProvider(),
        )
        
        base_url = f"http://{host}:{port}"

        if mock:
            logger.warning("Starting server in mock mode (no OCI credentials required)")

        # region Dynamic agent executor setup
        primary_agent_base_url = f"{base_url}/agent"
        dynamic_base_url = primary_agent_base_url
        dynamic_agent_card = AgentCard(
            name="Energy Outage Agent",
            description="This agent helps analyze power outages, energy statistics, and industry performance.",
            url=dynamic_base_url,
            version="1.0.0",
            default_input_modes=DynamicGraph.SUPPORTED_CONTENT_TYPES,
            default_output_modes=DynamicGraph.SUPPORTED_CONTENT_TYPES,
            capabilities=dynamic_agent_capabilities,
            skills=[get_widget_catalog,get_widget_schema],
        )

        dynamic_agent_executor = MockDynamicExecutor() if mock else DynamicGraphExecutor(
            base_url=dynamic_base_url,
            langfuse_client=langfuse_client,
        )

        httpx_client = httpx.AsyncClient()
        dynamic_agent_push_config_store = InMemoryPushNotificationConfigStore()
        dynamic_agent_push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=dynamic_agent_push_config_store
        )
        
        dynamic_agent_request_handler = DefaultRequestHandler(
            agent_executor=dynamic_agent_executor,
            task_store=InMemoryTaskStore(),
            push_config_store=dynamic_agent_push_config_store,
            push_sender=dynamic_agent_push_sender
        )

        dynamic_agent_server = A2AStarletteApplication(
            agent_card=dynamic_agent_card, http_handler=dynamic_agent_request_handler
        )

        dynamic_agent_app = dynamic_agent_server.build()
        # endregion

        # region Streaming agent executor setup
        streaming_base_url = primary_agent_base_url
        streaming_agent_card = AgentCard(
            name="Energy Outage Streaming Agent",
            description="Streaming-first agent that emits progressive UI fragments from layout planning and worker packages.",
            url=streaming_base_url,
            version="1.0.0",
            default_input_modes=StreamingDynamicApp.SUPPORTED_CONTENT_TYPES,
            default_output_modes=StreamingDynamicApp.SUPPORTED_CONTENT_TYPES,
            capabilities=dynamic_agent_capabilities,
            skills=[get_widget_catalog, get_widget_schema],
        )

        streaming_agent_executor = MockDynamicExecutor() if mock else StreamingGraphExecutor(
            base_url=streaming_base_url,
            langfuse_client=langfuse_client,
        )

        streaming_agent_push_config_store = InMemoryPushNotificationConfigStore()
        streaming_agent_push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=streaming_agent_push_config_store,
        )

        streaming_agent_request_handler = DefaultRequestHandler(
            agent_executor=streaming_agent_executor,
            task_store=InMemoryTaskStore(),
            push_config_store=streaming_agent_push_config_store,
            push_sender=streaming_agent_push_sender,
        )

        streaming_agent_server = A2AStarletteApplication(
            agent_card=streaming_agent_card, http_handler=streaming_agent_request_handler
        )
        streaming_agent_app = streaming_agent_server.build()

        selected_primary_agent_app = (
            streaming_agent_app if str(agent_backend).lower() == "streaming" else dynamic_agent_app
        )
        selected_backend_label = str(agent_backend).lower()
        logger.info("Primary /agent backend selected: %s", selected_backend_label)
        # endregion

        # region LLM executor setup
        llm_base_url = f"{base_url}/llm"
        llm_capabilities = dynamic_agent_capabilities
        llm_skills = []
        llm_card = AgentCard(
            name="Outage and Energy LLM Agent",
            description="This LLM agent provides information about power outages, energy statistics, and industry performance.",
            url=llm_base_url,
            version="1.0.0",
            default_input_modes=OCIOutageEnergyLLM.SUPPORTED_CONTENT_TYPES,
            default_output_modes=OCIOutageEnergyLLM.SUPPORTED_CONTENT_TYPES,
            capabilities=llm_capabilities,
            skills=llm_skills,
        )

        llm_executor = MockLLMExecutor() if mock else OutageEnergyLLMExecutor(langfuse_client)

        llm_push_config_store = InMemoryPushNotificationConfigStore()
        llm_push_sender = BasePushNotificationSender(httpx_client=httpx_client,
                        config_store=llm_push_config_store)
        llm_request_handler = DefaultRequestHandler(
            agent_executor=llm_executor,
            task_store=InMemoryTaskStore(),
            push_config_store=llm_push_config_store,
            push_sender=llm_push_sender
        )
        llm_server = A2AStarletteApplication(
            agent_card=llm_card, http_handler=llm_request_handler
        )
        llm_app = llm_server.build()
        # endregion

        # region Main app setup
        main_app = Starlette()

        main_app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://localhost:\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # region Config endpoints
        async def get_config(request: Request):
            config = dynamic_agent_executor.get_config()
            return JSONResponse(config)

        async def post_config(request: Request):
            try:
                data = await request.json()
                success, error = dynamic_agent_executor.update_config(data)
                if success:
                    return JSONResponse({"status": "success", "message": "Configuration updated"})
                else:
                    return JSONResponse({"status": "error", "message": error}, status_code=400)
            except Exception as e:
                return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

        async def delete_config(request: Request):
            dynamic_agent_executor.reset_config()
            return JSONResponse({"status": "success", "message": "Configuration reset to default"})
        # endregion

        # region Traditional endpoints
        async def get_traditional_outage(request: Request):
            try:
                messages = await get_traditional_outage_messages()
                return JSONResponse(messages)
            except Exception as e:
                logger.error(f"Error getting traditional outage data: {e}")
                return JSONResponse({"error": "Failed to retrieve outage data"}, status_code=500)

        async def get_traditional_energy(request: Request):
            try:
                messages = await get_traditional_energy_messages()
                return JSONResponse(messages)
            except Exception as e:
                logger.error(f"Error getting traditional energy data: {e}")
                return JSONResponse({"error": "Failed to retrieve energy data"}, status_code=500)

        async def get_traditional_industry(request: Request):
            try:
                messages = await get_traditional_industry_messages()
                return JSONResponse(messages)
            except Exception as e:
                logger.error(f"Error getting traditional industry data: {e}")
                return JSONResponse({"error": "Failed to retrieve industry data"}, status_code=500)

        async def get_traditional_energy_trends(request: Request):
            try:
                messages = await get_traditional_energy_trends_messages()
                return JSONResponse(messages)
            except Exception as e:
                logger.error(f"Error getting traditional energy trends data: {e}")
                return JSONResponse({"error": "Failed to retrieve energy trends data"}, status_code=500)

        async def get_traditional_timeline(request: Request):
            try:
                messages = await get_traditional_timeline_messages()
                return JSONResponse(messages)
            except Exception as e:
                logger.error(f"Error getting traditional timeline data: {e}")
                return JSONResponse({"error": "Failed to retrieve timeline data"}, status_code=500)
        # endregion

        # region Route registration and app mount
        main_app.add_route("/agent/config", get_config, methods=["GET"])
        main_app.add_route("/agent/config", post_config, methods=["POST"])
        main_app.add_route("/agent/config", delete_config, methods=["DELETE"])
        main_app.add_route("/traditional", get_traditional_outage, methods=["GET"])
        main_app.add_route("/traditional/energy", get_traditional_energy, methods=["GET"])
        main_app.add_route("/traditional/trends", get_traditional_energy_trends, methods=["GET"])
        main_app.add_route("/traditional/timeline", get_traditional_timeline, methods=["GET"])
        main_app.add_route("/traditional/industry", get_traditional_industry, methods=["GET"])

        # Serve RAG source documents so clients can open source links.
        rag_docs_dir = Path(__file__).resolve().parent / "core" / "rag_docs"
        if rag_docs_dir.exists():
            main_app.mount("/rag_docs", StaticFiles(directory=str(rag_docs_dir)), name="rag_docs")

        main_app.mount("/agent", selected_primary_agent_app)
        main_app.mount("/llm", llm_app)
        # endregion
        # endregion

        import uvicorn
        uvicorn.run(main_app, host=host, port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()

"""
uv run __main__.py --agent-backend dynamic
uv run __main__.py --agent-backend streaming
"""
