"""
Builder classes for operator definitions.

Separated from operator_library.py to avoid circular imports.
"""

from typing import Dict, Any, Optional


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
