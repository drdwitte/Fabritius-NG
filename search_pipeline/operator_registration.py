"""
Operator registration.

This module registers all available operators in the central registry.
Import this module early to ensure all operators are registered before use.
"""

from loguru import logger

from search_pipeline.operator_registry import OperatorRegistry, OperatorNames
from search_pipeline.operator_implementations import (
    SemanticSearchOperator,
    MetadataFilterOperator,
    SimilaritySearchOperator,
    PoseSearchOperator,
    SketchSearchOperator,
    ColorSearchOperator
)
from search_pipeline.operator_builder import (
    ParamBuilder,
    OperatorBuilder
)


def _register_metadata_filter():
    """Register Metadata Filter operator."""
    _, definition = (
        OperatorBuilder(OperatorNames.METADATA_FILTER)
        .icon('filter_alt')
        .description('Filter artworks by metadata attributes')
        .param('source', 
            ParamBuilder('multiselect')
            .label('Source Collection')
            .description('Filter by collection source (FILTER IN operation)')
            .default([])
            .options([])  # To be populated from disk
        )
        .param('artist',
            ParamBuilder('text')
            .label('Artist Name')
            .description('Full or partial artist name')
            .default('')
        )
        .param('title',
            ParamBuilder('text')
            .label('Artwork Title')
            .description('Full or partial artwork title')
            .default('')
        )
        .param('inventory_number',
            ParamBuilder('text')
            .label('Inventory Number')
            .description('Full or partial inventory number')
            .default('')
        )
        .param('year_range',
            ParamBuilder('range')
            .label('Year Range')
            .description('Filter by creation year range')
            .default([None, None])
            .min_value(1400)
            .max_value(2024)
        )
        .param('result_mode',
            ParamBuilder('select')
            .label('Result Mode')
            .description('How to apply this filter')
            .default('replace_all')
            .options({
                'replace_all': 'Replace All Results',
                'filter_previous': 'Filter Previous Results'
            })
        )
        .build()
    )
    
    OperatorRegistry.register(
        name=OperatorNames.METADATA_FILTER,
        icon=definition['icon'],
        description=definition['description'],
        params=definition['params'],
        implementation=MetadataFilterOperator
    )


def _register_semantic_search():
    """Register Semantic Search operator."""
    _, definition = (
        OperatorBuilder(OperatorNames.SEMANTIC_SEARCH)
        .icon('search')
        .description('AI-powered search using natural language queries')
        .param('query_text',
            ParamBuilder('text')
            .label('Search Query')
            .description('Natural language search query')
            .default('')
            .required()
        )
        .param('top_k',
            ParamBuilder('number')
            .label('Number of Results')
            .description('Maximum number of results to return')
            .default(15)
            .min_value(1)
            .max_value(100)
        )
        .param('result_mode',
            ParamBuilder('select')
            .label('Result Mode')
            .description('How to apply this search')
            .default('replace_all')
            .options({
                'replace_all': 'Replace All Results',
                'filter_previous': 'Filter Previous Results'
            })
        )
        .build()
    )
    
    OperatorRegistry.register(
        name=OperatorNames.SEMANTIC_SEARCH,
        icon=definition['icon'],
        description=definition['description'],
        params=definition['params'],
        implementation=SemanticSearchOperator
    )


def _register_similarity_search():
    """Register Similarity Search operator."""
    _, definition = (
        OperatorBuilder(OperatorNames.SIMILARITY_SEARCH)
        .icon('image_search')
        .description('Find similar artworks by uploading an image')
        .param('query_image',
            ParamBuilder('image')
            .label('Upload Image')
            .description('Upload an image to find similar artworks')
            .default(None)
            .required()
        )
        .param('top_k',
            ParamBuilder('number')
            .label('Number of Results')
            .description('Maximum number of results to return')
            .default(15)
            .min_value(1)
            .max_value(100)
        )
        .param('result_mode',
            ParamBuilder('select')
            .label('Result Mode')
            .description('How to apply this search')
            .default('replace_all')
            .options({
                'replace_all': 'Replace All Results',
                'filter_previous': 'Filter Previous Results'
            })
        )
        .build()
    )
    
    OperatorRegistry.register(
        name=OperatorNames.SIMILARITY_SEARCH,
        icon=definition['icon'],
        description=definition['description'],
        params=definition['params'],
        implementation=SimilaritySearchOperator
    )


def _register_pose_search():
    """Register Pose Search operator."""
    _, definition = (
        OperatorBuilder(OperatorNames.POSE_SEARCH)
        .icon('accessibility_new')
        .description('Find artworks with similar human poses')
        .param('pose',
            ParamBuilder('text')
            .label('Pose Description')
            .description('Describe the body pose or posture (e.g., "Standing figures", "Seated person")')
            .default('')
            .required(True)
        )
        .param('confidence',
            ParamBuilder('number')
            .label('Confidence Threshold')
            .description('Minimum AI confidence level for pose detection')
            .default(0.7)
            .min_value(0.0)
            .max_value(1.0)
        )
        .param('top_k',
            ParamBuilder('number')
            .label('Number of Results')
            .description('Maximum number of results to return')
            .default(15)
            .min_value(1)
            .max_value(100)
        )
        .param('result_mode',
            ParamBuilder('select')
            .label('Result Mode')
            .description('How to apply this search')
            .default('replace_all')
            .options({
                'replace_all': 'Replace All Results',
                'filter_previous': 'Filter Previous Results'
            })
        )
        .build()
    )
    
    OperatorRegistry.register(
        name=OperatorNames.POSE_SEARCH,
        icon=definition['icon'],
        description=definition['description'],
        params=definition['params'],
        implementation=PoseSearchOperator
    )


def _register_sketch_search():
    """Register Sketch Search operator."""
    _, definition = (
        OperatorBuilder(OperatorNames.SKETCH_SEARCH)
        .icon('brush')
        .description('Search by drawing or uploading a sketch')
        .param('sketch_data',
            ParamBuilder('canvas')
            .label('Sketch')
            .description('Draw a rough sketch of the composition you are looking for')
            .default(None)
            .required(True)
        )
        .param('top_k',
            ParamBuilder('number')
            .label('Number of Results')
            .description('Maximum number of results to return')
            .default(15)
            .min_value(1)
            .max_value(100)
        )
        .param('result_mode',
            ParamBuilder('select')
            .label('Result Mode')
            .description('How to apply this search')
            .default('replace_all')
            .options({
                'replace_all': 'Replace All Results',
                'filter_previous': 'Filter Previous Results'
            })
        )
        .build()
    )
    
    OperatorRegistry.register(
        name=OperatorNames.SKETCH_SEARCH,
        icon=definition['icon'],
        description=definition['description'],
        params=definition['params'],
        implementation=SketchSearchOperator
    )


def _register_color_search():
    """Register Color-Based Search operator."""
    _, definition = (
        OperatorBuilder(OperatorNames.COLOR_SEARCH)
        .icon('palette')
        .description('Find artworks by dominant colors or color palette')
        .param('colors',
            ParamBuilder('multiselect')
            .label('Colors')
            .description('Select one or more colors to search for')
            .default([])
            .options([
                'Red', 'Orange', 'Yellow', 'Green', 'Blue', 
                'Purple', 'Pink', 'Brown', 'Black', 'White', 'Gray'
            ])
            .required(True)
        )
        .param('color_tolerance',
            ParamBuilder('number')
            .label('Color Tolerance')
            .description('How closely colors must match (0 = exact, 1 = loose)')
            .default(0.3)
            .min_value(0.0)
            .max_value(1.0)
        )
        .param('top_k',
            ParamBuilder('number')
            .label('Number of Results')
            .description('Maximum number of results to return')
            .default(15)
            .min_value(1)
            .max_value(100)
        )
        .param('result_mode',
            ParamBuilder('select')
            .label('Result Mode')
            .description('How to apply this search')
            .default('replace_all')
            .options({
                'replace_all': 'Replace All Results',
                'filter_previous': 'Filter Previous Results'
            })
        )
        .build()
    )
    
    OperatorRegistry.register(
        name=OperatorNames.COLOR_SEARCH,
        icon=definition['icon'],
        description=definition['description'],
        params=definition['params'],
        implementation=ColorSearchOperator
    )


# Track if operators are already registered to make this idempotent
_operators_registered = False

def register_all_operators():
    """
    Register all available operators.
    
    Call this function to populate the registry. Safe to call multiple times (idempotent).
    Typically called from pages/search.py when the search page is first accessed.
    """
    global _operators_registered
    if _operators_registered:
        logger.debug("Operators already registered, skipping")
        return
    
    logger.info("Registering all operators...")
    _register_metadata_filter()
    _register_semantic_search()
    _register_similarity_search()
    _register_pose_search()
    _register_sketch_search()
    _register_color_search()
    _operators_registered = True
    logger.info(f"Successfully registered {len(OperatorRegistry._registry)} operators")
