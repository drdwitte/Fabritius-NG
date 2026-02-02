"""
Algorithm registry for label validation.

Manages available validation algorithms and their configurations.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AlgorithmInfo:
    """Information about a validation algorithm."""
    id: str                    # Internal identifier
    display_name: str          # Display name for UI
    description: str           # Short description
    requires_model: bool = False  # Whether this requires a loaded model
    model_name: Optional[str] = None  # Model identifier if required


@dataclass
class AlgorithmInfo:
    """Information about a validation algorithm."""
    id: str                    # Internal identifier
    display_name: str          # Display name for UI
    description: str           # Short description
    requires_model: bool = False  # Whether this requires a loaded model
    model_name: Optional[str] = None  # Model identifier if required


# Available validation algorithms
AVAILABLE_ALGORITHMS = [
    AlgorithmInfo(
        id="text_embedding",
        display_name="Text",
        description="Text-based semantic similarity search",
        requires_model=False,
    ),
    AlgorithmInfo(
        id="multimodal_embedding",
        display_name="Multimodal",
        description="Vision-language model for image-text matching",
        requires_model=True,
        model_name="clip-vit-base-patch32",
    ),
]


def get_algorithm_names() -> List[str]:
    """Get list of algorithm display names for UI."""
    return [a.display_name for a in AVAILABLE_ALGORITHMS]


def get_algorithm_by_name(name: str) -> Optional[AlgorithmInfo]:
    """Get algorithm info by display name."""
    for algorithm in AVAILABLE_ALGORITHMS:
        if algorithm.display_name == name:
            return algorithm
    return None


def get_algorithm_by_id(algorithm_id: str) -> Optional[AlgorithmInfo]:
    """Get algorithm info by ID."""
    for algorithm in AVAILABLE_ALGORITHMS:
        if algorithm.id == algorithm_id:
            return algorithm
    return None


def get_enabled_algorithms(selected: List[str]) -> List[AlgorithmInfo]:
    """Get algorithm info for selected algorithms."""
    return [get_algorithm_by_name(name) for name in selected if get_algorithm_by_name(name)]


