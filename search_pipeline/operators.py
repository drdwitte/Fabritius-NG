"""
Operator execution functions.

This module contains the backend execution logic for all search operators:
- Semantic Search: Vector search based on text query
- Metadata Filter: Filter by artwork metadata
- Similarity Search: Image-to-text + vector search
"""

import traceback
from loguru import logger
from backend.supabase_client import SupabaseClient
from backend.caption_generator import generate_caption_from_base64
from config import settings


def execute_semantic_search(params: dict) -> tuple:
    """
    Execute Semantic Search operator by calling backend vector search.
    
    Args:
        params: Operator parameters containing:
            - query_text (str): Search query text (required)
            - result_mode (str): 'top_n', 'last_n', or 'similarity_range'
            - n_results (int): Number of results for top_n/last_n modes
            - similarity_min (float): Min similarity for similarity_range mode
            - similarity_max (float): Max similarity for similarity_range mode
    
    Returns:
        Tuple of (preview_results, total_count):
            - preview_results: List of artwork dicts for display (max settings.preview_results_count)
            - total_count: Total number of results after filtering (for result count badge)
    """
    try:
        logger.info("="*60)
        logger.info("SEMANTIC SEARCH - START")
        logger.info("="*60)
        
        # 1. Validate required params
        query_text = params.get('query_text', '').strip()
        if not query_text:
            logger.error("Semantic Search: query_text is required")
            return [], 0
        
        result_mode = params.get('result_mode', 'top_n')
        
        logger.info(f"Query text: '{query_text}'")
        logger.info(f"Result mode: {result_mode}")
        logger.info(f"Full params: {params}")
        logger.info(f"Preview count: {settings.preview_results_count}")
        
        # 2. Call backend vector search (get many results for filtering)
        logger.info("Step 1: Calling vector_search with limit=1000...")
        db = SupabaseClient()
        vector_results = db.vector_search(query_text, limit=1000)
        
        if not vector_results:
            logger.warning(f"No vector search results for query: {query_text}")
            return [], 0
        
        logger.info(f"Step 1 complete: Vector search returned {len(vector_results)} results")
        
        # 3. Apply result_mode filtering (get ALL filtered results first for count)
        logger.info(f"Step 2: Applying {result_mode} filter...")
        filtered_results_all = vector_results
        
        if result_mode == 'top_n':
            n_results = int(params.get('n_results', 100))
            filtered_results_all = vector_results[:n_results]
            logger.info(f"Step 2 complete: top_n filter applied, {len(filtered_results_all)} total results (n={n_results})")
            
        elif result_mode == 'last_n':
            n_results = int(params.get('n_results', 100))
            filtered_results_all = vector_results[-n_results:] if len(vector_results) >= n_results else vector_results
            logger.info(f"Step 2 complete: last_n filter applied, {len(filtered_results_all)} total results (n={n_results})")
            
        elif result_mode == 'similarity_range':
            similarity_min = params.get('similarity_min', 0.0)
            similarity_max = params.get('similarity_max', 1.0)
            filtered_results_all = [
                r for r in vector_results 
                if similarity_min <= r.get('similarity', 0) <= similarity_max
            ]
            logger.info(f"Step 2 complete: similarity_range filter applied [{similarity_min}-{similarity_max}], {len(filtered_results_all)} total results")
        
        # Store total count BEFORE slicing for preview
        total_count = len(filtered_results_all)
        
        if not filtered_results_all:
            logger.warning("No results after applying filters")
            return [], 0
        
        # 4. Slice to preview count for display
        preview_results = filtered_results_all[:settings.preview_results_count]
        logger.info(f"Showing {len(preview_results)} preview results out of {total_count} total")
        
        # 5. Get inventory numbers from preview results
        inv_numbers = [r['inventarisnummer'] for r in preview_results]
        
        # 6. Fetch full artwork details from database
        full_results = db.get_artworks(
            page=1,
            items_per_page=len(inv_numbers),
            search_params={'inventory_number': inv_numbers}
        )
        
        logger.info(f"Fetched full details for {len(full_results['items'])} artworks")
        
        # 7. Format for display (map backend fields to UI format)
        formatted_results = []
        for artwork in full_results['items']:
            # Construct full image URL
            image_path = artwork.get('imageOpacLink', '')
            if image_path and not image_path.startswith('http'):
                image_url = f"{settings.image_base_url}{image_path}" if image_path.startswith('/') else f"{settings.image_base_url}/{image_path}"
            else:
                image_url = image_path
            
            formatted_results.append({
                'id': artwork.get('inventarisnummer', 'N/A'),
                'title': artwork.get('beschrijving_titel', 'Untitled'),
                'artist': artwork.get('beschrijving_kunstenaar', 'Unknown Artist'),
                'year': artwork.get('beschrijving_datering', 'N/A'),
                'inventory': artwork.get('inventarisnummer', 'N/A'),
                'image_url': image_url  # Use image_url for consistency
            })
        
        logger.info(f"Semantic Search completed: {len(formatted_results)} preview results, {total_count} total results")
        logger.info("="*60)
        logger.info("SEMANTIC SEARCH - COMPLETE")
        logger.info("="*60)
        return formatted_results, total_count
        
    except Exception as e:
        logger.error(f"Error executing Semantic Search: {e}")
        traceback.print_exc()
        return [], 0


def execute_metadata_filter(params: dict) -> tuple:
    """
    Execute Metadata Filter operator by calling backend with search filters.
    
    Args:
        params: Operator parameters containing:
            - artist (str): Artist name (partial match)
            - title (str): Work title (partial match)
            - inventory_number (str): Inventory number (partial match)
            - year_range (list): [min_year, max_year] or [None, None]
            - source (list): Collection sources (multiselect)
    
    Returns:
        Tuple of (preview_results, total_count)
    """
    try:
        logger.info("="*60)
        logger.info("METADATA FILTER - START")
        logger.info("="*60)
        
        # Build search_params dict from operator params
        search_params = {}
        
        if artist := params.get('artist', '').strip():
            search_params['artist'] = artist
            logger.info(f"Filter: artist = '{artist}'")
        
        if title := params.get('title', '').strip():
            search_params['title'] = title
            logger.info(f"Filter: title = '{title}'")
        
        if inv_num := params.get('inventory_number', '').strip():
            search_params['inventory_number'] = inv_num
            logger.info(f"Filter: inventory_number = '{inv_num}'")
        
        # Year range filtering (ensure integers)
        year_range = params.get('year_range', [None, None])
        if year_range and (year_range[0] is not None or year_range[1] is not None):
            min_year = int(year_range[0]) if year_range[0] is not None else None
            max_year = int(year_range[1]) if year_range[1] is not None else None
            search_params['year_range'] = [min_year, max_year]
            logger.info(f"Filter: year_range = {min_year} - {max_year}")
        
        # Source filtering (multiselect)
        source = params.get('source', [])
        if source:
            search_params['source'] = source
            logger.info(f"Filter: source = {source}")
        
        logger.info(f"Total filters applied: {len(search_params)}")
        
        # Call backend - get all results first for count
        logger.info("Step 1: Querying database with filters...")
        db = SupabaseClient()
        
        # Get total count by querying with large page size
        full_results = db.get_artworks(
            page=1,
            items_per_page=10000,
            search_params=search_params
        )
        
        total_count = full_results['total_items']
        all_items = full_results['items']
        
        logger.info(f"Step 1 complete: Database returned {total_count} matching artworks")
        
        if not all_items:
            logger.warning("No results after applying metadata filters")
            return [], 0
        
        # Slice to preview count for display
        preview_results = all_items[:settings.preview_results_count]
        
        # Format for display
        formatted_results = []
        for artwork in preview_results:
            # Construct full image URL
            image_path = artwork.get('imageOpacLink', '')
            if image_path and not image_path.startswith('http'):
                image_url = f"{settings.image_base_url}{image_path}" if image_path.startswith('/') else f"{settings.image_base_url}/{image_path}"
            else:
                image_url = image_path
            
            formatted_results.append({
                'id': artwork.get('inventarisnummer', 'N/A'),
                'title': artwork.get('beschrijving_titel', 'Untitled'),
                'artist': artwork.get('beschrijving_kunstenaar', 'Unknown Artist'),
                'year': artwork.get('beschrijving_datering', 'N/A'),
                'inventory': artwork.get('inventarisnummer', 'N/A'),
                'image_url': image_url  # Changed from 'image' for consistency
            })
        
        logger.info(f"Metadata Filter completed: {len(formatted_results)} preview results, {total_count} total results")
        logger.info("="*60)
        logger.info("METADATA FILTER - COMPLETE")
        logger.info("="*60)
        return formatted_results, total_count
        
    except Exception as e:
        logger.error(f"Error executing Metadata Filter: {e}")
        traceback.print_exc()
        return [], 0


def execute_similarity_search(params: dict) -> tuple:
    """
    Execute Similarity Search operator by generating caption from image and doing vector search.
    
    Args:
        params: Operator parameters containing:
            - query_image (dict): {'filename': str, 'data': base64_str} (required)
            - result_mode (str): 'top_n', 'last_n', or 'similarity_range'
            - n_results (int): Number of results for top_n/last_n modes
            - similarity_min (float): Min similarity for similarity_range mode
            - similarity_max (float): Max similarity for similarity_range mode
    
    Returns:
        Tuple of (preview_results, total_count)
    """
    try:
        logger.info("="*60)
        logger.info("SIMILARITY SEARCH - START")
        logger.info("="*60)
        
        # 1. Validate required params
        query_image = params.get('query_image')
        if not query_image or not isinstance(query_image, dict):
            logger.error("Similarity Search: query_image is required")
            return [], 0
        
        image_data = query_image.get('data')
        if not image_data:
            logger.error("Similarity Search: image data is missing")
            return [], 0
        
        result_mode = params.get('result_mode', 'top_n')
        filename = query_image.get('filename', 'unknown')
        
        logger.info(f"Uploaded image: {filename}")
        logger.info(f"Image data size: {len(image_data)} bytes (base64)")
        logger.info(f"Image data preview: {image_data[:20]}...")
        logger.info(f"Result mode: {result_mode}")
        
        # Log params without full image data
        params_log = params.copy()
        if 'query_image' in params_log and isinstance(params_log['query_image'], dict):
            img_copy = params_log['query_image'].copy()
            if 'data' in img_copy:
                img_copy['data'] = f"{img_copy['data'][:20]}... ({len(img_copy['data'])} chars)"
            params_log['query_image'] = img_copy
        logger.info(f"Params: {params_log}")
        
        # 2. Generate caption from uploaded image
        logger.info("Step 1: Generating caption from uploaded image using GPT-4 Vision...")
        caption = generate_caption_from_base64(image_data)
        
        if not caption:
            logger.error("Step 1 failed: Could not generate caption from image")
            return [], 0
        
        caption_preview = caption[:200] + '...' if len(caption) > 200 else caption
        logger.info(f"Step 1 complete: Generated caption ({len(caption)} chars): {caption_preview}")
        
        # 3. Call backend vector search using caption (same as semantic search)
        logger.info("Step 2: Calling vector_search with caption...")
        db = SupabaseClient()
        vector_results = db.vector_search(caption, limit=1000)
        
        if not vector_results:
            logger.warning(f"Step 2: No vector search results for image caption")
            return [], 0
        
        logger.info(f"Step 2 complete: Vector search returned {len(vector_results)} results")
        
        # 4. Apply result_mode filtering (same logic as semantic search)
        logger.info(f"Step 3: Applying {result_mode} filter...")
        filtered_results_all = vector_results
        
        if result_mode == 'top_n':
            n_results = int(params.get('n_results', 100))
            filtered_results_all = vector_results[:n_results]
            logger.info(f"Step 3 complete: top_n filter applied, {len(filtered_results_all)} total results (n={n_results})")
            
        elif result_mode == 'last_n':
            n_results = int(params.get('n_results', 100))
            filtered_results_all = vector_results[-n_results:] if len(vector_results) >= n_results else vector_results
            logger.info(f"Step 3 complete: last_n filter applied, {len(filtered_results_all)} total results (n={n_results})")
            
        elif result_mode == 'similarity_range':
            similarity_min = params.get('similarity_min', 0.0)
            similarity_max = params.get('similarity_max', 1.0)
            filtered_results_all = [
                r for r in vector_results 
                if similarity_min <= r.get('similarity', 0) <= similarity_max
            ]
            logger.info(f"Step 3 complete: similarity_range filter applied [{similarity_min}-{similarity_max}], {len(filtered_results_all)} total results")
        
        # Store total count BEFORE slicing for preview
        total_count = len(filtered_results_all)
        
        if not filtered_results_all:
            logger.warning("No results after applying filters")
            return [], 0
        
        # 5. Slice to preview count for display
        preview_results = filtered_results_all[:settings.preview_results_count]
        logger.info(f"Showing {len(preview_results)} preview results out of {total_count} total")
        
        # 6. Get inventory numbers from preview results
        inv_numbers = [r['inventarisnummer'] for r in preview_results]
        
        # 7. Fetch full artwork details from database
        full_results = db.get_artworks(
            page=1,
            items_per_page=len(inv_numbers),
            search_params={'inventory_number': inv_numbers}
        )
        
        logger.info(f"Fetched full details for {len(full_results['items'])} artworks")
        
        # 8. Format for display
        formatted_results = []
        for artwork in full_results['items']:
            # Construct full image URL
            image_path = artwork.get('imageOpacLink', '')
            if image_path and not image_path.startswith('http'):
                image_url = f"{settings.image_base_url}{image_path}" if image_path.startswith('/') else f"{settings.image_base_url}/{image_path}"
            else:
                image_url = image_path
            
            formatted_results.append({
                'id': artwork.get('inventarisnummer', 'N/A'),
                'title': artwork.get('beschrijving_titel', 'Untitled'),
                'artist': artwork.get('beschrijving_kunstenaar', 'Unknown Artist'),
                'year': artwork.get('beschrijving_datering', 'N/A'),
                'inventory': artwork.get('inventarisnummer', 'N/A'),
                'image_url': image_url  # Changed from 'image' for consistency
            })
        
        logger.info(f"Similarity Search completed: {len(formatted_results)} preview results, {total_count} total results")
        logger.info("="*60)
        logger.info("SIMILARITY SEARCH - COMPLETE")
        logger.info("="*60)
        return formatted_results, total_count
        
    except Exception as e:
        logger.error(f"Error executing Similarity Search: {e}")
        traceback.print_exc()
        return [], 0
