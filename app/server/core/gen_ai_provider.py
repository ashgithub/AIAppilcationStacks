# region Imports
import os
from typing import Any
import httpx
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_oci.embeddings import OCIGenAIEmbeddings
from oci_openai import OciUserPrincipalAuth
#OpenAI SDK migration
from oci_genai_auth import OciUserPrincipalAuth
from openai import OpenAI, AsyncOpenAI
from langchain_openai import ChatOpenAI

from database.connections import RAGDBConnection

from dotenv import load_dotenv
load_dotenv()
# endregion Imports

# region Constants
EMBED_MODEL = "cohere.embed-v4.0"
DEFAULT_CHAT_MODEL = "xai.grok-4-fast-non-reasoning"
# endregion Constants

# region LLM Provider
class GenAIProvider:
    """Singleton provider for OCI GenAI LLM clients."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass

    def _build_default_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if os.getenv("COMPARTMENT_ID"):
            headers["opc-compartment-id"] = os.getenv("COMPARTMENT_ID")
            headers["CompartmentId"] = os.getenv("COMPARTMENT_ID")
        if os.getenv("OCI_OPENAI_PROJECT"):
            headers["OpenAI-Project"] = os.getenv("OCI_OPENAI_PROJECT")
        return headers

    def build_oci_client(self, model_id: str | None = None, model_kwargs: dict[str, Any] | None = None):
        resolved_model_id = model_id or os.getenv("GEN_AI_MODEL", DEFAULT_CHAT_MODEL)
        resolved_model_kwargs = model_kwargs or {}

        # client = ChatOpenAI(
        #     base_url=os.getenv("SERVICE_ENDPOINT", "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/v1"),
        #     http_client=httpx.Client(
        #         auth=OciUserPrincipalAuth(profile_name=os.getenv("AUTH_PROFILE"))
        #     ),
        #     default_headers=self._build_default_headers(),
        #     api_key=os.getenv("OPENAI_INNO_DEV1"),
        #     model=resolved_model_id,
        #     store=False,
        #     **resolved_model_kwargs,
        # )

        client = ChatOpenAI(
            model=resolved_model_id,
            openai_api_base="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1",
            openai_api_key="OCI",
            default_headers=self._build_default_headers(),
            http_client=httpx.Client(
                auth=OciUserPrincipalAuth(profile_name=os.getenv("AUTH_PROFILE"))
            ),
            http_async_client=httpx.AsyncClient(
                auth=OciUserPrincipalAuth(profile_name=os.getenv("AUTH_PROFILE"))
            ),
            use_responses_api=True,
            **resolved_model_kwargs,
        )

        return client
    
    def update_oci_client(
        self,
        client: ChatOpenAI,
        model_id: str | None = None,
        model_kwargs: dict[str, Any] | None = None
    ):
        client.model_name = model_id or self.get_default_chat_model()
        client.model_kwargs = model_kwargs or {}
# endregion LLM Provider

# region Embedding Provider
class GenAIEmbedProvider:
    """Singleton provider for OCI GenAI Embeddings with optional PDF processing capabilities."""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if GenAIEmbedProvider._initialized:
            return
        GenAIEmbedProvider._initialized = True
        
        self.embed_client = OCIGenAIEmbeddings(
            model_id=EMBED_MODEL,
            service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
            compartment_id=os.getenv("COMPARTMENT_ID"),
            auth_profile=os.getenv("AUTH_PROFILE")
        )
        # Populated when load_pdf() runs.
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

    def load_and_insert_pdf(self, pdf_path: str, db_conn: RAGDBConnection, chunk_size: int = 300, chunk_overlap: int = 200):
        """Load PDF, generate embeddings, and insert into database."""
        embeddings = self.load_pdf(pdf_path, chunk_size, chunk_overlap)

        with db_conn.get_connection() as conn:
            db_conn.insert_embedding(conn, embeddings, self.texts, self.splits)

        return embeddings

    def load_all_rag_documents(self, db_conn: RAGDBConnection, chunk_size: int = 300, chunk_overlap: int = 200):
        """Load all PDF documents from the rag_docs directory and insert into database."""
        rag_docs_dir = "./core/rag_docs/"

        with db_conn.get_connection() as conn:
            db_conn.create_table(conn)

        pdf_files = [f for f in os.listdir(rag_docs_dir) if f.endswith('.pdf')]
        loaded_count = 0

        for pdf_file in pdf_files:
            pdf_path = os.path.join(rag_docs_dir, pdf_file)
            print(f"Loading and indexing {pdf_file}...")
            try:
                self.load_and_insert_pdf(pdf_path, db_conn, chunk_size, chunk_overlap)
                loaded_count += 1
            except Exception as e:
                print(f"Error loading {pdf_file}: {e}")

        print(f"Successfully loaded and indexed {loaded_count} documents.")
# endregion Embedding Provider
