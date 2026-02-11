from backend.supabase_client import SupabaseClient
from loguru import logger
from backend.llms import LLMClient

#def vector_search(db: SupabaseClient, query_text: str, limit: int = 5) -> list:
#    """Search artworks using vector similarity."""
#    try:
#        # Generate embedding for query
#        llm = LLMClient()
#        query_embedding = llm.get_embedding(query_text)
#        
#        if not query_embedding:
#            logger.error("Failed to generate embedding for query")
#            return []
        
#       # Call stored procedure through RPC
#        response = (db.client.rpc('vector_search', {
#            'query_embedding': query_embedding,
#            'match_count': limit
#        }).execute())
        
#        return response.data if response.data else []
        
#    except Exception as e:
#        logger.error(f"Error in vector search: {e}")
#        return []

def main():
    # Test query
    test_query = "ik wil een afbeelding waarop iemand vermoord wordt"
    
    # Initialize database client and search
    db = SupabaseClient()
    results = db.vector_search(test_query, limit=3)
    
    # Display results
    if results:
        logger.info(f"\nFound {len(results)} similar artworks:")
        for idx, result in enumerate(results, 3):
            logger.info(f"\n{idx}. Inventory number: {result['inventarisnummer']}")
            logger.info(f"   Similarity: {result['similarity']:.2%}")
            logger.info(f"   Image: http://193.190.214.119{result['imageOpacLink']}")
    else:
        logger.info("No results found")

if __name__ == "__main__":
    main()