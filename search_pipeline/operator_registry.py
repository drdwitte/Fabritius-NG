"""
Centralized operator registry with auto-registration.

⚠️ IMPORTANT: This module automatically registers all operators when imported.
   - operator_registration.py has been REMOVED (was redundant)
   - Registration happens at the bottom of this file (see "# Auto-register..." section)
   - No need to call register_all_operators() anywhere
   - Just import OperatorRegistry and operators are ready to use

This module provides a single source of truth for all operator information:
- UI metadata (icon, description, parameter schema)
- Implementation class (for execution)

This eliminates the risk of mismatched names between OPERATOR_DEFINITIONS
and OperatorFactory, and makes adding new operators easier.
"""

from typing import Dict, Any, Type, List
from loguru import logger
from search_pipeline.operator_base import Operator


# ============================================================================
# BUILDER CLASSES
# ============================================================================

class ParamBuilder:
    """Builder for operator parameter definitions."""
    
    def __init__(self, param_type: str):
        self._param = {'type': param_type}
    
    def label(self, text: str): 
        """ Set the label of the parameter, for example "Artist Name".
        """
        self._param['label'] = text
        return self
    
    def description(self, text: str): 
        """ Set the description of the parameter, for example "Full or partial artist name".
        """
        self._param['description'] = text
        return self
    
    def default(self, value: Any):
        """ Set the default value of the parameter, for example an empty string or a specific number.
        """
        self._param['default'] = value
        return self
    
    def required(self, is_required: bool = True):
        self._param['required'] = is_required
        return self
    
    def options(self, opts: Any):
        """ Set the options for the parameter, for example a list of selectable values.
        """
        self._param['options'] = opts
        return self
    
    def min_value(self, value: float):
        self._param['min'] = value
        return self
    
    def max_value(self, value: float):
        self._param['max'] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """ Finalize and return the parameter definition dictionary. 
        For example: { 'type': 'text', 'label': 'Artist Name', 'description': '... ' } 
        """
        return self._param


class OperatorBuilder:
    """Builder for operator definitions. Constructs operator schema step by step, relying on
    ParamBuilder for parameter definitions.
    """
    
    def __init__(self, name: str):
        self._name = name
        self._operator = {'params': {}}
    
    def icon(self, icon_name: str) -> 'OperatorBuilder':
        self._operator['icon'] = icon_name
        return self
    
    def description(self, text: str) -> 'OperatorBuilder':
        self._operator['description'] = text
        return self
    
    def param(self, name: str, param: ParamBuilder) -> 'OperatorBuilder':
        self._operator['params'][name] = param.build()
        return self
    
    def build(self) -> tuple[str, Dict[str, Any]]:
        return (self._name, self._operator)


# ============================================================================
# REGISTRY
# ============================================================================

# Operator name constants - single source of truth
class OperatorNames:
    """Centralized operator name constants."""
    METADATA_FILTER = "Metadata Filter"
    SEMANTIC_SEARCH = "Semantic Search"
    SIMILARITY_SEARCH = "Similarity Search"
    POSE_SEARCH = "Pose Search"
    SKETCH_SEARCH = "Sketch Search"
    COLOR_SEARCH = "Color-Based Search"


class OperatorRegistry:
    """
    Central registry for all operators.
    
    Combines UI metadata and implementation class in one place.
    """
    
    _registry: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, 
                 name: str, 
                 icon: str, 
                 description: str,
                 params: Dict[str, Any],
                 implementation: Type[Operator]):
        """
        Register an operator with all its metadata and implementation.
        
        Args:
            name: Operator name (e.g., "Semantic Search")
            icon: Material icon name (e.g., "search")
            description: User-friendly description
            params: Parameter schema for UI config panel
            implementation: Operator class (subclass of Operator)
        """
        if name in cls._registry:
            logger.warning(f"Operator '{name}' is already registered. Overwriting.")
        
        cls._registry[name] = {
            'icon': icon,
            'description': description,
            'params': params,
            'implementation': implementation
        }
        logger.debug(f"Registered operator: {name}")
    
    @classmethod
    def create(cls, operator_name: str) -> Operator:
        """
        Create an operator instance by name.
        
        Args:
            operator_name: Name of the operator to create
        Raises:
            KeyError: If operator name is not registered
        """
        if operator_name not in cls._registry:
            available = ', '.join(cls.get_all_names())
            raise KeyError(
                f"Unknown operator '{operator_name}'. "
                f"Available operators: {available}"
            )
        
        implementation_class = cls._registry[operator_name]['implementation']
        return implementation_class()
    
    @classmethod
    def get_metadata(cls, operator_name: str) -> Dict[str, Any]:
        """
        Get UI metadata for an operator (icon, description, params).
        
        Args:
            operator_name: Name of the operator
            
        Returns:
            Dictionary with 'icon', 'description', and 'params' keys
            
        Raises:
            KeyError: If operator name is not registered
        """
        if operator_name not in cls._registry:
            raise KeyError(f"Unknown operator: {operator_name}")
        
        entry = cls._registry[operator_name]
        return {
            'icon': entry['icon'],
            'description': entry['description'],
            'params': entry['params']
        }
    
    @classmethod
    def get_all_names(cls) -> List[str]:
        """Get list of all registered operator names."""
        return list(cls._registry.keys())
    
    @classmethod
    def get_all_definitions(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get all operator definitions (for backward compatibility with OPERATOR_DEFINITIONS).
        
        Returns:
            Dictionary mapping operator names to their metadata (icon, description, params)
        """
        return {
            name: {
                'icon': entry['icon'],
                'description': entry['description'],
                'params': entry['params']
            }
            for name, entry in cls._registry.items()
        }
    
    @classmethod
    def is_registered(cls, operator_name: str) -> bool:
        """Check if an operator is registered."""
        return operator_name in cls._registry


# ============================================================================
# OPERATOR REGISTRATION
# ============================================================================
# All operators are registered here and auto-loaded when this module is imported

from search_pipeline.operator_implementations import (
    SemanticSearchOperator,
    MetadataFilterOperator,
    SimilaritySearchOperator,
    PoseSearchOperator,
    SketchSearchOperator,
    ColorSearchOperator
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


# Auto-register all operators on module import
logger.info("Auto-registering all operators...")
_register_metadata_filter()
_register_semantic_search()
_register_similarity_search()
_register_pose_search()
_register_sketch_search()
_register_color_search()
logger.info(f"Successfully registered {len(OperatorRegistry._registry)} operators")
