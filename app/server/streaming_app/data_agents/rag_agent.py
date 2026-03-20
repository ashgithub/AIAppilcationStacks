import array
from langchain.tools import tool

from core.gen_ai_provider import GenAIEmbedProvider
from database.connections import RAGDBConnection

from dotenv import load_dotenv

# region Environment
load_dotenv()
# endregion Environment

# region Helpers
def build_context_snippet(results: list[dict]) -> str:
    """Format retrieved chunks for prompt context."""
    if not results:
        return "No relevant documents found."
    context_parts = []
    for i, r in enumerate(results, 1):
        snippet = r["text"].replace("\n", " ")
        context_parts.append(f"[{i}] (Source: {r['source']}) {snippet}")
    return "\n\n".join(context_parts)
# endregion Helpers

# region Tool
@tool()
async def semantic_search(query: str, top_k: int = 3) -> str:
    """Perform cosine-similarity search over available document chunks:
    [epa_actions_for_outages (US), fema_outage_flyer (US), general_disaster_manual (MEX)]
    """
    
    embed_provider = GenAIEmbedProvider()
    db_conn = RAGDBConnection()
    
    try:
        query_response = embed_provider.embed_client.embed_query(query)
        query_vec = array.array("f", query_response)
        
        with db_conn.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(f"""
                SELECT text, vector_distance(vec, :1, COSINE) AS distance, source
                FROM {db_conn.table_prefix}_embedding
                ORDER BY distance
                FETCH FIRST {top_k} ROWS ONLY
            """, [query_vec])
            
            rows = cursor.fetchall()
            results = [{"text": r[0], "distance": r[1], "source": r[2]} for r in rows]
            cursor.close()
        
        return build_context_snippet(results)
    except Exception as e:
        return f"Error performing semantic search: {str(e)}"
# endregion Tool
