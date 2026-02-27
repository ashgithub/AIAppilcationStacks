import os
from typing import Any
from langchain_oci import ChatOCIGenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_oci.embeddings import OCIGenAIEmbeddings

from core.common_struct import EMBED_MODEL

from dotenv import load_dotenv
load_dotenv()


class GenAIProvider:
    """Singleton provider for OCI GenAI LLM clients."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass

    def build_oci_client(self, model_id:str="xai.grok-4-fast-non-reasoning", model_kwargs:dict[str,Any] = {}):
        client = ChatOCIGenAI(
            model_id=model_id,
            service_endpoint=os.getenv("SERVICE_ENDPOINT"),
            compartment_id=os.getenv("COMPARTMENT_ID"),
            model_kwargs=model_kwargs,
            auth_profile="API-USER",
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

class GenAIEmbedProvider:
    """Singleton provider for OCI GenAI Embeddings with optional PDF processing capabilities."""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Avoid re-initialization on subsequent calls
        if GenAIEmbedProvider._initialized:
            return
        GenAIEmbedProvider._initialized = True
        
        self.embed_client = OCIGenAIEmbeddings(
            model_id=EMBED_MODEL,
            service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
            compartment_id=os.getenv("COMPARTMENT_ID"),
        )
        # PDF processing attributes - initialized when load_pdf is called
        self.docs = None
        self.splits = None
        self.texts = None
        self.embed_response = None
    
    def load_pdf(self, pdf_path: str, chunk_size: int = 300, chunk_overlap: int = 200):
        """Load and process a PDF file for embedding.
        
        Args:
            pdf_path: Path to the PDF file to load.
            chunk_size: Size of text chunks for splitting.
            chunk_overlap: Overlap between chunks.
        
        Returns:
            List of embeddings for the document chunks.
        """
        loader = PyPDFLoader(pdf_path)
        self.docs = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True
        )
        self.splits = text_splitter.split_documents(self.docs)
        self.texts = [chunk.page_content for chunk in self.splits]
        self.embed_response = self.embed_client.embed_documents(self.texts)
        
        return self.embed_response