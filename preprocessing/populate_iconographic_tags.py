"""
Populate iconographic_tags table with tags from the existing 'tags' table
and generate embeddings for each tag.

This is a one-time setup script to:
1. Copy tags from 'tags' table to 'iconographic_tags' table
2. Generate embeddings for each tag label
3. Store embeddings for later similarity-based recommendations

Usage:
    python preprocessing/populate_iconographic_tags.py [--stats-only]
"""

from backend.supabase_client import SupabaseClient
from backend.llms import LLMClient
from loguru import logger
from datetime import datetime, timedelta
import argparse


def copy_tags_to_iconographic_table(db: SupabaseClient) -> int:
    """Copy all tags from 'tags' table to 'iconographic_tags' table.
    
    Returns:
        Number of tags copied
    """
    try:
        # Get all tags from 'tags' table using pagination
        all_tags = []
        batch_size = 1000
        offset = 0
        
        while True:
            response = db.client.table("tags")\
                .select("label, description, created_at")\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            if not response.data:
                break
                
            all_tags.extend(response.data)
            logger.info(f"Fetched {len(response.data)} tags (total: {len(all_tags)})")
            
            if len(response.data) < batch_size:
                break
                
            offset += batch_size
        
        if not all_tags:
            logger.warning("No tags found in 'tags' table")
            return 0
        
        logger.info(f"Found {len(all_tags)} tags in 'tags' table")
        
        # Insert into iconographic_tags (on conflict do nothing - idempotent)
        # Convert to format for iconographic_tags
        iconographic_tags = [
            {
                "label": tag.get("label"),
                "description": tag.get("description"),
                "created_at": tag.get("created_at"),
                "source": "fabritius_iconographic_tags"
            }
            for tag in all_tags
        ]
        
        # Upsert to iconographic_tags in batches
        batch_size = 500
        for i in range(0, len(iconographic_tags), batch_size):
            batch = iconographic_tags[i:i+batch_size]
            response = db.client.table("iconographic_tags")\
                .upsert(batch, on_conflict="label")\
                .execute()
            logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} tags")
        
        logger.info(f"Successfully copied {len(all_tags)} tags to iconographic_tags table")
        return len(all_tags)
        
    except Exception as e:
        logger.error(f"Error copying tags: {e}")
        return 0


def get_tags_without_embeddings(db: SupabaseClient, limit: int = 100, offset: int = 0) -> list:
    """Get tags that don't have embeddings yet.
    
    Args:
        db: Supabase client
        limit: Maximum number of tags to return
        offset: Number of tags to skip
        
    Returns:
        List of tag dictionaries with id and label
    """
    try:
        response = db.client.table("iconographic_tags")\
            .select("id, label, description")\
            .is_("tag_embedding", "null")\
            .limit(limit)\
            .offset(offset)\
            .execute()
        
        if response.data:
            logger.info(f"Found {len(response.data)} tags without embeddings (offset: {offset})")
            return response.data
        else:
            logger.info(f"No tags without embeddings found (offset: {offset})")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching tags: {e}")
        return []


def generate_tag_embedding(llm: LLMClient, label: str, description: str = None) -> list:
    """Generate embedding for a tag.
    
    Args:
        llm: LLM client
        label: Tag label (e.g., "man met baard")
        description: Optional tag description for more context
        
    Returns:
        Embedding vector as list of floats
    """
    try:
        # Add context to help with semantic similarity
        # Option A: Simple context
        text = f"iconographic subject: {label}"
        
        # Option B: With description (if available)
        # if description:
        #     text = f"iconographic subject: {label}. {description}"
        
        embedding = llm.get_embedding(text)
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding for '{label}': {e}")
        return None


def update_tag_embedding(db: SupabaseClient, tag_id: int, embedding: list) -> bool:
    """Update tag with embedding.
    
    Args:
        db: Supabase client
        tag_id: Tag ID
        embedding: Embedding vector
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = db.client.table("iconographic_tags")\
            .update({"tag_embedding": embedding})\
            .eq("id", tag_id)\
            .execute()
        
        return response.data is not None
        
    except Exception as e:
        logger.error(f"Error updating embedding for tag {tag_id}: {e}")
        return False


def process_tag_embeddings(db: SupabaseClient, tags: list) -> tuple[int, int]:
    """Generate and store embeddings for multiple tags.
    
    Args:
        db: Supabase client
        tags: List of tag dictionaries
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    llm = LLMClient()
    total = len(tags)
    successful = 0
    failed = 0
    start_time = datetime.now()
    runtimes = []
    
    logger.info(f"Starting to process {total} tag embeddings...")
    
    for idx, tag in enumerate(tags, 1):
        item_start = datetime.now()
        logger.info(f"Processing tag {idx}/{total}: '{tag['label']}'")
        
        try:
            # Generate embedding
            embedding = generate_tag_embedding(
                llm=llm,
                label=tag['label'],
                description=tag.get('description')
            )
            
            if embedding:
                # Update in database
                success = update_tag_embedding(
                    db=db,
                    tag_id=tag['id'],
                    embedding=embedding
                )
                
                if success:
                    successful += 1
                    logger.info(f"✓ Updated '{tag['label']}' ({idx}/{total})")
                else:
                    failed += 1
                    logger.error(f"× Failed to update '{tag['label']}' in database")
            else:
                failed += 1
                logger.error(f"× No embedding generated for '{tag['label']}'")
                
        except Exception as e:
            failed += 1
            logger.error(f"× Error processing '{tag['label']}': {e}")
            continue
        
        # Calculate timing
        item_duration = datetime.now() - item_start
        runtimes.append(item_duration)
        avg_runtime = sum(runtimes, timedelta()) / len(runtimes)
        
        # Progress summary
        logger.info(f"Progress: {successful} successful, {failed} failed, {total-idx} remaining")
        logger.info(f"Time: This item: {item_duration.total_seconds():.1f}s, Average: {avg_runtime.total_seconds():.1f}s")
        
        if total - idx > 0:
            est_remaining = avg_runtime * (total - idx)
            est_completion = datetime.now() + est_remaining
            logger.info(f"Estimated completion at: {est_completion.strftime('%H:%M:%S')}")
    
    # Final summary
    total_duration = datetime.now() - start_time
    logger.info("\n=== Tag Embedding Generation Summary ===")
    logger.info(f"Total time: {total_duration}")
    if runtimes:
        logger.info(f"Average time per tag: {sum(runtimes, timedelta()) / len(runtimes)}")
    logger.info(f"Successful: {successful}/{total} ({(successful/total)*100:.1f}%)")
    logger.info(f"Failed: {failed}/{total}")
    
    return successful, failed


def get_embedding_stats(db: SupabaseClient) -> tuple[int, int]:
    """Get statistics about embedded and unembedded tags.
    
    Returns:
        Tuple of (embedded_count, total_count)
    """
    try:
        # Get total count
        total_response = db.client.table("iconographic_tags")\
            .select("id", count="exact")\
            .execute()
        
        # Get embedded count
        embedded_response = db.client.table("iconographic_tags")\
            .select("id", count="exact")\
            .not_.is_("tag_embedding", "null")\
            .execute()
        
        total = total_response.count or 0
        embedded = embedded_response.count or 0
        
        return embedded, total
        
    except Exception as e:
        logger.error(f"Error fetching embedding stats: {e}")
        return 0, 0


def main():
    parser = argparse.ArgumentParser(description='Populate iconographic tags with embeddings')
    parser.add_argument('-n', '--number', type=int, default=100,
                       help='Number of tags to process per batch (default: 100)')
    parser.add_argument('-o', '--offset', type=int, default=0,
                       help='Skip first N tags (default: 0)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show statistics without processing')
    parser.add_argument('--copy-tags', action='store_true',
                       help='Copy tags from tags table to iconographic_tags table')
    args = parser.parse_args()
    
    db = SupabaseClient()
    
    # Copy tags if requested
    if args.copy_tags:
        logger.info("\n=== Copying Tags ===")
        copied = copy_tags_to_iconographic_table(db)
        logger.info(f"Copied {copied} tags to iconographic_tags table\n")
    
    # Get current statistics
    embedded, total = get_embedding_stats(db)
    logger.info("\n=== Current Embedding Status ===")
    logger.info(f"Total iconographic tags: {total}")
    logger.info(f"Already embedded: {embedded}")
    logger.info(f"Remaining to embed: {total - embedded}")
    
    if total > 0:
        progress = (embedded / total) * 100
        logger.info(f"Progress: {progress:.1f}%\n")
    else:
        logger.info("Progress: No tags found\n")
    
    if args.stats_only:
        return
    
    # Process embeddings
    tags = get_tags_without_embeddings(db, limit=args.number, offset=args.offset)
    
    if tags:
        logger.info(f"Starting embedding generation for {len(tags)} tags...")
        successful, failed = process_tag_embeddings(db, tags)
        logger.info(f"\nFinished: {successful} successful, {failed} failed")
    else:
        logger.info("No tags without embeddings found to process")


if __name__ == "__main__":
    main()
