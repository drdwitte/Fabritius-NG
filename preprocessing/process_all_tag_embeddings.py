"""
Process ALL tag embeddings in batches with progress updates.

Usage:
    python preprocessing/process_all_tag_embeddings.py
"""

import sys
sys.path.insert(0, 'C:\\Users\\Dieter\\OneDrive - UGent\\Development\\KMSKB_Software\\Fabritius-NG')

from backend.supabase_client import SupabaseClient
from backend.llms import LLMClient
from loguru import logger
from datetime import datetime, timedelta


def get_embedding_stats(db: SupabaseClient) -> tuple[int, int]:
    """Get current embedding statistics."""
    try:
        total_response = db.client.table("iconographic_tags")\
            .select("id", count="exact")\
            .execute()
        
        embedded_response = db.client.table("iconographic_tags")\
            .select("id", count="exact")\
            .not_.is_("tag_embedding", "null")\
            .execute()
        
        total = total_response.count or 0
        embedded = embedded_response.count or 0
        
        return embedded, total
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return 0, 0


def get_tags_without_embeddings(db: SupabaseClient, limit: int, offset: int) -> list:
    """Get tags without embeddings."""
    try:
        response = db.client.table("iconographic_tags")\
            .select("id, label, description")\
            .is_("tag_embedding", "null")\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching tags: {e}")
        return []


def generate_and_update_embedding(db: SupabaseClient, llm: LLMClient, tag: dict) -> bool:
    """Generate and update a single tag embedding."""
    try:
        # Generate embedding with context
        text = f"iconographic subject: {tag['label']}"
        embedding = llm.get_embedding(text)
        
        if not embedding:
            return False
        
        # Update in database
        response = db.client.table("iconographic_tags")\
            .update({"tag_embedding": embedding})\
            .eq("id", tag['id'])\
            .execute()
        
        return response.data is not None
    except Exception as e:
        logger.error(f"Error processing tag '{tag['label']}': {e}")
        return False


def main():
    db = SupabaseClient()
    llm = LLMClient()
    
    # Get initial stats
    embedded, total = get_embedding_stats(db)
    logger.info(f"\n{'='*60}")
    logger.info(f"Initial Status: {embedded}/{total} tags embedded ({embedded/total*100:.1f}%)")
    logger.info(f"{'='*60}\n")
    
    batch_size = 100
    offset = 0
    total_processed = 0
    total_successful = 0
    total_failed = 0
    start_time = datetime.now()
    
    while True:
        # Get next batch
        tags = get_tags_without_embeddings(db, limit=batch_size, offset=0)  # Always offset 0 because we process them
        
        if not tags:
            logger.info("\n✅ All tags processed!")
            break
        
        batch_start = datetime.now()
        successful = 0
        failed = 0
        
        logger.info(f"\n--- Processing batch of {len(tags)} tags ---")
        
        for idx, tag in enumerate(tags, 1):
            if generate_and_update_embedding(db, llm, tag):
                successful += 1
                total_successful += 1
            else:
                failed += 1
                total_failed += 1
            
            total_processed += 1
            
            # Show progress every 10 tags
            if idx % 10 == 0:
                current_embedded = embedded + total_successful
                print(f"\r[{current_embedded}/{total}] {tag['label'][:40]:<40}", end='', flush=True)
        
        batch_duration = datetime.now() - batch_start
        
        # Update current status
        current_embedded = embedded + total_successful
        progress_pct = (current_embedded / total * 100) if total > 0 else 0
        
        logger.info(f"\n✓ Batch completed: {successful} success, {failed} failed")
        logger.info(f"📊 Progress: {current_embedded}/{total} embedded ({progress_pct:.1f}%)")
        logger.info(f"⏱️  Batch time: {batch_duration.total_seconds():.1f}s")
        
        # Estimate remaining time
        if total_processed > 0:
            avg_time = (datetime.now() - start_time) / total_processed
            remaining = total - current_embedded
            est_remaining = avg_time * remaining
            est_completion = datetime.now() + est_remaining
            logger.info(f"⏰ Estimated completion: {est_completion.strftime('%H:%M:%S')} (in {est_remaining})")
    
    # Final summary
    total_duration = datetime.now() - start_time
    final_embedded, final_total = get_embedding_stats(db)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🎉 COMPLETE!")
    logger.info(f"{'='*60}")
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Successful: {total_successful}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Final status: {final_embedded}/{final_total} embedded")
    logger.info(f"Total time: {total_duration}")
    logger.info(f"Average: {total_duration/total_processed if total_processed > 0 else 0}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()
