"""
Search pipeline package.

This package provides the search pipeline functionality for the Fabritius-NG application.
It includes state management, operator execution, and UI rendering components.

Main entry point: render_search()
"""

from .state import PipelineState
from .operators import execute_semantic_search, execute_metadata_filter, execute_similarity_search
from .ui_helpers import icon_button, run_button, format_param_value, save_pipeline, load_pipeline, show_artwork_detail
from .preview_coordinator import show_preview_for_operator
from .operator_base import Operator
from .operator_implementations import SemanticSearchOperator, MetadataFilterOperator, SimilaritySearchOperator
from .operator_registry import OperatorRegistry

__all__ = [
    'PipelineState',
    'execute_semantic_search',
    'execute_metadata_filter',
    'execute_similarity_search',
    'icon_button',
    'run_button',
    'format_param_value',
    'save_pipeline',
    'load_pipeline',
    'show_artwork_detail',
    'show_preview_for_operator',
    'Operator',
    'OperatorRegistry',
    'SemanticSearchOperator',
    'MetadataFilterOperator',
    'SimilaritySearchOperator',
]
