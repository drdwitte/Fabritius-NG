"""
Level configuration for label validation.

Defines the validation levels (EXPERT, HUMAN, AI) and their properties.
"""

from dataclasses import dataclass
from typing import List


# Validation level constants (matching database values)
VALIDATION_LEVEL_AI = "AI"
VALIDATION_LEVEL_HUMAN = "HUMAN"
VALIDATION_LEVEL_EXPERT = "EXPERT"


@dataclass
class ValidationLevel:
    """Configuration for a validation level."""
    name: str           # Internal name (e.g., "EXPERT")
    display_name: str   # Display name (e.g., "Expert")
    color: str          # Tailwind color class (e.g., "amber-700")
    enabled: bool       # Whether this level is active
    order: int          # Display order (0 = leftmost)
    description: str    # Description of what this level means


# Default validation levels
DEFAULT_LEVELS = [
    ValidationLevel(
        name="EXPERT",
        display_name="Expert",
        color="amber-700",
        enabled=True,
        order=0,
        description="Expert-validated labels with high confidence"
    ),
    ValidationLevel(
        name="HUMAN",
        display_name="Human",
        color="blue-600",
        enabled=True,
        order=1,
        description="Human-validated labels with moderate confidence"
    ),
    ValidationLevel(
        name="AI",
        display_name="AI",
        color="green-600",
        enabled=True,
        order=2,
        description="AI-suggested labels requiring validation"
    ),
]


def get_enabled_levels() -> List[ValidationLevel]:
    """Returns list of enabled validation levels in display order."""
    return sorted([level for level in DEFAULT_LEVELS if level.enabled], key=lambda x: x.order)


def get_level_by_name(name: str) -> ValidationLevel:
    """Get level configuration by name."""
    for level in DEFAULT_LEVELS:
        if level.name == name:
            return level
    raise ValueError(f"Unknown validation level: {name}")
