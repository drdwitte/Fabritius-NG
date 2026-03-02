"""
Validation engine for label validation.

Core logic for running validation algorithms against artwork collections.
Generates columns for:
- AI algorithms: One column per selected algorithm (AI-Text, AI-Multimodal, etc.)
- Validated data: Fixed columns (AI-validated, Human, Expert)
"""

from typing import List, Dict, Any
from loguru import logger

from .state import LabelState, ValidationResults
from search_pipeline.operators import execute_semantic_search
from config import settings
from backend.supabase_client import SupabaseClient


class ValidationEngine:
    """Engine for validating labels and generating column results."""
    
    def __init__(self):
        """Initialize the validation engine."""
        logger.info("Initialized ValidationEngine")
    
    async def validate_label(
        self,
        label_name: str,
        label_definition: str,
        algorithms: List[str],
        state: LabelState,
        validated_boxes: List[str] = None
    ) -> Dict[str, ValidationResults]:
        """
        Validate a label using selected algorithms and fetch validated data.
        
        Args:
            label_name: Name of the label to validate
            label_definition: Definition of the label
            algorithms: List of algorithm names to use (for AI columns)
            state: Current label state
            validated_boxes: List of validated box keys to fetch (optional)
            
        Returns:
            Dictionary mapping column keys to their results
        """
        if validated_boxes is None:
            validated_boxes = []
        
        logger.info(
            f"Starting validation for label '{label_name}' "
            f"with algorithms: {', '.join(algorithms)} | "
            f"validated boxes: {', '.join(validated_boxes)}"
        )
        
        results = {}
        
        # Run AI algorithms (one column per algorithm)
        for algo_name in algorithms:
            column_key = f"AI-{algo_name}"
            logger.info(f"Running algorithm: {algo_name}")
            
            box_results = state.get_box_results(column_key)
            box_results.column_label = f"AI - {algo_name}"
            box_results.is_loading = True
            box_results.error = None
            
            try:
                artworks = await self._run_algorithm(
                    label_name=label_name,
                    label_definition=label_definition,
                    algorithm_name=algo_name
                )
                
                box_results.results = artworks
                box_results.total_count = len(artworks)
                box_results.is_loading = False
                
                logger.info(f"Algorithm {algo_name} complete: {box_results.total_count} results")
                
            except Exception as e:
                logger.error(f"Error running algorithm {algo_name}: {str(e)}")
                box_results.error = str(e)
                box_results.is_loading = False
            
            results[column_key] = box_results
        
        # Fetch validated data columns (only for requested boxes)
        for column_key in validated_boxes:
            logger.info(f"Fetching validated data: {column_key}")
            
            box_results = state.get_box_results(column_key)
            box_results.column_label = column_key.replace("AI-validated", "AI ✓")
            box_results.is_loading = True
            box_results.error = None
            
            try:
                artworks = await self._fetch_validated_data(
                    label_name=label_name,
                    validation_level=column_key
                )
                
                box_results.results = artworks
                box_results.total_count = len(artworks)
                box_results.is_loading = False
                
                logger.info(f"Validated data {column_key} complete: {box_results.total_count} results")
                
            except Exception as e:
                logger.error(f"Error fetching validated data {column_key}: {str(e)}")
                box_results.error = str(e)
                box_results.is_loading = False
            
            results[column_key] = box_results
        
        return results
    
    async def _run_algorithm(
        self,
        label_name: str,
        label_definition: str,
        algorithm_name: str
    ) -> List[Dict[str, Any]]:
        """
        Run a specific algorithm to find matching artworks.
        
        Args:
            label_name: Name of the label
            label_definition: Definition of the label
            algorithm_name: Algorithm to run (Text, Image, etc.)
            
        Returns:
            List of matching artworks with metadata
        """
        # Build search query from label name and definition
        if label_definition:
            query_text = f"{label_name}: {label_definition}"
        else:
            query_text = label_name
        
        logger.info(f"Running {algorithm_name} algorithm with query: '{query_text}'")
        
        # Multimodal uses different engine - use mock data for now
        if algorithm_name.lower() in ['multimodal', 'image']:
            logger.info(f"{algorithm_name} algorithm: Using mock data (multimodal engine not yet implemented)")
            from .mock_data import MULTIMODAL_PAINTINGS
            return [dict(p, algorithm=algorithm_name) for p in MULTIMODAL_PAINTINGS]
        
        # Text embeddings: use vector search
        try:
            # Execute semantic search using shared operator
            params = {
                'query_text': query_text,
                'result_mode': 'top_n',
                'n_results': 50  # Get top 50 results per algorithm
            }
            
            preview_results, total_count = execute_semantic_search(params)
            
            logger.info(f"{algorithm_name} algorithm: {total_count} results found, showing {len(preview_results)}")
            
            # Add algorithm metadata to each result
            for result in preview_results:
                result['algorithm'] = algorithm_name
            
            return preview_results
            
        except Exception as e:
            logger.error(f"Error executing {algorithm_name} algorithm: {e}")
            raise
    
    async def _fetch_validated_data(
        self,
        label_name: str,
        validation_level: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch validated/labeled data from database.
        
        Args:
            label_name: Name of the label
            validation_level: Type of validation (AI, HUMAN, EXPERT)
            
        Returns:
            List of labeled artworks
        """
        # Map validation level to database provenance field
        # AI → provenance "AI"
        # HUMAN → provenance ["FABRITIUS", "HUMAN"] (show BOTH original and new human tags)
        # EXPERT → provenance "EXPERT"
        provenance_map = {
            "AI": "AI",
            "HUMAN": ["FABRITIUS", "HUMAN"],  # HUMAN layer shows both!
            "EXPERT": "EXPERT"
        }
        
        provenance = provenance_map.get(validation_level)
        if not provenance:
            logger.warning(f"Unknown validation level: {validation_level}")
            return []
        
        try:
            logger.info(f"Fetching {validation_level} validated data for label '{label_name}' with provenance '{provenance}'")
            db = SupabaseClient()
            
            # Query artworks with this label and provenance (read-only, no modifications)
            artworks = db.fetch_artworks_by_label_and_prov(
                label=label_name,
                provenance=provenance,  # Can be string or list
                limit=50  # Limit to 50 results per layer
            )
            
            logger.info(f"Found {len(artworks)} artworks with label '{label_name}' and provenance '{provenance}'")
            
            # If no results found, return empty list (don't use mock data)
            if not artworks:
                logger.info(f"No {validation_level} validated data found for label '{label_name}'")
                return []
            
            # Map database fields to UI format
            formatted_results = []
            for artwork in artworks:
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
                    'date': artwork.get('beschrijving_datering', 'N/A'),
                    'inventory': artwork.get('inventarisnummer', 'N/A'),
                    'image_url': image_url,
                    'validation_level': validation_level,
                    'provenance': artwork.get('provenance'),  # Use actual provenance from DB
                    'tag_id': artwork.get('tag_id')  # Needed for promote/demote
                })
            
            logger.info(f"Returning {len(formatted_results)} formatted results for {validation_level}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error fetching {validation_level} validated data with provenance '{provenance}': {e}")
            import traceback
            traceback.print_exc()
            
            # Return empty list on error (no mock data fallback)
            logger.warning(f"Returning empty list due to database error")
            return []
