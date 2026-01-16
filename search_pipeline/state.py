"""
Pipeline state management.
This module contains the PipelineState class that manages the search pipeline configuration,
including operators, their parameters, and result counts.
"""

# Standard library imports
import json
import uuid
import copy
from typing import List, Dict, Optional
from loguru import logger

#this class keeps track of all (possible) operators in the pipeline
from search_pipeline.operator_registry import OperatorRegistry

class PipelineState:
    """
    Manages the search pipeline configuration (application state).
    Stores which operators are in the pipeline, their parameters, and execution results.
    This is domain/application state, not pure UI state. Each operator instance has a 
    unique UUID, allowing multiple instances of the same type with different configs.
    """
    
    def __init__(self):
        self._operators: List[Dict] = []
    
    def _find_index(self, operator_id: str) -> int:
        """
        Private helper: finds the index of an operator by ID.
        Returns -1 if not found.
        """
        for i, op in enumerate(self._operators):
            if op['id'] == operator_id:
                return i
        return -1
    
    def add_operator(self, operator_name: str) -> str:
        """
        Adds an operator to the pipeline.
        
        Args:
            operator_name: Name of the operator (must exist in OPERATOR_DEFINITIONS)
        
        Returns:
            Unique ID of the operator instance
            
        Raises:
            ValueError: If operator_name is not a valid operator
        """
        # Validate operator name
        if not OperatorRegistry.is_registered(operator_name):
            valid_names = ', '.join(OperatorRegistry.get_all_names())
            raise ValueError(
                f"Unknown operator '{operator_name}'. "
                f"Valid operators: {valid_names}"
            )
        
        # Generate a unique ID for the operator, 2 operators with same name can coexist, with different IDs
        operator_id = str(uuid.uuid4())
        operator = {
            'id': operator_id,
            'name': operator_name,
            'params': {},
            'result_count': None  # None until first execution
        }
        self._operators.append(operator)
        logger.info(f"Added '{operator_name}': {[op['name'] for op in self._operators]}")
        return operator_id
    
    def remove_operator(self, operator_id: str) -> bool:
        """
        Removes an operator by ID.
        Returns True if removed, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            removed_name = self._operators[index]['name']
            self._operators.pop(index)
            logger.info(f"Removed '{removed_name}': {[op['name'] for op in self._operators]}")
            return True
        return False
    
    def get_operator(self, operator_id: str) -> Optional[Dict]:
        """
        Gets a single operator by ID.
        Returns a deep copy to prevent external mutation.
        """
        index = self._find_index(operator_id)
        if index != -1:
            return copy.deepcopy(self._operators[index])
        return None
    
    def get_all_operators(self) -> List[Dict]:
        """Returns a deep copy of all operators to prevent external mutation."""
        return copy.deepcopy(self._operators)
    
    def update_params(self, operator_id: str, params: Dict) -> bool:
        """
        Updates the parameters of an operator.
        Replaces the entire params dict.
        Returns True if updated, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators[index]['params'] = params
            return True
        return False
    
    def update_result_count(self, operator_id: str, count: int) -> bool:
        """
        Updates the result count for an operator after execution.
        Returns True if updated, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators[index]['result_count'] = count
            logger.info(f"Updated result count for operator {operator_id}: {count} results")
            return True
        return False
    
    def move_left(self, operator_id: str) -> bool:
        """
        Moves an operator one position to the left (earlier in pipeline).
        Returns True if moved, False if already at start or not found.
        """
        index = self._find_index(operator_id)
        if index > 0:  # Can only move left if not at start
            # Swap with previous operator
            self._operators[index], self._operators[index - 1] = self._operators[index - 1], self._operators[index]
            logger.info(f"Moved '{self._operators[index]['name']}' left: {[op['name'] for op in self._operators]}")
            return True
        return False
    
    def move_right(self, operator_id: str) -> bool:
        """
        Moves an operator one position to the right (later in pipeline).
        Returns True if moved, False if already at end or not found.
        """
        index = self._find_index(operator_id)
        if index != -1 and index < len(self._operators) - 1:  # Can only move right if not at end
            # Swap with next operator
            self._operators[index], self._operators[index + 1] = self._operators[index + 1], self._operators[index]
            logger.info(f"Moved '{self._operators[index]['name']}' right: {[op['name'] for op in self._operators]}")
            return True
        return False
    
    def clear(self):
        """Removes all operators from the pipeline."""
        self._operators = []
        logger.info("Pipeline cleared")
    
    def to_json(self) -> str:
        """Export pipeline to JSON string."""
        return json.dumps(self._operators, indent=2)
    
    def from_json(self, json_string: str):
        """
        Import pipeline from JSON string.
        TODO: This should be enhanced with validation in the future.
        """
        self._operators = json.loads(json_string)
        logger.info(f"Loaded {len(self._operators)} operators from JSON")
