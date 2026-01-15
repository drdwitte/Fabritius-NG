"""
Centralized operator registry.

This module provides a single source of truth for all operator information:
- UI metadata (icon, description, parameter schema)
- Implementation class (for execution)

This eliminates the risk of mismatched names between OPERATOR_DEFINITIONS
and OperatorFactory, and makes adding new operators easier.
"""

from typing import Dict, Any, Type, List
from loguru import logger
from search_pipeline.operator_base import Operator


# Operator name constants - single source of truth
class OperatorNames:
    """Centralized operator name constants."""
    METADATA_FILTER = "Metadata Filter"
    SEMANTIC_SEARCH = "Semantic Search"
    SIMILARITY_SEARCH = "Similarity Search"


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
                 implementation: Type[Operator]) -> None:
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
            
        Returns:
            Operator instance
            
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
