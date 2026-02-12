import os
from typing import Any
from langchain_oci import ChatOCIGenAI
from dotenv import load_dotenv
load_dotenv()

class GenAIProvider:
    def __init__(self):
        pass

    def build_oci_client(self, model_id:str="xai.grok-4-fast-non-reasoning", model_kwargs:dict[str,Any] = {}):
        client = ChatOCIGenAI(
            model_id=model_id,
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs=model_kwargs,
            auth_profile="DEFAULT",
        )

        return client
    
    def update_oci_client(
        self, 
        client:ChatOCIGenAI, 
        model_id:str="xai.grok-4-fast-non-reasoning", 
        model_kwargs:dict[str,Any] = {}
    ):
        client.model_id=model_id
        client.model_kwargs=model_kwargs