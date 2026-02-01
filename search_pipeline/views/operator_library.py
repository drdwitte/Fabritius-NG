"""
Operator library component.

This module renders the operator library sidebar where users can select
and add operators to their pipeline. It also defines the operator schemas
using a builder pattern for better readability.
"""

from typing import Dict, Any, Optional
from nicegui import ui
from config import settings

from search_pipeline.operator_registry import OperatorRegistry


def operator_card(operator_name: str, on_add, operator_definitions: Dict):
    """
    Creates an operator card using the centralized settings configuration.
    
    Args:
        operator_name: Name of the operator to display
        on_add: Callback function to execute when the add button is clicked
        operator_definitions: Dictionary of operator definitions from registry
    """
    operator = operator_definitions[operator_name]
    
    with ui.row().classes('w-full items-center gap-3 p-3 rounded-lg bg-white shadow hover:bg-gray-100 transition'):
        # Operator icon
        ui.icon(operator['icon']).classes(f'text-3xl text-[{settings.primary_color}]')
        
        # Operator title + description
        with ui.column().classes('flex-1 items-start gap-0'):
            ui.label(operator_name).classes('text-base font-bold text-gray-800 mb-0')
            ui.label(operator['description']).classes('text-xs text-gray-500 mt-0')
        
        # Plus button to add operator
        (
            ui.button(icon='add', on_click=on_add)
                .props('round color=none text-color=none')
                .classes(f'bg-[{settings.primary_color}] text-white ml-auto text-xs p-0')
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
    # Lazy evaluation: fetch definitions at runtime, not during import
    operator_definitions = OperatorRegistry.get_all_definitions()
    
    with ui.column().classes('w-64 p-4 bg-gray-50 rounded-xl gap-4 shrink-0') as library:
        ui.label('OPERATOR LIBRARY').classes('text-sm font-bold text-gray-600 mb-2')
        
        # Render operator cards from the centralized operator definitions
        for operator_name in operator_definitions.keys():
            def add_operator(op=operator_name):
                pipeline_state.add_operator(op)
                ui.notify(f'Added {op}')
                on_operator_added()
            
            operator_card(operator_name, add_operator, operator_definitions)
    
    return library
