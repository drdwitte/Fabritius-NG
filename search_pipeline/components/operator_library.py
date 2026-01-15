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


# Import registry and auto-register all operators
import search_pipeline.operator_registration  # noqa: F401 - triggers auto-registration
from search_pipeline.operator_registry import OperatorRegistry

# Expose registry as OPERATOR_DEFINITIONS for backward compatibility
# TODO: Migrate all code to use OperatorRegistry directly
OPERATOR_DEFINITIONS = OperatorRegistry.get_all_definitions()


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
