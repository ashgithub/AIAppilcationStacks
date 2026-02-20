import logging
import httpx

import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, BasePushNotificationSender, InMemoryPushNotificationConfigStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2ui.extension.a2ui_extension import get_a2ui_agent_extension
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import JSONResponse
from starlette.requests import Request

from chat_app.llm_executor import OutageEnergyLLMExecutor
from chat_app.main_llm import OCIOutageEnergyLLM
from dynamic_app.dynamic_agents_graph import DynamicGraph
from dynamic_app.dynamic_graph_executor import DynamicGraphExecutor
from dynamic_app.configs.a2a_config_provider import (
    dynamic_agent_capabilities,
    get_widget_catalog,
    get_widget_schema
)

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
def main(host, port):
    try:
        base_url = f"http://{host}:{port}"

        #region Agent executor setup
        agent_base_url = f"{base_url}/agent"
        agent_card = AgentCard(
            name="Restaurant Agent",
            description="This agent helps find restaurants based on user criteria.",
            url=agent_base_url,
            version="1.0.0",
            default_input_modes=DynamicGraph.SUPPORTED_CONTENT_TYPES,
            default_output_modes=DynamicGraph.SUPPORTED_CONTENT_TYPES,
            capabilities=dynamic_agent_capabilities,
            skills=[get_widget_catalog,get_widget_schema],
        )

        agent_executor = DynamicGraphExecutor(base_url=agent_base_url)

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

        #region LLM executor setup
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

        llm_executor = OutageEnergyLLMExecutor()

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

        #region main app setup
        main_app = Starlette()

        main_app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://localhost:\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        #region config endpoints
        async def get_config(request: Request):
            config = agent_executor.get_config()
            return JSONResponse(config)

        async def post_config(request: Request):
            try:
                data = await request.json()
                success, error = agent_executor.update_config(data)
                if success:
                    return JSONResponse({"status": "success", "message": "Configuration updated"})
                else:
                    return JSONResponse({"status": "error", "message": error}, status_code=400)
            except Exception as e:
                return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

        async def delete_config(request: Request):
            agent_executor.reset_config()
            return JSONResponse({"status": "success", "message": "Configuration reset to default"})
        
        #region app mount
        main_app.add_route("/agent/config", get_config, methods=["GET"])
        main_app.add_route("/agent/config", post_config, methods=["POST"])
        main_app.add_route("/agent/config", delete_config, methods=["DELETE"])

        # main_app.mount("/static", StaticFiles(directory="images"), name="static")
        main_app.mount("/agent", agent_app)
        main_app.mount("/llm", llm_app)

        import uvicorn
        uvicorn.run(main_app, host=host, port=port)
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
