"""
Generate tag recommendations for artworks and save to CSV.

This script:
1. Retrieves artworks from the fabritius table (with embeddings)
2. For each artwork, generates top N tag recommendations based on similarity
3. Saves results to CSV for analysis or later use

The core recommendation logic is reusable in the web app (detail.py).

Usage:
    Adjust the constants in main() (LIMIT, OFFSET, TOP_TAGS, OUTPUT_PATH)
    Then run: python preprocessing/generate_tag_recommendations.py
"""

from backend.supabase_client import SupabaseClient
from loguru import logger
import pandas as pd
import json
from datetime import datetime
from pathlib import Path


def get_artworks_with_embeddings(db: SupabaseClient, limit: int = None, offset: int = 0) -> list:
    """Get artworks that have caption embeddings.
    
    Args:
        db: Supabase client
        limit: Maximum number of artworks to retrieve (None = all, uses pagination)
        offset: Number of artworks to skip
        
    Returns:
        List of artwork dictionaries with inventarisnummer, metadata, and caption_embedding
    """
    try:
        if limit is None:
            # Fetch all artworks using pagination (Supabase default limit is 1000)
            all_artworks = []
            batch_size = 1000
            current_offset = offset
            
            logger.info("Fetching all artworks with embeddings (using pagination)...")
            
            while True:
                query = db.client.table("fabritius")\
                    .select("inventarisnummer, beschrijving_titel, beschrijving_kunstenaar, caption_embedding")\
                    .not_.is_("caption_embedding", "null")\
                    .limit(batch_size)\
                    .offset(current_offset)
                
                response = query.execute()
                
                if not response.data:
                    break
                
                all_artworks.extend(response.data)
                logger.info(f"Fetched {len(all_artworks)} artworks so far...")
                
                # If we got fewer than batch_size, we've reached the end
                if len(response.data) < batch_size:
                    break
                
                current_offset += batch_size
            
            logger.info(f"Found {len(all_artworks)} total artworks with embeddings")
            return all_artworks
        else:
            # Fetch specific limit
            query = db.client.table("fabritius")\
                .select("inventarisnummer, beschrijving_titel, beschrijving_kunstenaar, caption_embedding")\
                .not_.is_("caption_embedding", "null")\
                .limit(limit)
            
            if offset:
                query = query.offset(offset)
                
            response = query.execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} artworks with embeddings")
                return response.data
            else:
                logger.warning("No artworks with embeddings found")
                return []
            
    except Exception as e:
        logger.error(f"Error fetching artworks: {e}")
        return []


def recommend_tags_for_embedding(db: SupabaseClient, artwork_embedding: list, artwork_id: str, top_n: int = 10) -> dict:
    """Generate tag recommendations for an artwork based on its embedding.
    
    This is the core recommendation logic that can be reused in the web app.
    Uses direct vector similarity query - no stored procedure needed.
    
    Args:
        db: Supabase client
        artwork_embedding: The caption embedding vector of the artwork
        artwork_id: Inventarisnummer of the artwork
        top_n: Number of top tags to recommend
        
    Returns:
        Dictionary with artwork_id and recommended tags list
        Example: {
            'inventarisnummer': '12345',
            'recommended_tags': [
                {'label': 'man', 'similarity': 0.85},
                {'label': 'vrouw', 'similarity': 0.82}
            ]
        }
    """
    try:
        # Direct similarity query on iconographic_tags
        # Using <=> operator for cosine distance (1 - distance = similarity)
        response = db.client.rpc('match_iconographic_tags', {
            'query_embedding': artwork_embedding,
            'match_count': top_n
        }).execute()
        
        if not response.data:
            logger.warning(f"No tags recommended for artwork {artwork_id}")
            return {
                'inventarisnummer': artwork_id,
                'recommended_tags': []
            }
        
        # Format the results
        recommended_tags = [
            {
                'label': tag['label'],
                'similarity': round(tag['similarity'], 4),
                'tag_id': tag['id']
            }
            for tag in response.data
        ]
        
        return {
            'inventarisnummer': artwork_id,
            'recommended_tags': recommended_tags
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations for {artwork_id}: {e}")
        return {
            'inventarisnummer': artwork_id,
            'recommended_tags': []
        }


def generate_recommendations_batch(db: SupabaseClient, artworks: list, top_n: int = 10) -> pd.DataFrame:
    """Generate tag recommendations for multiple artworks.
    
    Args:
        db: Supabase client
        artworks: List of artwork dictionaries
        top_n: Number of top tags to recommend per artwork
        
    Returns:
        DataFrame with columns: inventarisnummer, titel, kunstenaar, tag_1, tag_2, ..., tag_N
        Each tag column contains a JSON string: {"tag": "...", "score": 0.85}
    """
    results = []
    
    total = len(artworks)
    logger.info(f"Generating recommendations for {total} artworks...")
    
    for idx, artwork in enumerate(artworks, 1):
        artwork_id = artwork['inventarisnummer']
        artwork_embedding = artwork['caption_embedding']
        
        # Generate recommendations using the embedding
        recommendations = recommend_tags_for_embedding(db, artwork_embedding, artwork_id, top_n)
        
        # Flatten the data for CSV format
        row = {
            'inventarisnummer': artwork_id,
            'titel': artwork.get('beschrijving_titel', ''),
            'kunstenaar': artwork.get('beschrijving_kunstenaar', '')
        }
        
        # Add top N tags as separate columns with mini-JSON format
        for i, tag in enumerate(recommendations['recommended_tags'], 1):
            row[f'tag_{i}'] = json.dumps({"tag": tag['label'], "score": tag['similarity']}, ensure_ascii=False)
        
        # Fill missing columns if fewer than top_n tags were recommended
        for i in range(len(recommendations['recommended_tags']) + 1, top_n + 1):
            row[f'tag_{i}'] = ''
        
        results.append(row)
        
        # Progress update every 10 artworks
        if idx % 10 == 0:
            logger.info(f"Progress: {idx}/{total} ({idx/total*100:.1f}%)")
    
    df = pd.DataFrame(results)
    logger.info(f"Generated recommendations for {len(df)} artworks")
    
    return df


def save_recommendations_to_csv(df: pd.DataFrame, output_path: str = None) -> str:
    """Save recommendations DataFrame to CSV.
    
    Args:
        df: DataFrame with recommendations
        output_path: Custom output path (optional)
        
    Returns:
        Path to saved CSV file
    """
    if output_path is None:
        # Default: data/processed/tag_recommendations_YYYYMMDD_HHMMSS.csv
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/processed/tag_recommendations_{timestamp}.csv"
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV with proper quoting for JSON strings
    df.to_csv(output_path, index=False, encoding='utf-8-sig', quoting=1)  # quoting=1 is csv.QUOTE_ALL
    logger.info(f"Saved recommendations to: {output_path}")
    
    return output_path


def main():

    # run as: python -m preprocessing.generate_tag_recommendations
    # ============================================
    # CONFIGURATION - Adjust these values as needed
    # ============================================
    
    # Number of artworks to process (None = all artworks with embeddings)
    LIMIT = None
    
    # Number of artworks to skip (useful for processing in batches)
    OFFSET = 0
    
    # Number of top tags to recommend per artwork
    TOP_TAGS = 20
    
    # Custom output path (None = auto-generate with timestamp)
    # Example: "data/processed/my_recommendations.csv"
    OUTPUT_PATH = "data/processed/tag_recommendations_ALL.csv"
    
    # ============================================
    
    db = SupabaseClient()
    
    # Get artworks with embeddings
    logger.info("\n" + "="*60)
    logger.info("STEP 1: Fetching artworks with embeddings")
    logger.info("="*60)
    
    artworks = get_artworks_with_embeddings(db, limit=LIMIT, offset=OFFSET)
    
    if not artworks:
        logger.error("No artworks found. Exiting.")
        return
    
    # Generate recommendations
    logger.info("\n" + "="*60)
    logger.info(f"STEP 2: Generating top {TOP_TAGS} tag recommendations")
    logger.info("="*60)
    
    df = generate_recommendations_batch(db, artworks, top_n=TOP_TAGS)
    
    # Save to CSV
    logger.info("\n" + "="*60)
    logger.info("STEP 3: Saving to CSV")
    logger.info("="*60)
    
    output_path = save_recommendations_to_csv(df, OUTPUT_PATH)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✅ COMPLETE")
    logger.info("="*60)
    logger.info(f"Processed: {len(df)} artworks")
    logger.info(f"Tags per artwork: {TOP_TAGS}")
    logger.info(f"Output: {output_path}")
    logger.info("="*60 + "\n")
    
    # Show sample
    logger.info("Sample results:")
    sample_cols = ['inventarisnummer', 'titel', 'tag_1', 'tag_2', 'tag_3']
    logger.info(f"\n{df[sample_cols].head(5).to_string()}")


if __name__ == "__main__":
    main()
