#!/usr/bin/env python3
"""
Setup script to load and index all RAG documents into the database.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.gen_ai_provider import GenAIEmbedProvider
from database.connections import RAGDBConnection

def main():
    """Load all RAG documents and insert into database."""
    print("Initializing RAG document indexing...")

    try:
        embed_provider = GenAIEmbedProvider()
        db_conn = RAGDBConnection()

        embed_provider.load_all_rag_documents(db_conn)

        print("\nRAG setup complete! You can now use semantic search.")

    except Exception as e:
        print(f"Error during RAG setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()