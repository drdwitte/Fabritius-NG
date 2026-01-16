"""
Concrete implementations of search pipeline operators.

Each operator implements the Operator interface with its own
specific logic for execution, validation, and configuration.
"""

from typing import Tuple, List, Dict, Any
from loguru import logger

from .operator_base import Operator
from .operators import execute_semantic_search, execute_metadata_filter, execute_similarity_search


class SemanticSearchOperator(Operator):
    """Operator for semantic search using text embeddings."""
    
    def __init__(self):
        super().__init__(
            name='Semantic Search',
            icon='search',
            description='Search artworks by semantic meaning using AI-powered text embeddings'
        )
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute semantic search with query text."""
        logger.info(f"Executing Semantic Search with params: {params}")
        return execute_semantic_search(params)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Schema for semantic search configuration."""
        return {
            'query_text': {
                'type': 'text',
                'label': 'Search Query',
                'placeholder': 'Enter search terms...',
                'required': True
            },
            'top_k': {
                'type': 'number',
                'label': 'Number of Results',
                'default': 15,
                'min': 1,
                'max': 100
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate semantic search parameters."""
        errors = []
        
        if not params.get('query_text', '').strip():
            errors.append('Search query is required')
        
        top_k = params.get('top_k', 15)
        if not isinstance(top_k, (int, float)) or top_k < 1:
            errors.append('Number of results must be at least 1')
        
        return (len(errors) == 0, errors)
    
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """Check if query text is provided."""
        return bool(params.get('query_text', '').strip())
    
    def get_loading_message(self) -> str:
        """Loading message for semantic search."""
        return 'Loading results...'
    
    def get_unconfigured_message(self) -> str:
        """Message when not configured."""
        return 'Please configure the Semantic Search operator first'


class MetadataFilterOperator(Operator):
    """Operator for filtering artworks by metadata fields."""
    
    def __init__(self):
        super().__init__(
            name='Metadata Filter',
            icon='filter_alt',
            description='Filter artworks by artist, title, date range, and other metadata'
        )
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute metadata filter query."""
        logger.info(f"Executing Metadata Filter with params: {params}")
        return execute_metadata_filter(params)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Schema for metadata filter configuration."""
        return {
            'artist': {
                'type': 'text',
                'label': 'Artist Name',
                'placeholder': 'Enter artist name...'
            },
            'title': {
                'type': 'text',
                'label': 'Artwork Title',
                'placeholder': 'Enter title...'
            },
            'inventory_number': {
                'type': 'text',
                'label': 'Inventory Number',
                'placeholder': 'Enter inventory number...'
            },
            'year_range': {
                'type': 'range',
                'label': 'Year Range',
                'min': 1400,
                'max': 2024
            },
            'source': {
                'type': 'multiselect',
                'label': 'Source',
                'options': ['KMSKA', 'Other']
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate metadata filter parameters."""
        errors = []
        
        year_range = params.get('year_range', [None, None])
        if isinstance(year_range, list) and len(year_range) == 2:
            start, end = year_range
            if start is not None and end is not None and start > end:
                errors.append('Year range start must be before end')
        
        return (len(errors) == 0, errors)
    
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """Check if at least one filter is configured."""
        return any([
            params.get('artist', '').strip(),
            params.get('title', '').strip(),
            params.get('inventory_number', '').strip(),
            params.get('year_range', [None, None]) != [None, None],
            params.get('source', [])
        ])
    
    def get_loading_message(self) -> str:
        """Loading message for metadata filter."""
        return 'Loading results...'
    
    def get_unconfigured_message(self) -> str:
        """Message when not configured."""
        return 'Please configure the Metadata Filter first'


class SimilaritySearchOperator(Operator):
    """Operator for similarity search using image embeddings."""
    
    def __init__(self):
        super().__init__(
            name='Similarity Search',
            icon='image_search',
            description='Find similar artworks by uploading an image'
        )
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute similarity search with uploaded image."""
        query_image = params.get('query_image', {})
        logger.info(f"Executing Similarity Search with image: {query_image.get('filename')}")
        return execute_similarity_search(params)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Schema for similarity search configuration."""
        return {
            'query_image': {
                'type': 'image',
                'label': 'Upload Image',
                'required': True
            },
            'top_k': {
                'type': 'number',
                'label': 'Number of Results',
                'default': 15,
                'min': 1,
                'max': 100
            }
        }
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate similarity search parameters."""
        errors = []
        
        query_image = params.get('query_image')
        if not query_image or not isinstance(query_image, dict) or not query_image.get('data'):
            errors.append('Image upload is required')
        
        top_k = params.get('top_k', 15)
        if not isinstance(top_k, (int, float)) or top_k < 1:
            errors.append('Number of results must be at least 1')
        
        return (len(errors) == 0, errors)
    
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """Check if image is uploaded."""
        query_image = params.get('query_image')
        return query_image and isinstance(query_image, dict) and query_image.get('data')
    
    def get_loading_message(self) -> str:
        """Loading message for similarity search."""
        return 'Generating caption and searching...'
    
    def get_unconfigured_message(self) -> str:
        """Message when not configured."""
        return 'Please configure the Similarity Search operator first'


class PoseSearchOperator(Operator):
    """Operator for finding artworks with similar human poses."""
    
    def __init__(self):
        super().__init__(
            name='Pose Search',
            icon='accessibility_new',
            description='Find artworks with similar human poses or body positions'
        )
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute pose search query."""
        logger.info(f"Executing Pose Search with params: {params}")
        # TODO: Implement pose search using pose detection AI
        logger.warning("Pose Search not yet implemented - returning empty results")
        return ([], 0)
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate pose search parameters."""
        errors = []
        
        pose = params.get('pose', '').strip()
        if not pose:
            errors.append('Pose description is required')
        
        return (len(errors) == 0, errors)
    
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """Check if pose is described."""
        return bool(params.get('pose', '').strip())
    
    def get_loading_message(self) -> str:
        """Loading message for pose search."""
        return 'Detecting poses in artworks...'
    
    def get_unconfigured_message(self) -> str:
        """Message when not configured."""
        return 'Please configure the Pose Search operator first'


class SketchSearchOperator(Operator):
    """Operator for searching by sketch/drawing."""
    
    def __init__(self):
        super().__init__(
            name='Sketch Search',
            icon='brush',
            description='Search by drawing or uploading a sketch'
        )
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute sketch search query."""
        logger.info(f"Executing Sketch Search with params: {params}")
        # TODO: Implement sketch-based search using sketch embeddings
        logger.warning("Sketch Search not yet implemented - returning empty results")
        return ([], 0)
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate sketch search parameters."""
        errors = []
        
        sketch_data = params.get('sketch_data')
        if not sketch_data:
            errors.append('Sketch is required')
        
        return (len(errors) == 0, errors)
    
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """Check if sketch is provided."""
        return bool(params.get('sketch_data'))
    
    def get_loading_message(self) -> str:
        """Loading message for sketch search."""
        return 'Analyzing sketch and searching...'
    
    def get_unconfigured_message(self) -> str:
        """Message when not configured."""
        return 'Please configure the Sketch Search operator first'


class ColorSearchOperator(Operator):
    """Operator for color-based search."""
    
    def __init__(self):
        super().__init__(
            name='Color-Based Search',
            icon='palette',
            description='Find artworks by dominant colors or color palette'
        )
    
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """Execute color-based search query."""
        logger.info(f"Executing Color-Based Search with params: {params}")
        # TODO: Implement color-based search using color histograms
        logger.warning("Color-Based Search not yet implemented - returning empty results")
        return ([], 0)
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate color search parameters."""
        errors = []
        
        colors = params.get('colors', [])
        if not colors or len(colors) == 0:
            errors.append('At least one color must be selected')
        
        return (len(errors) == 0, errors)
    
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """Check if colors are selected."""
        colors = params.get('colors', [])
        return colors and len(colors) > 0
    
    def get_loading_message(self) -> str:
        """Loading message for color search."""
        return 'Analyzing color palettes...'
    
    def get_unconfigured_message(self) -> str:
        """Message when not configured."""
        return 'Please configure the Color-Based Search operator first'

