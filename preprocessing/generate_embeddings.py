#note in Supabase UI moet de kolom aangemaakt worden als volgt:
#ALTER TABLE fabritius ADD COLUMN caption_embedding vector(1536); (anders is het een open dimensie en dat werkt niet)
#note openai vectoren zijn dim:1536 (ada-002) dhttps://platform.openai.com/docs/api-reference/embeddings/object

# Available OpenAI embedding models:
# - text-embedding-ada-002 (1536 dimensions) [default, recommended] <::::::::::::::::::::::::::::::
# - text-embedding-3-small (1536 dimensions)
# - text-embedding-3-large (3072 dimensions)
# Legacy models (not recommended):
# - text-similarity-ada-001 (1024 dimensions)
# - text-search-ada-doc-001 (1024 dimensions)

from backend.supabase_client import SupabaseClient
from loguru import logger
from backend.llms import LLMClient
from datetime import datetime, timedelta
import argparse

def generate_test_embedding(text: str, model: str = LLMClient.DEFAULT_EMBEDDING_MODEL) -> list:
    """TEMP TEST: Generate embedding for a test text using GPT.
    
    Args:
        text: The text to embed
        model: The OpenAI model to use for embedding (default: text-embedding-ada-002)
    """
    try:
        llm = LLMClient()
        embedding = llm.get_embedding(text, model=model)
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

def get_n_unembedded_artworks(db: SupabaseClient, n: int = 5, offset: int = 0) -> list:
    """Get n artworks that have captions but no embeddings."""
    try:
        response = (db.client.table("fabritius")
                   .select("inventarisnummer, gpt_vision_caption")
                   .neq("gpt_vision_caption", None)
                   .neq("gpt_vision_caption", "")  # Exclude empty strings
                   .is_("caption_embedding", "null") #no embedding yet
                   .limit(n)
                   .offset(offset)
                   .execute())
        
        # Check if we got any results
        if response.data:
            artworks = response.data
            logger.info(f"Found {len(artworks)} artworks without embeddings (offset: {offset})")
            return artworks
        else:
            logger.info(f"No unembedded artworks found (offset: {offset})")
            return None
    
    except Exception as e:
        logger.error(f"Error fetching artworks: {e}")
        return None

def update_artwork_embedding(db: SupabaseClient, inventory_number: str, embedding: list) -> bool:
    """Update the embedding for an artwork."""
    try:
        response = (db.client.table("fabritius")
                   .update({"caption_embedding": embedding})
                   .eq("inventarisnummer", inventory_number)
                   .execute())
        
        if response.data:
            logger.info(f"Updated embedding for {inventory_number}")
            return True
        return False
    
    except Exception as e:
        logger.error(f"Error updating embedding: {e}")
        return False

def process_artwork_embeddings(db: SupabaseClient, artworks: list) -> None:
    """Process and update embeddings for multiple artworks."""
    total = len(artworks)
    successful = 0
    failed = 0
    start_time = datetime.now()
    runtimes = []

    logger.info(f"Starting to process {total} artworks...")
    
    for idx, artwork in enumerate(artworks, 1):
        item_start = datetime.now()
        logger.info(f"Processing artwork {idx}/{total}: {artwork['inventarisnummer']}")

        try:
            # Generate embedding from caption
            embedding = generate_test_embedding(artwork['gpt_vision_caption'])

            if embedding:
                success = update_artwork_embedding(
                    db=db,
                    inventory_number=artwork['inventarisnummer'],
                    embedding=embedding
                )
                if success:
                    successful += 1
                    logger.info(f"✓ Updated {artwork['inventarisnummer']} ({idx}/{total})")
                else:
                    failed += 1
                    logger.error(f"× Failed to update {artwork['inventarisnummer']} in database")
            else:
                failed += 1
                logger.error(f"× No embedding generated for {artwork['inventarisnummer']}")

        except Exception as e:
            failed += 1
            logger.error(f"× Error processing {artwork['inventarisnummer']}: {e}")
            continue

        # Calculate timing for this iteration
        item_duration = datetime.now() - item_start
        runtimes.append(item_duration)
        avg_runtime = sum(runtimes, timedelta()) / len(runtimes)
        
        # Progress summary
        logger.info(f"Progress: {successful} successful, {failed} failed, {total-idx} remaining")
        logger.info(f"Time: This item: {item_duration.seconds}s, Average: {avg_runtime.seconds}s")
        
        if total-idx > 0:
            est_remaining = avg_runtime * (total-idx)
            est_completion = datetime.now() + est_remaining
            logger.info(f"Estimated completion at: {est_completion.strftime('%H:%M:%S')}")

def get_embedding_stats(db: SupabaseClient) -> tuple[int, int]:
    """Get statistics about embedded and unembedded artworks."""
    try:
        # Get total count of artworks with captions
        total_response = (db.client.table("fabritius")
                        .select("inventarisnummer", count="exact")  # Select just one column for efficiency
                        .not_.is_("gpt_vision_caption", None)
                        .execute())
        
        # Get count of embedded artworks
        embedded_response = (db.client.table("fabritius")
                           .select("inventarisnummer", count="exact")  # Select just one column for efficiency
                           .not_.is_("gpt_vision_caption", None)
                           .not_.is_("caption_embedding", None)
                           .execute())
        
        # Count the records in the response data
        total = total_response.count or 0
        embedded = embedded_response.count or 0
        
        return embedded, total
    
    except Exception as e:
        logger.error(f"Error fetching embedding stats: {e}")
        return 0, 0


def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for artwork captions')
    parser.add_argument('-n', '--number', type=int, default=5,
                       help='Number of artworks to process (default: 5)')
    parser.add_argument('-o', '--offset', type=int, default=0,
                       help='Skip first N artworks (default: 0)')
    parser.add_argument('--stats', action='store_true',
                       help='Only show statistics without processing')
    args = parser.parse_args()

    db = SupabaseClient()
    
    # Get current statistics
    # Get current statistics
    embedded, total = get_embedding_stats(db)
    logger.info("\n=== Current Embedding Status ===")
    logger.info(f"Total artworks with captions: {total}")
    logger.info(f"Already embedded: {embedded}")
    logger.info(f"Remaining to embed: {total - embedded}")
    
    # Add check to prevent division by zero
    if total > 0:
        progress = (embedded/total) * 100
        logger.info(f"Progress: {progress:.1f}%\n")
    else:
        logger.info("Progress: No artworks found with captions\n")

    if args.stats:
        return

    artworks = get_n_unembedded_artworks(db, n=args.number, offset=args.offset)
    if artworks:
        process_artwork_embeddings(db, artworks)
    else:
        logger.info("No unembedded artworks found to process")

if __name__ == "__main__":
    main()