from nicegui import ui, app
from ui_components.config import BROWN, OPERATORS, IMAGE_BASE_URL, PREVIEW_RESULTS_COUNT
import json
import uuid
from loguru import logger
from typing import List, Dict, Optional

# TODO: Future refactoring - Class-based operators
# Currently operators are identified by name strings (e.g., 'Metadata Filter').
# Future improvement: Create operator classes with execute() methods that can be
# mapped from operator names (Strategy pattern). This allows each operator type
# to have its own implementation logic while maintaining the same interface.
# Example: OPERATOR_CLASSES = {'Metadata Filter': MetadataFilterOperator, ...}

############################################
############### BACK-END ###################
############################################

# Global UI containers
results_display_container = None

class PipelineState:
    """
    Manages the state of the search pipeline.
    Each operator instance has a unique ID and can store parameters.
    """
    
    def __init__(self):
        self._operators: List[Dict] = []
    
    def _find_index(self, operator_id: str) -> int:
        """
        Private helper: finds the index of an operator by ID.
        Returns -1 if not found.
        """
        for i, op in enumerate(self._operators):
            if op['id'] == operator_id:
                return i
        return -1
    
    def add_operator(self, operator_name: str) -> str:
        """
        Adds an operator to the pipeline.
        Returns the unique ID of the operator instance.
        """
        # Generate a unique ID for the operator, 
        # 2 operators with same name can coexist and will have different IDs
        operator_id = str(uuid.uuid4())
        operator = {
            'id': operator_id,
            'name': operator_name,
            'params': {},
            'result_count': None  # None until first execution
        }
        self._operators.append(operator)
        logger.info(f"Added '{operator_name}': {[op['name'] for op in self._operators]}")
        return operator_id
    
    def remove_operator(self, operator_id: str) -> bool:
        """
        Removes an operator by ID.
        Returns True if removed, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            removed_name = self._operators[index]['name']
            self._operators.pop(index)
            logger.info(f"Removed '{removed_name}': {[op['name'] for op in self._operators]}")
            return True
        return False
    
    def get_operator(self, operator_id: str) -> Optional[Dict]:
        """
        Gets a single operator by ID.
        Returns a copy to prevent external mutation.
        """
        index = self._find_index(operator_id)
        if index != -1:
            return self._operators[index].copy()
        return None
    
    def get_all_operators(self) -> List[Dict]:
        """Returns a copy of all operators."""
        # op.copy makes a copy of each operator dict to prevent external mutation
        return [op.copy() for op in self._operators]
    
    def update_params(self, operator_id: str, params: Dict) -> bool:
        """
        Updates the parameters of an operator.
        Replaces the entire params dict.
        Returns True if updated, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators[index]['params'] = params
            return True
        return False
    
    def update_result_count(self, operator_id: str, count: int) -> bool:
        """
        Updates the result count for an operator after execution.
        Returns True if updated, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators[index]['result_count'] = count
            logger.info(f"Updated result count for operator {operator_id}: {count} results")
            return True
        return False
    
    def reorder(self, new_order: List[str]):
        """
        Reorders operators based on a list of IDs.
        Missing IDs are ignored.
        """
        #id_to_operator is a mapping to new index in operator List (uid -> operator dict)
        id_to_operator = {op['id']: op for op in self._operators}
        # Rebuild the operator list in the new order
        self._operators = [id_to_operator[op_id] for op_id in new_order if op_id in id_to_operator]
        logger.info(f"Reordered: {[op['name'] for op in self._operators]}")
        print(f"[Pipeline] Reordered: {[op['name'] for op in self._operators]}")
    
    def clear(self):
        """Removes all operators from the pipeline."""
        self._operators = []
    
    def to_json(self) -> str:
        """Export pipeline to JSON string."""
        return json.dumps(self._operators, indent=2)
    
    def from_json(self, json_string: str):
        """Import pipeline from JSON string."""
        self._operators = json.loads(json_string)

# Global state instance
pipeline_state = PipelineState()

# Initialize with default operators (NOTE: we will refactor this into class based operators later)
pipeline_state.add_operator('Metadata Filter')
pipeline_state.add_operator('Semantic Search')
pipeline_state.add_operator('Similarity Search')


############################################
############### FRONT-END ##################
############################################

# The main function in front-end are: 
# - render_search: renders the main search page with operator library and pipeline area
# - render_pipeline: renders the current pipeline in the pipeline area
# - show_operator_config: shows the configuration panel for a selected operator

# Global UI references
pipeline_area = None  # The UI area where the pipeline is rendered (with operator tiles, delete and drag buttons)
pipeline_name_input = None  # Reference to UI element with the name input field
config_panel = None  # Reference to UI Config panel: right-hand side panel for configuration of operators
results_area = None  # The UI area where search results are displayed
current_view = 'grid'  # Current results view: 'grid' or 'list'

# Mock data for results preview
MOCK_RESULTS = {
    'Metadata Filter': [
        {'id': '1', 'title': 'Self-Portrait with Flowered Hat', 'artist': 'James Ensor', 'year': '1883', 'inventory': 'ME001', 'image': 'https://loremflickr.com/400/400/painting?lock=1'},
        {'id': '2', 'title': 'The Entry of Christ into Brussels', 'artist': 'James Ensor', 'year': '1889', 'inventory': 'ME002', 'image': 'https://loremflickr.com/400/400/painting?lock=2'},
        {'id': '3', 'title': 'Skeletons Fighting Over a Pickled Herring', 'artist': 'James Ensor', 'year': '1891', 'inventory': 'ME003', 'image': 'https://loremflickr.com/400/400/painting?lock=3'},
        {'id': '4', 'title': 'The Intrigue', 'artist': 'James Ensor', 'year': '1890', 'inventory': 'ME004', 'image': 'https://loremflickr.com/400/400/painting?lock=4'},
        {'id': '5', 'title': 'Death and the Masks', 'artist': 'James Ensor', 'year': '1897', 'inventory': 'ME005', 'image': 'https://loremflickr.com/400/400/painting?lock=5'},
        {'id': '6', 'title': 'Woman Eating Oysters', 'artist': 'James Ensor', 'year': '1882', 'inventory': 'ME006', 'image': 'https://loremflickr.com/400/400/painting?lock=6'},
        {'id': '7', 'title': 'The Cathedral', 'artist': 'James Ensor', 'year': '1886', 'inventory': 'ME007', 'image': 'https://loremflickr.com/400/400/painting?lock=7'},
        {'id': '8', 'title': 'Russian Music', 'artist': 'James Ensor', 'year': '1881', 'inventory': 'ME008', 'image': 'https://loremflickr.com/400/400/painting?lock=8'},
        {'id': '9', 'title': 'The Consoling Virgin', 'artist': 'James Ensor', 'year': '1892', 'inventory': 'ME009', 'image': 'https://loremflickr.com/400/400/painting?lock=9'},
        {'id': '10', 'title': 'Attributes of the Studio', 'artist': 'James Ensor', 'year': '1889', 'inventory': 'ME010', 'image': 'https://loremflickr.com/400/400/painting?lock=10'},
    ],
    'Semantic Search': [
        {'id': '11', 'title': 'The Night Watch', 'artist': 'Rembrandt van Rijn', 'year': '1642', 'inventory': 'SS001', 'image': 'https://loremflickr.com/400/400/art?lock=11'},
        {'id': '12', 'title': 'The Anatomy Lesson', 'artist': 'Rembrandt van Rijn', 'year': '1632', 'inventory': 'SS002', 'image': 'https://loremflickr.com/400/400/art?lock=12'},
        {'id': '13', 'title': 'The Jewish Bride', 'artist': 'Rembrandt van Rijn', 'year': '1665', 'inventory': 'SS003', 'image': 'https://loremflickr.com/400/400/art?lock=13'},
        {'id': '14', 'title': 'Self Portrait', 'artist': 'Rembrandt van Rijn', 'year': '1669', 'inventory': 'SS004', 'image': 'https://loremflickr.com/400/400/art?lock=14'},
        {'id': '15', 'title': 'The Storm on the Sea', 'artist': 'Rembrandt van Rijn', 'year': '1633', 'inventory': 'SS005', 'image': 'https://loremflickr.com/400/400/art?lock=15'},
        {'id': '16', 'title': 'Belshazzar\'s Feast', 'artist': 'Rembrandt van Rijn', 'year': '1635', 'inventory': 'SS006', 'image': 'https://loremflickr.com/400/400/art?lock=16'},
        {'id': '17', 'title': 'The Syndics', 'artist': 'Rembrandt van Rijn', 'year': '1662', 'inventory': 'SS007', 'image': 'https://loremflickr.com/400/400/art?lock=17'},
        {'id': '18', 'title': 'The Abduction of Europa', 'artist': 'Rembrandt van Rijn', 'year': '1632', 'inventory': 'SS008', 'image': 'https://loremflickr.com/400/400/art?lock=18'},
        {'id': '19', 'title': 'The Return of the Prodigal Son', 'artist': 'Rembrandt van Rijn', 'year': '1669', 'inventory': 'SS009', 'image': 'https://loremflickr.com/400/400/art?lock=19'},
        {'id': '20', 'title': 'Danaë', 'artist': 'Rembrandt van Rijn', 'year': '1636', 'inventory': 'SS010', 'image': 'https://loremflickr.com/400/400/art?lock=20'},
    ],
    'Similarity Search': [
        {'id': '21', 'title': 'The Starry Night', 'artist': 'Vincent van Gogh', 'year': '1889', 'inventory': 'SI001', 'image': 'https://loremflickr.com/400/400/museum?lock=21'},
        {'id': '22', 'title': 'Sunflowers', 'artist': 'Vincent van Gogh', 'year': '1888', 'inventory': 'SI002', 'image': 'https://loremflickr.com/400/400/museum?lock=22'},
        {'id': '23', 'title': 'Irises', 'artist': 'Vincent van Gogh', 'year': '1889', 'inventory': 'SI003', 'image': 'https://loremflickr.com/400/400/museum?lock=23'},
        {'id': '24', 'title': 'The Bedroom', 'artist': 'Vincent van Gogh', 'year': '1888', 'inventory': 'SI004', 'image': 'https://loremflickr.com/400/400/museum?lock=24'},
        {'id': '25', 'title': 'Café Terrace at Night', 'artist': 'Vincent van Gogh', 'year': '1888', 'inventory': 'SI005', 'image': 'https://loremflickr.com/400/400/museum?lock=25'},
        {'id': '26', 'title': 'Wheatfield with Crows', 'artist': 'Vincent van Gogh', 'year': '1890', 'inventory': 'SI006', 'image': 'https://loremflickr.com/400/400/museum?lock=26'},
        {'id': '27', 'title': 'Almond Blossoms', 'artist': 'Vincent van Gogh', 'year': '1890', 'inventory': 'SI007', 'image': 'https://loremflickr.com/400/400/museum?lock=27'},
        {'id': '28', 'title': 'The Potato Eaters', 'artist': 'Vincent van Gogh', 'year': '1885', 'inventory': 'SI008', 'image': 'https://loremflickr.com/400/400/museum?lock=28'},
        {'id': '29', 'title': 'Self-Portrait', 'artist': 'Vincent van Gogh', 'year': '1889', 'inventory': 'SI009', 'image': 'https://loremflickr.com/400/400/museum?lock=29'},
        {'id': '30', 'title': 'The Night Café', 'artist': 'Vincent van Gogh', 'year': '1888', 'inventory': 'SI010', 'image': 'https://loremflickr.com/400/400/museum?lock=30'},
    ]
}


############################################
############ OPERATOR EXECUTION ############
############################################

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
            - preview_results: List of artwork dicts for display (max PREVIEW_RESULTS_COUNT)
            - total_count: Total number of results after filtering (for result count badge)
    """
    from backend.supabase_client import SupabaseClient
    
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
        logger.info(f"Preview count: {PREVIEW_RESULTS_COUNT}")
        
        # 2. Call backend vector search (get many results for filtering)
        logger.info("Step 1: Calling vector_search with limit=1000...")
        db = SupabaseClient()
        vector_results = db.vector_search(query_text, limit=1000)  # Get many results for filtering
        
        if not vector_results:
            logger.warning(f"No vector search results for query: {query_text}")
            return [], 0
        
        logger.info(f"Step 1 complete: Vector search returned {len(vector_results)} results")
        
        # 3. Apply result_mode filtering (get ALL filtered results first for count)
        logger.info(f"Step 2: Applying {result_mode} filter...")
        filtered_results_all = vector_results
        
        if result_mode == 'top_n':
            # Get all results that match this mode (for counting)
            n_results = int(params.get('n_results', 100))
            filtered_results_all = vector_results[:n_results]
            logger.info(f"Step 2 complete: top_n filter applied, {len(filtered_results_all)} total results (n={n_results})")
            
        elif result_mode == 'last_n':
            # Get all results that match this mode (for counting)
            n_results = int(params.get('n_results', 100))
            filtered_results_all = vector_results[-n_results:] if len(vector_results) >= n_results else vector_results
            logger.info(f"Step 2 complete: last_n filter applied, {len(filtered_results_all)} total results (n={n_results})")
            
        elif result_mode == 'similarity_range':
            # Filter by similarity range (get all matches for counting)
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
        preview_results = filtered_results_all[:PREVIEW_RESULTS_COUNT]
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
                # If relative path, prepend base URL
                image_url = f"{IMAGE_BASE_URL}{image_path}" if image_path.startswith('/') else f"{IMAGE_BASE_URL}/{image_path}"
            else:
                # Already absolute URL or empty
                image_url = image_path
            
            formatted_results.append({
                'id': artwork.get('inventarisnummer', 'N/A'),
                'title': artwork.get('beschrijving_titel', 'Untitled'),
                'artist': artwork.get('beschrijving_kunstenaar', 'Unknown Artist'),
                'year': artwork.get('beschrijving_datering', 'N/A'),
                'inventory': artwork.get('inventarisnummer', 'N/A'),
                'image': image_url
            })
        
        logger.info(f"Semantic Search completed: {len(formatted_results)} preview results, {total_count} total results")
        logger.info("="*60)
        logger.info("SEMANTIC SEARCH - COMPLETE")
        logger.info("="*60)
        return formatted_results, total_count
        
    except Exception as e:
        logger.error(f"Error executing Semantic Search: {e}")
        import traceback
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
    from backend.supabase_client import SupabaseClient
    
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
            # Convert to integers to prevent float values
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
            items_per_page=10000,  # Large enough to get all results
            search_params=search_params
        )
        
        total_count = full_results['total_items']
        all_items = full_results['items']
        
        logger.info(f"Step 1 complete: Database returned {total_count} matching artworks")
        
        if not all_items:
            logger.warning("No results after applying metadata filters")
            return [], 0
        
        # Slice to preview count for display
        preview_results = all_items[:PREVIEW_RESULTS_COUNT]
        
        # Format for display
        formatted_results = []
        for artwork in preview_results:
            # Construct full image URL
            image_path = artwork.get('imageOpacLink', '')
            if image_path and not image_path.startswith('http'):
                image_url = f"{IMAGE_BASE_URL}{image_path}" if image_path.startswith('/') else f"{IMAGE_BASE_URL}/{image_path}"
            else:
                image_url = image_path
            
            formatted_results.append({
                'id': artwork.get('inventarisnummer', 'N/A'),
                'title': artwork.get('beschrijving_titel', 'Untitled'),
                'artist': artwork.get('beschrijving_kunstenaar', 'Unknown Artist'),
                'year': artwork.get('beschrijving_datering', 'N/A'),
                'inventory': artwork.get('inventarisnummer', 'N/A'),
                'image': image_url
            })
        
        logger.info(f"Metadata Filter completed: {len(formatted_results)} preview results, {total_count} total results")
        logger.info("="*60)
        logger.info("METADATA FILTER - COMPLETE")
        logger.info("="*60)
        return formatted_results, total_count
        
    except Exception as e:
        logger.error(f"Error executing Metadata Filter: {e}")
        import traceback
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
    from backend.supabase_client import SupabaseClient
    from backend.caption_generator import generate_caption_from_base64
    
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
        preview_results = filtered_results_all[:PREVIEW_RESULTS_COUNT]
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
                image_url = f"{IMAGE_BASE_URL}{image_path}" if image_path.startswith('/') else f"{IMAGE_BASE_URL}/{image_path}"
            else:
                image_url = image_path
            
            formatted_results.append({
                'id': artwork.get('inventarisnummer', 'N/A'),
                'title': artwork.get('beschrijving_titel', 'Untitled'),
                'artist': artwork.get('beschrijving_kunstenaar', 'Unknown Artist'),
                'year': artwork.get('beschrijving_datering', 'N/A'),
                'inventory': artwork.get('inventarisnummer', 'N/A'),
                'image': image_url
            })
        
        logger.info(f"Similarity Search completed: {len(formatted_results)} preview results, {total_count} total results")
        logger.info("="*60)
        logger.info("SIMILARITY SEARCH - COMPLETE")
        logger.info("="*60)
        return formatted_results, total_count
        
    except Exception as e:
        logger.error(f"Error executing Similarity Search: {e}")
        import traceback
        traceback.print_exc()
        return [], 0


async def sync_from_dom():
    """Syncs the pipeline state from the DOM order (DOM is source of truth)."""
    # Use JavaScript to read the current order from DOM
    result = await ui.run_javascript('''
        const container = document.getElementById('pipeline-container');
        if (container) {
            return Array.from(container.children)
                .map(tile => tile.getAttribute('data-operator-id'))
                .filter(id => id !== null);
        }
        return [];
    ''', timeout=1.0)
    
    if result:
        pipeline_state.reorder(result)
        logger.info(f"Synced from DOM: {[op['name'] for op in pipeline_state.get_all_operators()]}")

async def save_pipeline(pipeline_name_input):
    """Shows a dialog to save the pipeline with a custom filename."""
    # Sync state from DOM before saving
    await sync_from_dom()
    
    # Get the pipeline name from the input field, or use default
    suggested_name = pipeline_name_input.value.strip() if pipeline_name_input and pipeline_name_input.value.strip() else 'Untitled Pipeline'
    
    def handle_save():
        """Save the pipeline with the given filename"""
        filename = filename_input.value.strip()
        if not filename:
            ui.notify('Please enter a filename')
            return
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            pipeline_json = pipeline_state.to_json()
            ui.download(pipeline_json.encode('utf-8'), filename)
            ui.notify(f'Saving {filename}...')
            dialog.close()
        except Exception as e:
            ui.notify(f'Error saving pipeline: {str(e)}')
    
    # Show a dialog to get the filename
    with ui.dialog() as dialog, ui.card().classes('p-6'):
        ui.label('Save Pipeline As').classes('text-lg font-bold mb-4')
        
        filename_input = ui.input(
            'Filename', 
            value=suggested_name,
            placeholder='my_pipeline'
        ).classes('w-80').on('keydown.enter', handle_save)
        
        ui.label('.json').classes('text-sm text-gray-500 mt-1')
        
        with ui.row().classes('w-full justify-end gap-2 mt-6'):
            ui.button('Cancel', on_click=dialog.close).props('flat color=grey')
            ui.button('Save', on_click=handle_save).props('color=none text-color=none').classes(f'bg-[{BROWN}] text-white')
    
    dialog.open()

async def load_pipeline(on_complete_callback):
    """Opens a file dialog to load a pipeline from a JSON file."""
    async def handle_upload(e):
        """Handle the uploaded file"""
        try:
            content = (await e.file.read()).decode('utf-8')
            pipeline_state.from_json(content)
            ui.notify('Pipeline loaded successfully!')
            on_complete_callback()  # Call the callback to re-render
        except Exception as ex:
            ui.notify(f'Error loading pipeline: {str(ex)}')
    
    # Create a hidden upload component
    upload = ui.upload(on_upload=handle_upload, auto_upload=True).props('accept=.json')
    upload.classes('hidden')
    # Trigger the file dialog
    upload.run_method('pickFiles')

def render_search(ui):
    """
    Renders the main search page, including the operator library and the pipeline area.
    """
    global pipeline_area, pipeline_name_input, results_area, results_display_container, last_preview_results, last_preview_operator_id
    
    # Load Sortable.js for drag-and-drop functionality
    ui.add_head_html("<script src=\"https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js\"></script>")    

    # Title & icon
    with ui.row().classes('items-center gap-2 mb-2'):
        ui.icon('search').classes('text-2xl text-amber-700')
        ui.label('Search Pipeline').classes('text-2xl font-bold')

    # Top bar: full width, left input, right buttons
    with ui.row().props('flat').classes('w-full flex items-center justify-between bg-white shadow-sm px-4 py-2 mb-4 rounded'):
        # Left: input field - store reference for later use
        pipeline_name_input = ui.input(
            placeholder='Pipeline name', 
            value='Untitled Pipeline'
        ).props('borderless dense').classes('w-64')
        # Right: buttons
        with ui.row().classes('gap-2'):
            icon_button('folder_open', 'Load', lambda: load_pipeline(render_pipeline))
            icon_button('save', 'Save', lambda: save_pipeline(pipeline_name_input))
            run_button('Run', lambda: ui.notify('Run clicked'))
    
    # Layout: operator library + operator chain + results preview
    with ui.row().classes('w-full gap-4 flex-nowrap'):
        # Sidebar (left), titled OPERATOR LIBRARY
        with ui.column().classes('w-64 p-4 bg-gray-50 rounded-xl gap-4 shrink-0'):
            ui.label('OPERATOR LIBRARY').classes('text-sm font-bold text-gray-600 mb-2')

            # Render operator cards from the centralized OPERATORS configuration
            for operator_name in OPERATORS.keys():
                operator_card(operator_name, lambda op=operator_name: (pipeline_state.add_operator(op), ui.notify(f'Added {op}'), clear_results(), render_pipeline()))

        # Main content (right)
        with ui.column().classes('flex-1 min-w-0 p-4'):
            ui.label('OPERATOR CHAIN').classes('text-xl font-bold mb-2')
            pipeline_area = ui.element('div').props('id=pipeline-area')  # Define the pipeline area
            render_pipeline()  # Render the pipeline
            
            # Results section
            ui.label('RESULTS').classes('text-xl font-bold mt-6 mb-2')
            results_area = ui.element('div').props('id=results-area').classes('w-full')
            
            # Restore cached results if available
            if last_preview_results and last_preview_operator_id:
                logger.info(f"Restoring cached results: {len(last_preview_results)} results")
                # Find operator name from id
                operator = pipeline_state.get_operator(last_preview_operator_id)
                operator_name = operator['name'] if operator else 'Unknown'
                render_results_ui(last_preview_results, last_preview_operator_id, operator_name)

def icon_button(icon_name, label, on_click, bg='bg-white', text='text-gray-700', border='border-gray-300'):
    """
    Creates an icon button with customizable icon, label, and click behavior.
    """
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes(f'h-9 px-3 flex items-center gap-x-8 rounded-md '
                f'border {border} {bg} {text} hover:bg-gray-50 py-1')
    with btn:
        ui.icon(icon_name).classes(f'{text} text-lg')
        ui.label(label).classes(f'{text} text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn

def run_button(label, on_click):
    """
    Creates a run button with a play icon, label, and click behavior.
    """
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes('h-9 px-3 flex items-center gap-x-8 rounded-md '
                'border border-gray-900 bg-black text-white hover:bg-gray-800 py-1')
    with btn:
        ui.icon('play_arrow').classes('text-white text-lg')
        ui.label(label).classes('text-white text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn

def operator_card(operator_name, on_add):
    """
    Creates an operator card using the centralized OPERATORS configuration.
    """
    operator = OPERATORS[operator_name]
    with ui.row().classes('w-full items-center gap-3 p-3 rounded-lg bg-white shadow hover:bg-gray-100 transition'):
        # Operator icon
        ui.icon(operator['icon']).classes(f'text-3xl text-[{BROWN}]')
        
        # Operator title + description
        with ui.column().classes('flex-1 items-start gap-0'):
            ui.label(operator_name).classes('text-base font-bold text-gray-800 mb-0')
            ui.label(operator['description']).classes('text-xs text-gray-500 mt-0')
        
        # Plus button to add operator
        (
            ui.button(icon='add', on_click=on_add)
                .props('round color=none text-color=none')
                .classes(f'bg-[{BROWN}] text-white ml-auto text-xs p-0')
        )

def render_pipeline():
    """
    Renders the pipeline area with all operators as tiles.
    """
    global pipeline_area
    pipeline = pipeline_state.get_all_operators()  # Get the current pipeline

    # Clear the pipeline area before re-rendering
    if pipeline_area is not None:
        pipeline_area.clear()

    # Create a new container for the pipeline
    with pipeline_area:
        pipeline_container = (
            ui.element('div')
            .props('id=pipeline-container')
            .classes('flex items-start gap-4 bg-white p-4 rounded')
        )

        with pipeline_container:
            for op_data in pipeline:
                op_id = op_data['id']
                op_name = op_data['name']
                operator = OPERATORS.get(op_name, {'icon': 'tune', 'description': 'Unknown operator'})
                icon = operator['icon']

                # Create a tile for the operator
                tile = (ui.element('div')
                    .classes('flex flex-col gap-0 px-2 py-2 rounded-xl bg-white shadow-sm min-w-[180px] hover:shadow-md transition')
                    .props(f'data-operator-id="{op_id}"')
                )

                with tile:
                    with ui.row().classes('items-center w-full'):
                        ui.icon('drag_indicator').classes('text-xl text-gray-400 cursor-move')
                        ui.icon(icon).classes('text-xl text-gray-700')
                        ui.label(op_name).classes('text-gray-800 font-medium ml-2')
                        # Preview icon to show results for this operator
                        ui.icon('visibility').classes(f'text-xl text-[{BROWN}] cursor-pointer ml-auto').on(
                            'click', lambda _, op_id=op_id, name=op_name: show_preview_for_operator(op_id, name)
                        ).tooltip('Preview Results')
                        # Settings icon to configure operator
                        ui.icon('settings').classes('text-xl text-gray-700 cursor-pointer').on(
                            'click', lambda _, op_id=op_id: show_operator_config(op_id)
                        ).tooltip('Configure')
                        # Delete icon with proper closure to avoid issues with lambda variable binding
                        ui.icon('delete').classes('text-xl text-red-500 cursor-pointer').on(
                            'click', lambda _, op_id=op_id, name=op_name, t=tile: delete_operator_by_id(op_id, name, t)
                        ).tooltip('Delete')

                    # Show actual operator parameters
                    params = op_data.get('params', {})
                    if params:
                        for param_name, param_value in list(params.items())[:3]:  # Show max 3 params
                            # Format the value nicely
                            if isinstance(param_value, dict) and 'filename' in param_value:
                                # For image type, show filename only (not base64 data)
                                display_value = f'📷 {param_value["filename"]}'
                            elif isinstance(param_value, list):
                                if all(isinstance(x, (int, float)) for x in param_value):
                                    # Convert to int for year ranges to avoid .0 display
                                    val0 = int(param_value[0]) if param_value[0] is not None else None
                                    val1 = int(param_value[1]) if param_value[1] is not None else None
                                    display_value = f"{val0} - {val1}"
                                else:
                                    display_value = ', '.join(str(v) for v in param_value[:3])
                                    if len(param_value) > 3:
                                        display_value += '...'
                            elif isinstance(param_value, float) and param_value.is_integer():
                                # Convert float to int if it has no decimal part (e.g., 15.0 -> 15)
                                display_value = str(int(param_value))
                            else:
                                display_value = str(param_value)[:30]
                            ui.label(f"{param_name}: {display_value}").classes('text-sm text-gray-400 italic w-full leading-tight mt-1')
                    else:
                        ui.label("No filters applied").classes('text-sm text-gray-400 italic w-full mt-2')
                    
                    # Show result count (None = not executed yet, int = actual count)
                    result_count = op_data.get('result_count')
                    if result_count is None:
                        count_text = "? results"
                    else:
                        count_text = f"{result_count} results"
                    
                    ui.label(count_text).classes(
                        f'inline-block mt-3 px-2 py-1 text-xs font-medium rounded-md bg-[{BROWN}] text-white'
                    )

    # Reinitialize Sortable.js for drag-and-drop functionality
    ui.run_javascript("""
    new Sortable(document.getElementById('pipeline-container'), {
        animation: 150,
        ghostClass: 'opacity-50'
    });
    """)

def delete_operator_by_id(operator_id: str, op_name: str, tile):
    """
    Deletes an operator from the pipeline by ID and removes its tile from the UI.
    
    Args:
        operator_id: The unique ID of the operator to delete
        op_name: The name of the operator (for notification)
        tile: The UI tile element to remove from the DOM
    """
    pipeline_state.remove_operator(operator_id)  # Remove the operator from the pipeline
    tile.delete()  # Remove the tile directly from the DOM
    ui.notify(f'Removed {op_name}')  # Notify the user
    clear_results()  # Clear results when pipeline changes
    render_pipeline()  # Re-render the pipeline

def show_operator_config(operator_id: str):
    """
    Shows a configuration panel for the selected operator.
    For operators with multiple filter options, allows dynamic adding/removing of filters.
    Loads existing parameters from the operator state.
    """
    global selected_operator, config_panel
    
    # Get the operator data from state
    operator_data = pipeline_state.get_operator(operator_id)
    if not operator_data:
        ui.notify('Operator not found')
        return
    
    op_name = operator_data['name']
    existing_params = operator_data.get('params', {})
    selected_operator = operator_id
    
    # Remove existing panel completely if it exists
    if config_panel:
        try:
            config_panel.delete()
        except RuntimeError:
            # Parent slot was already deleted (e.g., after render_pipeline was called)
            pass
        config_panel = None
    
    # Create new panel
    config_panel = ui.column().classes(
        'fixed right-0 top-0 h-screen w-96 bg-white shadow-2xl p-6 border-l border-gray-200 z-50 overflow-y-auto'
    )
    
    def close_panel():
        """Completely remove the config panel"""
        global config_panel
        if config_panel:
            try:
                config_panel.delete()
            except RuntimeError:
                # Parent slot was already deleted
                pass
            config_panel = None
    
    with config_panel:
        # Header with close button
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label(f'Configure {op_name}').classes('text-xl font-bold')
            ui.button(icon='close', on_click=close_panel).props('flat round dense')
        
        # Get operator info
        operator = OPERATORS.get(op_name, {})
        
        # Operator icon and description
        with ui.row().classes('items-center gap-3 mb-6 p-3 bg-gray-50 rounded-lg'):
            ui.icon(operator.get('icon', 'tune')).classes(f'text-2xl text-[{BROWN}]')
            ui.label(operator.get('description', 'No description')).classes('text-sm text-gray-600')
        
        # Parameters section
        params_schema = operator.get('params', {})
        
        if params_schema:
            # Determine UI pattern: Metadata Filter uses dynamic filters, others use static form
            use_dynamic_filters = (op_name == 'Metadata Filter')
            
            if use_dynamic_filters:
                # DYNAMIC FILTER UI (Metadata Filter)
                render_dynamic_filter_ui(params_schema, existing_params, operator_id, op_name, close_panel)
            else:
                # STATIC FORM UI (Semantic Search, Similarity Search, etc.)
                render_static_form_ui(params_schema, existing_params, operator_id, op_name, close_panel)
        else:
            # No parameters defined for this operator
            ui.label('No parameters available for this operator.').classes('text-sm text-gray-500 italic')

def render_dynamic_filter_ui(params_schema, existing_params, operator_id, op_name, close_panel):
    """Renders dynamic filter UI for Metadata Filter"""
    ui.label('PARAMETERS').classes('text-sm font-bold text-gray-600 mb-3')
    
    # Container for active filters
    filters_container = ui.column().classes('w-full gap-2 mb-4')
    
    # Track active filters: list of dicts with {param_name, container, inputs}
    active_filters = []
    
    def create_filter_row(param_name=None):
        """Creates a new filter row with dropdown and input"""
        filter_row = ui.row().classes('w-full items-start gap-2 p-3 bg-gray-50 rounded border border-gray-200')
        
        with filter_row:
            filter_data = {'container': filter_row, 'inputs': {}}
            
            with ui.column().classes('flex-1 gap-2'):
                # Dropdown to select filter type
                filter_options = [
                    (name, config.get('label', name)) 
                    for name, config in params_schema.items()
                ]
                
                selected_param = param_name or list(params_schema.keys())[0]
                filter_select = ui.select(
                    options={name: label for name, label in filter_options},
                    value=selected_param,
                    label='Filter Type'
                ).classes('w-full')
                
                filter_data['param_select'] = filter_select
                
                # Container for the input field (will be updated based on selection)
                input_container = ui.column().classes('w-full')
                filter_data['input_container'] = input_container
                
                def update_input_field():
                    """Updates the input field based on selected filter type"""
                    input_container.clear()
                    current_param = filter_select.value
                    param_config = params_schema.get(current_param, {})
                    param_type = param_config.get('type')
                    default = param_config.get('default')
                    
                    with input_container:
                        if param_type == 'text':
                            filter_data['inputs']['value'] = ui.input(
                                placeholder=f'Enter value',
                                value=default or ''
                            ).classes('w-full')
                        
                        elif param_type == 'textarea':
                            filter_data['inputs']['value'] = ui.textarea(
                                placeholder=f'Enter value',
                                value=default or ''
                            ).classes('w-full').props('rows=5')
                        
                        elif param_type == 'image':
                            # Image upload field with preview
                            filter_data['inputs']['filename'] = None
                            filter_data['inputs']['image_data'] = None
                            
                            # Container for image preview
                            preview_container = ui.column().classes('w-full')
                            filter_data['preview_container'] = preview_container
                            
                            async def handle_upload(e):
                                """Handle image upload"""
                                content = await e.file.read()
                                filename = e.file.name
                                filter_data['inputs']['filename'] = filename
                                filter_data['inputs']['image_data'] = content
                                
                                # Update preview
                                preview_container.clear()
                                with preview_container:
                                    with ui.row().classes('w-full items-center gap-2'):
                                        # Show thumbnail using base64 encoding
                                        import base64
                                        b64_data = base64.b64encode(content).decode()
                                        ui.image(f'data:image/png;base64,{b64_data}').classes('w-24 h-24 object-cover rounded border')
                                        with ui.column().classes('flex-1'):
                                            ui.label(filename).classes('text-sm font-medium')
                                            ui.label(f'{len(content) // 1024} KB').classes('text-xs text-gray-500')
                            
                            filter_data['inputs']['upload'] = ui.upload(
                                on_upload=handle_upload,
                                auto_upload=True,
                                label='Choose Image'
                            ).props('accept="image/*"').classes('w-full')
                        
                        elif param_type == 'select':
                            options = param_config.get('options', [])
                            option_labels = param_config.get('option_labels', {})
                            # Map options to labels if available
                            options_dict = {opt: option_labels.get(opt, opt) for opt in options} if option_labels else options
                            filter_data['inputs']['value'] = ui.select(
                                options=options_dict,
                                value=default
                            ).classes('w-full')
                        
                        elif param_type == 'multiselect':
                            options = param_config.get('options', [])
                            filter_data['inputs']['value'] = ui.select(
                                options=options,
                                multiple=True,
                                value=default or []
                            ).classes('w-full')
                        
                        elif param_type == 'number':
                            min_val = param_config.get('min', 0)
                            max_val = param_config.get('max', 100)
                            step = param_config.get('step', 1)
                            filter_data['inputs']['value'] = ui.number(
                                placeholder=f'Enter value',
                                value=default if default is not None else min_val,
                                min=min_val,
                                max=max_val,
                                step=step
                            ).classes('w-full')
                        
                        elif param_type == 'range':
                            min_val = param_config.get('min', 0)
                            max_val = param_config.get('max', 100)
                            
                            with ui.row().classes('w-full gap-2'):
                                filter_data['inputs']['min'] = ui.number(
                                    label='From',
                                    value=default[0] if default and default[0] is not None else min_val,
                                    min=min_val,
                                    max=max_val
                                ).classes('flex-1')
                                
                                filter_data['inputs']['max'] = ui.number(
                                    label='To',
                                    value=default[1] if default and default[1] is not None else max_val,
                                    min=min_val,
                                    max=max_val
                                ).classes('flex-1')
                
                # Initial input field
                update_input_field()
                
                # Update input when filter type changes
                filter_select.on('update:model-value', lambda: update_input_field())
            
            # Remove button
            def remove_filter():
                active_filters.remove(filter_data)
                filter_row.delete()
            
            ui.button(icon='close', on_click=remove_filter).props('flat round dense color=red').classes('mt-6')
        
        active_filters.append(filter_data)
        return filter_data
    
    with filters_container:
        # Load existing filters from operator params
        for param_name, param_value in existing_params.items():
            if param_name in params_schema:
                filter_data = create_filter_row(param_name)
                # Set the value after creation
                param_config = params_schema.get(param_name, {})
                param_type = param_config.get('type')
                
                if param_type == 'range' and isinstance(param_value, list) and len(param_value) == 2:
                    if 'min' in filter_data['inputs']:
                        filter_data['inputs']['min'].value = param_value[0]
                    if 'max' in filter_data['inputs']:
                        filter_data['inputs']['max'].value = param_value[1]
                elif param_type == 'image' and param_value:
                    # For image type, param_value might be string (old) or dict with filename and data
                    if isinstance(param_value, dict):
                        filename = param_value.get('filename')
                        image_data_b64 = param_value.get('data')
                        filter_data['inputs']['filename'] = filename
                        # Show full preview with actual image
                        if 'preview_container' in filter_data and image_data_b64:
                            with filter_data['preview_container']:
                                import base64
                                with ui.row().classes('w-full items-center gap-2'):
                                    ui.image(f'data:image/png;base64,{image_data_b64}').classes('w-24 h-24 object-cover rounded border')
                                    with ui.column().classes('flex-1'):
                                        ui.label(filename).classes('text-sm font-medium')
                                        size_kb = len(base64.b64decode(image_data_b64)) // 1024
                                        ui.label(f'{size_kb} KB').classes('text-xs text-gray-500')
                    else:
                        # Old format: just filename string
                        filter_data['inputs']['filename'] = param_value
                        if 'preview_container' in filter_data:
                            with filter_data['preview_container']:
                                ui.label(f'📷 {param_value}').classes('text-sm text-gray-600')
                elif param_type in ['text', 'textarea', 'select', 'multiselect', 'number']:
                    if 'value' in filter_data['inputs']:
                        filter_data['inputs']['value'].value = param_value
    
    # Add Filter button
    with ui.row().classes('w-full mb-6'):
        ui.button(
            'Add Filter',
            icon='add',
            on_click=lambda: (filters_container.move(create_filter_row()['container']), None)
        ).props('outline').classes(f'text-[{BROWN}]')
    
    # Action buttons for dynamic filters
    def apply_params():
        """Collect parameter values from active filters and update the operator"""
        params = {}
        missing_required = []
        
        for filter_data in active_filters:
            param_name = filter_data['param_select'].value
            param_config = params_schema.get(param_name, {})
            param_type = param_config.get('type')
            is_required = param_config.get('required', False)
            
            if param_type == 'range':
                min_input = filter_data['inputs'].get('min')
                max_input = filter_data['inputs'].get('max')
                if min_input and max_input:
                    params[param_name] = [min_input.value, max_input.value]
            elif param_type == 'image':
                # Store image data as base64 string
                filename = filter_data['inputs'].get('filename')
                image_data = filter_data['inputs'].get('image_data')
                if filename and image_data:
                    import base64
                    params[param_name] = {
                        'filename': filename,
                        'data': base64.b64encode(image_data).decode('utf-8')
                    }
                elif is_required:
                    missing_required.append(param_config.get('label', param_name))
            else:
                value_input = filter_data['inputs'].get('value')
                if value_input:
                    value = value_input.value
                    # Only include non-empty values
                    if value or value == 0:
                        params[param_name] = value
                    elif is_required:
                        missing_required.append(param_config.get('label', param_name))
                elif is_required:
                    missing_required.append(param_config.get('label', param_name))
        
        # Check if required fields are missing
        if missing_required:
            ui.notify(f'Required fields missing: {", ".join(missing_required)}', type='negative')
            return
        
        # Check for Semantic/Similarity Search: must have result_mode and corresponding parameter
        if op_name in ['Semantic Search', 'Similarity Search']:
            if 'result_mode' not in params:
                ui.notify('Please select a result mode', type='negative')
                return
            
            result_mode = params.get('result_mode')
            if result_mode in ['top_n', 'last_n'] and 'n_results' not in params:
                ui.notify('Please specify number of results', type='negative')
                return
            elif result_mode == 'similarity_range' and 'similarity_min' not in params and 'similarity_max' not in params:
                ui.notify('Please specify at least similarity min or max', type='negative')
                return
        
        # Update params in state
        pipeline_state.update_params(operator_id, params)
        
        # Log params with truncated base64 data for readability
        log_params = {}
        for k, v in params.items():
            if isinstance(v, dict) and 'data' in v and 'filename' in v:
                # Truncate base64 data to first 20 chars
                log_params[k] = {'filename': v['filename'], 'data': v['data'][:20] + '...'}
            else:
                log_params[k] = v
        logger.info(f"Applied params for {op_name}: {log_params}")
        ui.notify(f'{op_name} updated with {len(params)} filters!')
        close_panel()
        # Re-render pipeline in a new context using app.storage
        with pipeline_area:
            render_pipeline()
    
    with ui.row().classes('w-full justify-end gap-2 mt-6'):
        ui.button('Cancel', on_click=close_panel).props('flat color=grey')
        ui.button('Apply', on_click=apply_params).props('color=primary')

def render_static_form_ui(params_schema, existing_params, operator_id, op_name, close_panel):
    """Renders static form UI for Semantic Search, Similarity Search, etc."""
    ui.label('PARAMETERS').classes('text-sm font-bold text-gray-600 mb-3')
    
    # Dictionary to store input references
    param_inputs = {}
    
    # Store result_mode value for conditional rendering
    result_mode_value = existing_params.get('result_mode', params_schema.get('result_mode', {}).get('default', 'top_n'))
    
    # Render all non-conditional parameters first
    for param_name, param_config in params_schema.items():
        if param_config.get('conditional'):
            continue  # Skip conditional params for now
        
        param_type = param_config.get('type')
        label = param_config.get('label', param_name)
        description = param_config.get('description', '')
        default = param_config.get('default')
        is_required = param_config.get('required', False)
        existing_value = existing_params.get(param_name, default)
        
        # Label with required indicator
        label_text = f"{label} {'*' if is_required else ''}"
        ui.label(label_text).classes('text-sm font-medium text-gray-700 mt-3')
        if description:
            ui.label(description).classes('text-xs text-gray-500 mb-1')
        
        # Render input based on type
        if param_type == 'text':
            param_inputs[param_name] = ui.input(
                placeholder=f'Enter {label.lower()}',
                value=existing_value or ''
            ).classes('w-full mb-2')
        
        elif param_type == 'textarea':
            param_inputs[param_name] = ui.textarea(
                placeholder=f'Enter {label.lower()}',
                value=existing_value or ''
            ).classes('w-full mb-2').props('rows=5')
        
        elif param_type == 'image':
            # Image upload with preview
            # existing_value might be a string (old format) or dict with filename and data
            if isinstance(existing_value, dict):
                existing_filename = existing_value.get('filename')
                existing_data = existing_value.get('data')  # base64 string
            else:
                existing_filename = existing_value  # old format: just filename
                existing_data = None
            
            param_inputs[param_name] = {'filename': existing_filename, 'image_data': None}
            preview_container = ui.column().classes('w-full mb-2')
            
            # Show existing image if available
            if existing_filename:
                with preview_container:
                    if existing_data:
                        # Show full preview with actual image
                        with ui.row().classes('w-full items-center gap-2'):
                            ui.image(f'data:image/png;base64,{existing_data}').classes('w-24 h-24 object-cover rounded border')
                            with ui.column().classes('flex-1'):
                                ui.label(existing_filename).classes('text-sm font-medium')
                                import base64
                                size_kb = len(base64.b64decode(existing_data)) // 1024
                                ui.label(f'{size_kb} KB').classes('text-xs text-gray-500')
                    else:
                        # Fallback for old format (filename only)
                        with ui.card().classes('w-full p-3 bg-gray-50'):
                            with ui.row().classes('w-full items-center gap-3'):
                                ui.icon('image', size='lg').classes('text-gray-400')
                                with ui.column().classes('flex-1 gap-1'):
                                    ui.label(existing_filename).classes('text-sm font-medium')
                                    ui.label('Previously uploaded').classes('text-xs text-gray-500')
            
            async def handle_upload(e, pname=param_name, prev=preview_container):
                # e is the upload event, contains the uploaded file
                content = await e.file.read()
                filename = e.file.name
                param_inputs[pname]['filename'] = filename
                param_inputs[pname]['image_data'] = content
                prev.clear()
                with prev:
                    import base64
                    b64_data = base64.b64encode(content).decode()
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.image(f'data:image/png;base64,{b64_data}').classes('w-24 h-24 object-cover rounded border')
                        with ui.column().classes('flex-1'):
                            ui.label(filename).classes('text-sm font-medium')
                            ui.label(f'{len(content) // 1024} KB').classes('text-xs text-gray-500')
            
            ui.upload(on_upload=handle_upload, auto_upload=True, label='Choose Image').props('accept="image/*"').classes('w-full mb-2')
        
        elif param_type == 'select':
            options = param_config.get('options', [])
            option_labels = param_config.get('option_labels', {})
            options_dict = {opt: option_labels.get(opt, opt) for opt in options} if option_labels else options
            param_inputs[param_name] = ui.select(
                options=options_dict,
                value=existing_value
            ).classes('w-full mb-2')
            
            # If this is result_mode, update conditional fields when changed
            if param_name == 'result_mode':
                conditional_container = ui.column().classes('w-full')
                
                def update_conditionals():
                    conditional_container.clear()
                    current_mode = param_inputs['result_mode'].value
                    with conditional_container:
                        render_conditional_fields(params_schema, param_inputs, existing_params, current_mode)
                
                param_inputs[param_name].on('update:model-value', update_conditionals)
                
                # Render initial conditional fields
                with conditional_container:
                    render_conditional_fields(params_schema, param_inputs, existing_params, result_mode_value)
        
        elif param_type == 'number':
            min_val = param_config.get('min', 0)
            max_val = param_config.get('max', 100)
            step = param_config.get('step', 1)
            param_inputs[param_name] = ui.number(
                value=existing_value if existing_value is not None else default,
                min=min_val,
                max=max_val,
                step=step
            ).classes('w-full mb-2')
    
    # Action buttons
    def apply_params():
        params = {}
        missing_required = []
        
        for param_name, param_config in params_schema.items():
            param_type = param_config.get('type')
            is_required = param_config.get('required', False)
            conditional = param_config.get('conditional')
            
            # Check if field should be included based on conditional logic
            if conditional:
                result_mode = param_inputs.get('result_mode')
                if result_mode and result_mode.value not in conditional:
                    continue  # Skip this param
            
            if param_type == 'image':
                filename = param_inputs[param_name].get('filename')
                image_data = param_inputs[param_name].get('image_data')
                if filename and image_data:
                    import base64
                    params[param_name] = {
                        'filename': filename,
                        'data': base64.b64encode(image_data).decode('utf-8')
                    }
                elif is_required:
                    missing_required.append(param_config.get('label', param_name))
            else:
                input_field = param_inputs.get(param_name)
                if input_field:
                    value = input_field.value
                    if value or value == 0:
                        # Convert number types to int if step is 1 (to avoid .0 floats)
                        if param_type == 'number':
                            step = param_config.get('step', 1)
                            if step == 1 or step is None:
                                value = int(value)
                        # Convert range types to int if step is 1
                        elif param_type == 'range':
                            step = param_config.get('step', 1)
                            if step == 1 or step is None:
                                if isinstance(value, list):
                                    value = [int(v) if v is not None else None for v in value]
                        params[param_name] = value
                    elif is_required:
                        missing_required.append(param_config.get('label', param_name))
        
        if missing_required:
            ui.notify(f'Required fields missing: {", ".join(missing_required)}', type='negative')
            return
        
        # Validate result mode logic
        if op_name in ['Semantic Search', 'Similarity Search']:
            result_mode = params.get('result_mode')
            if result_mode in ['top_n', 'last_n'] and 'n_results' not in params:
                ui.notify('Please specify number of results', type='negative')
                return
            elif result_mode == 'similarity_range' and 'similarity_min' not in params and 'similarity_max' not in params:
                ui.notify('Please specify at least similarity min or max', type='negative')
                return
        
        pipeline_state.update_params(operator_id, params)
        
        # Log params with truncated base64 data for readability
        log_params = {}
        for k, v in params.items():
            if isinstance(v, dict) and 'data' in v and 'filename' in v:
                # Truncate base64 data to first 20 chars
                log_params[k] = {'filename': v['filename'], 'data': v['data'][:20] + '...'}
            else:
                log_params[k] = v
        logger.info(f"Applied params for {op_name}: {log_params}")
        ui.notify(f'{op_name} configured successfully!')
        close_panel()
        with pipeline_area:
            render_pipeline()
    
    with ui.row().classes('w-full justify-end gap-2 mt-6'):
        ui.button('Cancel', on_click=close_panel).props('flat color=grey')
        ui.button('Apply', on_click=apply_params).props('color=primary')

def render_conditional_fields(params_schema, param_inputs, existing_params, current_mode):
    """Renders conditional fields based on the current result_mode"""
    for param_name, param_config in params_schema.items():
        conditional = param_config.get('conditional')
        if not conditional or current_mode not in conditional:
            continue
        
        param_type = param_config.get('type')
        label = param_config.get('label', param_name)
        description = param_config.get('description', '')
        default = param_config.get('default')
        existing_value = existing_params.get(param_name, default)
        
        ui.label(label).classes('text-sm font-medium text-gray-700 mt-3')
        if description:
            ui.label(description).classes('text-xs text-gray-500 mb-1')
        
        if param_type == 'number':
            min_val = param_config.get('min', 0)
            max_val = param_config.get('max', 100)
            step = param_config.get('step', 1)
            param_inputs[param_name] = ui.number(
                value=existing_value if existing_value is not None else default,
                min=min_val,
                max=max_val,
                step=step
            ).classes('w-full mb-2')


def render_results_section():
    """Renders the results section with view toggle and results display"""
    global results_area, current_view, results_display_container
    
    if results_area is None:
        return
    
    with results_area:
        # Header with view toggle
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label('Showing 10 results').classes('text-sm text-gray-600')
            
            with ui.row().classes('gap-2'):
                ui.button(icon='grid_view', on_click=lambda: toggle_view('grid')).props(
                    f'flat dense {"color=primary" if current_view == "grid" else "color=grey"}'
                ).tooltip('Grid View')
                ui.button(icon='view_list', on_click=lambda: toggle_view('list')).props(
                    f'flat dense {"color=primary" if current_view == "list" else "color=grey"}'
                ).tooltip('List View')
        
        # Results display area
        results_display_container = ui.column().classes('w-full')
        render_mock_results(results_display_container)


def clear_results():
    """Clear the results area"""
    global results_area
    if results_area:
        results_area.clear()


def show_preview():
    """Show the results preview when Preview button is clicked"""
    pipeline = pipeline_state.get_all_operators()
    if not pipeline:
        ui.notify('Please add at least one operator to the pipeline', type='warning')
        return
    
    # Use first operator for preview
    first_operator = pipeline[0]
    show_preview_for_operator(first_operator['id'], first_operator['name'])


def show_preview_for_operator(operator_id: str, operator_name: str):
    """Show results preview for a specific operator"""
    global results_area, current_view
    
    logger.info(f"Showing preview for operator: {operator_name} (ID: {operator_id})")
    
    # Get operator params from pipeline state
    operator_data = None
    for op in pipeline_state.get_all_operators():
        if op['id'] == operator_id:
            operator_data = op
            break
    
    if not operator_data:
        logger.error(f"Operator {operator_id} not found in pipeline")
        ui.notify('Operator not found', type='negative')
        return
    
    params = operator_data.get('params', {})
    
    # Clear results area immediately
    if not results_area:
        return
    
    results_area.clear()
    
    # --- SEMANTIC SEARCH ---
    if operator_name == 'Semantic Search' and params.get('query_text'):
        with results_area:
            with ui.row().classes('w-full items-center justify-center p-8 gap-3'):
                ui.spinner('dots', size='lg', color='primary')
                ui.label('Loading results...').classes('text-gray-600 font-medium')
        
        # Use timer to defer execution so spinner is visible
        def execute_semantic_query():
            # Execute backend search
            logger.info(f"Executing Semantic Search with params: {params}")
            preview_results, total_count = execute_semantic_search(params)
            
            # Update result count in pipeline state (use total_count, not preview count)
            pipeline_state.update_result_count(operator_id, total_count)
            
            # Re-render pipeline to show updated count
            render_pipeline()
            
            # Clear spinner and show results
            results_area.clear()
            
            if not preview_results:
                with results_area:
                    ui.label('No results found').classes('text-gray-600 font-medium')
                    ui.label('Try adjusting your search parameters').classes('text-sm text-gray-500 mt-2')
                return
            
            # Render results
            render_results_ui(preview_results, operator_id, operator_name)
        
        # Execute after short delay to let UI update
        ui.timer(0.1, execute_semantic_query, once=True)
        return
    
    # --- METADATA FILTER ---
    if operator_name == 'Metadata Filter':
        # Check if any filter is configured
        has_filters = any([
            params.get('artist', '').strip(),
            params.get('title', '').strip(),
            params.get('inventory_number', '').strip(),
            params.get('year_range', [None, None]) != [None, None],
            params.get('source', [])
        ])
        
        if has_filters:
            with results_area:
                with ui.row().classes('w-full items-center justify-center p-8 gap-3'):
                    ui.spinner('dots', size='lg', color='primary')
                    ui.label('Loading results...').classes('text-gray-600 font-medium')
            
            def execute_metadata_query():
                logger.info(f"Executing Metadata Filter with params: {params}")
                preview_results, total_count = execute_metadata_filter(params)
                
                # Update result count in pipeline state
                pipeline_state.update_result_count(operator_id, total_count)
                
                # Re-render pipeline to show updated count
                render_pipeline()
                
                # Clear spinner and show results
                results_area.clear()
                
                if not preview_results:
                    with results_area:
                        ui.label('No results found').classes('text-gray-600 font-medium')
                        ui.label('Try adjusting your filter parameters').classes('text-sm text-gray-500 mt-2')
                    return
                
                # Render results
                render_results_ui(preview_results, operator_id, operator_name)
            
            ui.timer(0.1, execute_metadata_query, once=True)
            return
        else:
            # No filters configured
            with results_area:
                ui.label('⚠️ Please configure the Metadata Filter first').classes('text-orange-600 font-medium')
                ui.label('Click the settings icon to add filter parameters').classes('text-sm text-gray-500 mt-2')
            return
    
    # --- SIMILARITY SEARCH ---
    if operator_name == 'Similarity Search':
        # Check if image is uploaded
        query_image = params.get('query_image')
        has_image = query_image and isinstance(query_image, dict) and query_image.get('data')
        
        if has_image:
            with results_area:
                with ui.row().classes('w-full items-center justify-center p-8 gap-3'):
                    ui.spinner('dots', size='lg', color='primary')
                    ui.label('Generating caption and searching...').classes('text-gray-600 font-medium')
            
            def execute_similarity_query():
                logger.info(f"Executing Similarity Search with image: {query_image.get('filename')}")
                preview_results, total_count = execute_similarity_search(params)
                
                # Update result count in pipeline state
                pipeline_state.update_result_count(operator_id, total_count)
                
                # Re-render pipeline to show updated count
                render_pipeline()
                
                # Clear spinner and show results
                results_area.clear()
                
                if not preview_results:
                    with results_area:
                        ui.label('No results found').classes('text-gray-600 font-medium')
                        ui.label('Try uploading a different image').classes('text-sm text-gray-500 mt-2')
                    return
                
                # Render results
                logger.info(f"Calling render_results_ui with {len(preview_results)} results")
                render_results_ui(preview_results, operator_id, operator_name)
            
            ui.timer(0.1, execute_similarity_query, once=True)
            return
        else:
            # No image uploaded
            with results_area:
                ui.label('⚠️ Please configure the Similarity Search operator first').classes('text-orange-600 font-medium')
                ui.label('Click the settings icon to upload an image').classes('text-sm text-gray-500 mt-2')
            return
    
    # Handle other cases
    if operator_name == 'Semantic Search':
        # No query_text configured
        with results_area:
            ui.label('⚠️ Please configure the Semantic Search operator first').classes('text-orange-600 font-medium')
            ui.label('Click the settings icon to add search parameters').classes('text-sm text-gray-500 mt-2')
        return
    
    # Use mock data for other operators
    results = MOCK_RESULTS.get(operator_name, MOCK_RESULTS['Metadata Filter'])
    render_results_ui(results, operator_id, operator_name)


def render_results_ui(results, operator_id, operator_name):
    """Render results UI with header and grid/list view"""
    global results_area, current_view, results_display_container, last_preview_results, last_preview_operator_id
    
    logger.info(f"render_results_ui called with {len(results)} results for {operator_name}")
    
    # Cache results for fast view toggling
    last_preview_results = results
    last_preview_operator_id = operator_id
    
    logger.info("Starting UI rendering...")
    
    with results_area:
            logger.info("Inside results_area context")
            # Header with view toggle
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label(f'Preview: {operator_name}').classes('text-sm text-gray-600')
                
                with ui.row().classes('gap-2'):
                    ui.button(icon='grid_view', on_click=lambda: toggle_view_for_operator('grid', operator_id, operator_name)).props(
                        f'flat dense {"color=primary" if current_view == "grid" else "color=grey"}'
                    ).tooltip('Grid View')
                    ui.button(icon='view_list', on_click=lambda: toggle_view_for_operator('list', operator_id, operator_name)).props(
                        f'flat dense {"color=primary" if current_view == "list" else "color=grey"}'
                    ).tooltip('List View')
            
            logger.info("Header rendered, creating results container...")
            # Results display area - wrap in full width container
            global results_display_container
            results_display_container = ui.element('div').classes('w-full')
            
            # Render results (already fetched above)
            with results_display_container:
                # Ensure grid container has full width
                container = ui.element('div').classes('w-full')
                with container:
                    logger.info(f"Rendering {current_view} view...")
                    if current_view == 'grid':
                        render_grid_view(results)
                    else:
                        render_list_view(results)
            
            logger.info("Results rendered successfully")
            
            # Update result count in header
            ui.run_javascript(f"""
                document.querySelector('[id="results-area"] .text-sm.text-gray-600').textContent = 
                    'Preview: {operator_name} ({len(results)} results)';
            """)
    
    logger.info(f"render_results_ui complete")
    ui.notify(f'Preview for {operator_name}: {len(results)} results', type='positive')


def toggle_view(view_type):
    """Toggle between grid and list view"""
    global current_view, results_display_container
    current_view = view_type
    logger.info(f"Toggled view to: {view_type}")
    # Re-render only the results display container
    if results_display_container:
        results_display_container.clear()
        with results_display_container:
            results = MOCK_RESULTS['Metadata Filter']
            if current_view == 'grid':
                render_grid_view(results)
            else:
                render_list_view(results)


# Global cache for last results
last_preview_results = None
last_preview_operator_id = None

def toggle_view_for_operator(view_type: str, operator_id: str, operator_name: str):
    """Toggle between grid and list view for a specific operator"""
    global current_view, results_display_container, last_preview_results
    current_view = view_type
    logger.info(f"Toggled view to: {view_type} for operator: {operator_name}")
    
    # Re-render only the results display container with cached results
    if results_display_container and last_preview_results:
        results_display_container.clear()
        
        # Use cached results instead of re-executing
        with results_display_container:
            container = ui.element('div').classes('w-full')
            with container:
                if current_view == 'grid':
                    render_grid_view(last_preview_results)
                else:
                    render_list_view(last_preview_results)


def render_mock_results(container):
    """Render mock results in current view mode"""
    global current_view
    
    # For now, show Metadata Filter results as default
    results = MOCK_RESULTS['Metadata Filter']
    
    with container:
        if current_view == 'grid':
            render_grid_view(results)
        else:
            render_list_view(results)


def show_artwork_detail(artwork_data):
    """Navigate to detail view with artwork data."""
    logger.info(f"Navigating to detail view for artwork: {artwork_data.get('inventory')}")
    
    # Store artwork data in detail module's storage dict
    from pages import detail
    detail._artwork_storage['current_artwork'] = artwork_data
    
    # Navigate to detail route
    ui.navigate.to('/detail')


def render_grid_view(results):
    """Render results in grid view (2 rows x 5 columns)"""
    # Grid with 5 columns
    with ui.element('div').classes('grid grid-cols-5 gap-4 w-full'):
        for result in results:
            # Truncate title to max 30 chars
            title = result['title']
            if len(title) > 30:
                title = title[:27] + '...'
            
            # Square tile with image and title below
            with ui.column().classes('gap-2 min-w-0'):
                # Image container with fixed aspect ratio - clickable
                with ui.card().classes('w-full p-0 overflow-hidden cursor-pointer hover:shadow-xl transition').style('aspect-ratio: 1/1;'):
                    img = ui.image(result['image']).classes('w-full h-full object-cover')
                    img.on('click', lambda r=result: show_artwork_detail(r))
                
                # Metadata below image with truncation
                with ui.column().classes('gap-0 w-full min-w-0'):
                    ui.label(title).classes('text-sm font-bold text-gray-800 truncate')
                    ui.label(result['artist']).classes('text-xs text-gray-600 truncate')
                    ui.label(f"{result['year']} • {result['inventory']}").classes('text-xs text-gray-500 truncate')


def render_list_view(results):
    """Render results in list view (1 per row)"""
    with ui.column().classes('w-full gap-3'):
        for result in results:
            # List item card - clickable
            with ui.card().classes('w-full hover:shadow-lg transition cursor-pointer'):
                card_row = ui.row().classes('w-full items-center gap-4 p-2')
                card_row.on('click', lambda r=result: show_artwork_detail(r))
                
                with card_row:
                    # Square thumbnail (fixed size)
                    ui.image(result['image']).classes('w-24 h-24 object-cover rounded')
                    
                    # Metadata (always visible)
                    with ui.column().classes('flex-1'):
                        ui.label(result['title']).classes('text-base font-bold text-gray-800')
                        ui.label(result['artist']).classes('text-sm text-gray-600')
                        with ui.row().classes('gap-2 mt-1'):
                            ui.badge(result['year']).props('color=grey')
                            ui.badge(result['inventory']).props(f'color=none').classes(f'bg-[{BROWN}] text-white')







