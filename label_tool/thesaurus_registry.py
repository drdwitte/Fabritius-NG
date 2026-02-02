"""
Thesaurus registry for label validation.

Manages available thesauri and their configurations.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ThesaurusInfo:
    """Information about a thesaurus."""
    id: str                    # Internal identifier
    display_name: str          # Display name for UI
    description: str           # Short description
    api_endpoint: Optional[str] = None  # API endpoint if available
    supports_search: bool = True        # Whether search is supported
    supports_create: bool = True        # Whether label creation is supported


# Available thesauri
AVAILABLE_THESAURI = [
    ThesaurusInfo(
        id="garnier",
        display_name="Garnier",
        description="Garnier thesaurus for art historical terminology",
        supports_search=True,
        supports_create=True,
    ),
    ThesaurusInfo(
        id="aat",
        display_name="AAT",
        description="Getty Art & Architecture Thesaurus",
        supports_search=True,
        supports_create=False,  # AAT is read-only
    ),
    ThesaurusInfo(
        id="iconclass",
        display_name="Iconclass",
        description="Iconclass iconographic classification system",
        supports_search=True,
        supports_create=False,  # Iconclass is read-only
    ),
    ThesaurusInfo(
        id="fabritius",
        display_name="Fabritius",
        description="Fabritius internal label system",
        supports_search=True,
        supports_create=True,
    ),
]


def get_thesaurus_names() -> List[str]:
    """Get list of thesaurus display names for UI."""
    return [t.display_name for t in AVAILABLE_THESAURI]


def get_thesaurus_by_name(name: str) -> Optional[ThesaurusInfo]:
    """Get thesaurus info by display name."""
    for thesaurus in AVAILABLE_THESAURI:
        if thesaurus.display_name == name:
            return thesaurus
    return None


def get_thesaurus_by_id(thesaurus_id: str) -> Optional[ThesaurusInfo]:
    """Get thesaurus info by ID."""
    for thesaurus in AVAILABLE_THESAURI:
        if thesaurus.id == thesaurus_id:
            return thesaurus
    return None
