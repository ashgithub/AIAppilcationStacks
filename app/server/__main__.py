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
from database.semantic_cache import (
    GraphSemanticCache,
    get_nl2graph_semantic_cache_summary,
)
from database.connections import RAGDBConnection

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_public_base_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned.rstrip("/")


@click.command()
@click.option("--host", default=os.getenv("SERVER_BIND_HOST", "127.0.0.1"))
@click.option("--port", default=int(os.getenv("SERVER_BIND_PORT", "10002")))
def main(host, port):
    try:
        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            timeout=60,
            tracer_provider=TracerProvider(),
        )

        internal_base_url = f"http://{host}:{port}"
        public_base_url = normalize_public_base_url(os.getenv("PUBLIC_BASE_URL"))
        base_url = public_base_url or internal_base_url

        # region Agent executor setup
        agent_base_url = f"{base_url}/agent/"
        agent_card = AgentCard(
            name="Energy Outage Agent",
            description="This agent helps analyze power outages, energy statistics, and industry performance.",
            url=agent_base_url,
            version="1.0.0",
            default_input_modes=DynamicGraph.SUPPORTED_CONTENT_TYPES,
            default_output_modes=DynamicGraph.SUPPORTED_CONTENT_TYPES,
            capabilities=dynamic_agent_capabilities,
            skills=[get_widget_catalog,get_widget_schema],
        )

        agent_executor = DynamicGraphExecutor(
            base_url=agent_base_url,
            langfuse_client=langfuse_client,
        )

        httpx_client = httpx.AsyncClient()
        agent_push_config_store = InMemoryPushNotificationConfigStore()
        agent_push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=agent_push_config_store
        )
        
        agent_request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
            push_config_store=agent_push_config_store,
            push_sender=agent_push_sender
        )

        agent_server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=agent_request_handler
        )

        agent_app = agent_server.build()
        # endregion

        # region LLM executor setup
        llm_base_url = f"{base_url}/llm/"
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

        llm_executor = OutageEnergyLLMExecutor(langfuse_client)

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

        # region Agent semantic cache endpoints
        async def get_agent_semantic_cache(request: Request):
            try:
                limit_raw = request.query_params.get("limit", "25")
                limit = max(1, min(int(limit_raw), 100))
                summary = get_nl2graph_semantic_cache_summary(limit=limit)
                return JSONResponse({"status": "success", "cache": summary})
            except Exception as e:
                logger.error(f"Error getting agent semantic cache info: {e}")
                return JSONResponse({"status": "error", "message": "Failed to retrieve semantic cache info"}, status_code=500)

        async def clear_agent_semantic_cache(request: Request):
            try:
                cache = GraphSemanticCache()
                deleted_rows = cache.clear_cache()
                return JSONResponse(
                    {
                        "status": "success",
                        "message": "Semantic cache was cleared.",
                        "deleted_rows": deleted_rows,
                    }
                )
            except Exception as e:
                logger.error(f"Error clearing agent semantic cache: {e}")
                return JSONResponse({"status": "error", "message": "Failed to clear semantic cache"}, status_code=500)
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
        main_app.add_route("/agent/cache/semantic", get_agent_semantic_cache, methods=["GET"])
        main_app.add_route("/agent/cache/semantic", clear_agent_semantic_cache, methods=["DELETE"])
        main_app.add_route("/traditional", get_traditional_outage, methods=["GET"])
        main_app.add_route("/traditional/energy", get_traditional_energy, methods=["GET"])
        main_app.add_route("/traditional/trends", get_traditional_energy_trends, methods=["GET"])
        main_app.add_route("/traditional/timeline", get_traditional_timeline, methods=["GET"])
        main_app.add_route("/traditional/industry", get_traditional_industry, methods=["GET"])

        # Serve RAG source documents so clients can open source links.
        rag_docs_dir = Path(__file__).resolve().parent / "core" / "rag_docs"
        if rag_docs_dir.exists():
            main_app.mount("/rag_docs", StaticFiles(directory=str(rag_docs_dir)), name="rag_docs")

        main_app.mount("/agent", agent_app)
        main_app.mount("/llm", llm_app)
        # endregion
        # endregion

        # Warm up DB connection so first user request avoids connection setup latency.
        try:
            RAGDBConnection().warmup_connection()
            logger.info("Database connection warm-up complete")
        except Exception as warmup_exc:
            logger.warning(f"Database warm-up skipped due to error: {warmup_exc}")

        import uvicorn
        uvicorn.run(main_app, host=host, port=port)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
