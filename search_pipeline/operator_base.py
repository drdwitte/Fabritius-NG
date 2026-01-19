"""
Abstract base class for search pipeline operators.

This module defines the Strategy pattern interface for operators,
allowing new operator types to be added without modifying existing code.
"""

#ABC = Abstract Base Class
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from loguru import logger


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
        self._pydantic_model: Optional[type[BaseModel]] = None
    
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
    def is_configured(self, params: Dict[str, Any]) -> bool:
        """
        Check if operator has minimum required configuration.
      
        Args:
            params: Current operator parameters
            
        Returns:
            True if operator can be executed, False if needs configuration
        """
        pass
    
    def get_loading_message(self) -> str:
        """
        Get the loading message to display during execution.
        """
        return 'Retrieving results from SQL database...'
    
    def get_unconfigured_message(self) -> str:
        """
        Get the message to display when operator is not configured.
        """
        return f'Please configure the {self.name} first'
    
    def set_pydantic_model(self, model: type[BaseModel]):
        """
        Set Pydantic model for parameter validation (optional).
        
        Args:
            model: Pydantic BaseModel class for validation
        """
        self._pydantic_model = model
    
    def validate_params(self, params: Dict[str, Any]) -> Any:
        """
        Validate parameters using Pydantic model if available.
        
        Args:
            params: Raw parameter dictionary
            
        Returns:
            Validated Pydantic model instance, or original dict if no model set
            
        Raises:
            ValidationError: If parameters don't match schema
        """
        if self._pydantic_model is None:
            # No validation model set, return params as-is
            return params
        
        try:
            # Validate and return Pydantic model instance
            validated = self._pydantic_model(**params)
            logger.debug(f"Parameters validated successfully for {self.name}")
            return validated
        except ValidationError as e:
            logger.error(f"Parameter validation failed for {self.name}: {e}")
            raise
