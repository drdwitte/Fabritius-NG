"""
Operator library component.

This module renders the operator library sidebar where users can select
and add operators to their pipeline. It also defines the operator schemas
using a builder pattern for better readability.
"""

from typing import Dict, Any, Optional
from nicegui import ui
from config import settings


class ParamBuilder:
    """Builder for operator parameter definitions."""
    
    def __init__(self, param_type: str):
        self._param = {'type': param_type}
    
    def label(self, text: str) -> 'ParamBuilder':
        self._param['label'] = text
        return self
    
    def description(self, text: str) -> 'ParamBuilder':
        self._param['description'] = text
        return self
    
    def default(self, value: Any) -> 'ParamBuilder':
        self._param['default'] = value
        return self
    
    def required(self, is_required: bool = True) -> 'ParamBuilder':
        self._param['required'] = is_required
        return self
    
    def options(self, opts: Any) -> 'ParamBuilder':
        self._param['options'] = opts
        return self
    
    def min_value(self, value: float) -> 'ParamBuilder':
        self._param['min'] = value
        return self
    
    def max_value(self, value: float) -> 'ParamBuilder':
        self._param['max'] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        return self._param


class OperatorBuilder:
    """Builder for operator definitions."""
    
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


def _build_operator_definitions() -> Dict[str, Any]:
    """
    Build operator definitions using builder pattern.
    This is much more readable and maintainable than nested dictionaries.
    """
    operators = {}
    
    # Metadata Filter Operator
    name, definition = (
        OperatorBuilder('Metadata Filter')
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
    operators[name] = definition
    
    # Semantic Search Operator
    name, definition = (
        OperatorBuilder('Semantic Search')
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
    operators[name] = definition
    
    # Similarity Search Operator
    name, definition = (
        OperatorBuilder('Similarity Search')
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
    operators[name] = definition
    
    return operators


# Build operator definitions once at module load
OPERATOR_DEFINITIONS = _build_operator_definitions()


def operator_card(operator_name: str, on_add):
    """
    Creates an operator card using the centralized settings configuration.
    
    Args:
        operator_name: Name of the operator to display
        on_add: Callback function to execute when the add button is clicked
    """
    operator = OPERATOR_DEFINITIONS[operator_name]
    
    with ui.row().classes('w-full items-center gap-3 p-3 rounded-lg bg-white shadow hover:bg-gray-100 transition'):
        # Operator icon
        ui.icon(operator['icon']).classes(f'text-3xl text-[{settings.brown}]')
        
        # Operator title + description
        with ui.column().classes('flex-1 items-start gap-0'):
            ui.label(operator_name).classes('text-base font-bold text-gray-800 mb-0')
            ui.label(operator['description']).classes('text-xs text-gray-500 mt-0')
        
        # Plus button to add operator
        (
            ui.button(icon='add', on_click=on_add)
                .props('round color=none text-color=none')
                .classes(f'bg-[{settings.brown}] text-white ml-auto text-xs p-0')
        )


def render_operator_library(pipeline_state, on_operator_added):
    """
    Renders the operator library sidebar.
    
    Args:
        pipeline_state: PipelineState instance for adding operators
        on_operator_added: Callback function to execute after an operator is added
    
    Returns:
        ui.column: The operator library container
    """
    with ui.column().classes('w-64 p-4 bg-gray-50 rounded-xl gap-4 shrink-0') as library:
        ui.label('OPERATOR LIBRARY').classes('text-sm font-bold text-gray-600 mb-2')
        
        # Render operator cards from the centralized operator definitions
        for operator_name in OPERATOR_DEFINITIONS.keys():
            def add_operator(op=operator_name):
                pipeline_state.add_operator(op)
                ui.notify(f'Added {op}')
                on_operator_added()
            
            operator_card(operator_name, add_operator)
    
    return library
