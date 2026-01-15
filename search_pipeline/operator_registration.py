"""
Operator registration.

This module registers all available operators in the central registry.
Import this module early to ensure all operators are registered before use.
"""

from search_pipeline.operator_registry import OperatorRegistry, OperatorNames
from search_pipeline.operator_implementations import (
    SemanticSearchOperator,
    MetadataFilterOperator,
    SimilaritySearchOperator
)
from search_pipeline.components.operator_library import (
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


def register_all_operators():
    """
    Register all available operators.
    
    Call this function once at application startup to populate the registry.
    """
    _register_metadata_filter()
    _register_semantic_search()
    _register_similarity_search()


# Auto-register on module import
register_all_operators()
