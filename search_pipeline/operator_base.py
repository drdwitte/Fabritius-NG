"""
Abstract base class for search pipeline operators.

This module defines the Strategy pattern interface for operators,
allowing new operator types to be added without modifying existing code.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any


class Operator(ABC):
    """
    Abstract base class for all search pipeline operators.
    
    Implements the Strategy pattern - each operator type has its own
    implementation of execute(), but they all share the same interface.
    """
    
    def __init__(self, name: str, icon: str, description: str):
        """
        Initialize operator with metadata.
        
        Args:
            name: Display name of the operator
            icon: Material icon name for UI
            description: User-friendly description
        """
        self.name = name
        self.icon = icon
        self.description = description
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Tuple[List[Dict], int]:
        """
        Execute the operator with given parameters.
        
        Args:
            params: Dictionary of operator-specific parameters
            
        Returns:
            Tuple of (preview_results, total_count):
            - preview_results: List of artwork dictionaries for preview
            - total_count: Total number of results (may be > len(preview_results))
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this operator.
        
        Returns:
            Dictionary describing the parameters this operator accepts.
            Used to generate the configuration UI dynamically.
        """
        pass
    
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate operator parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_messages):
            - is_valid: True if all parameters are valid
            - error_messages: List of error messages if invalid
        """
        pass
    
    @abstractmethod
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """
        Check if operator has minimum required configuration.
        
        Args:
            params: Current operator parameters
            
        Returns:
            True if operator can be executed, False if needs configuration
        """
        pass
    
    @abstractmethod
    def get_loading_message(self) -> str:
        """
        Get the loading message to display during execution.
        
        Returns:
            User-friendly message shown while operator is executing
        """
        pass
    
    @abstractmethod
    def get_unconfigured_message(self) -> str:
        """
        Get the message to display when operator is not configured.
        
        Returns:
            User-friendly message prompting user to configure operator
        """
        pass
