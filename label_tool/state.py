"""
State management for label validation.

Manages the state of label validation including search results per column.

Column structure:
- AI columns: One per selected algorithm (e.g., "AI-Text", "AI-Multimodal")
- Validated columns: Fixed three columns ("AI", "HUMAN", "EXPERT")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .level_config import VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT


@dataclass
class ColumnResults:
    """Results for a single column (algorithm or validation level)."""
    column_key: str                          # e.g., "AI-Text", "Human", "Expert"
    column_label: str                        # Display label
    results: List[Dict[str, Any]] = field(default_factory=list)  # Artwork results
    total_count: int = 0                     # Total results for this column
    is_loading: bool = False                 # Whether results are being loaded
    error: Optional[str] = None              # Error message if loading failed
    
    def clear(self):
        """Clear all results."""
        self.results = []
        self.total_count = 0
        self.is_loading = False
        self.error = None


@dataclass
class LabelState:
    """State for the label validation page."""
    
    # Selected thesaurus and label
    selected_thesaurus: Optional[str] = None  # Current thesaurus (None = free search)
    label_name: Optional[str] = None         # Current label being validated
    label_definition: Optional[str] = None   # Label definition (if available)
    label_id: Optional[str] = None           # Label ID in thesaurus system
    
    # Cached thesaurus terms for autocomplete
    cached_thesaurus_terms: List[str] = field(default_factory=list)  # Terms from selected thesaurus
    
    # Selected validation algorithms (for AI columns)
    selected_algorithms: List[str] = field(default_factory=list)
    
    # Selected validation levels (for validated rows)
    selected_levels: List[str] = field(default_factory=list)  # e.g., ["AI", "HUMAN", "EXPERT"]
    
    # Closed boxes (which boxes are hidden)
    closed_boxes: List[str] = field(default_factory=list)  # e.g., ["AI-Multimodal", "Expert"]
    
    # Results per column (both AI and validated)
    # Keys: "AI-Text", "AI-Multimodal", "AI", "HUMAN", "EXPERT"
    results_per_column: Dict[str, ColumnResults] = field(default_factory=dict)
    
    # View mode
    view_mode: str = 'grid'                  # 'grid' or 'list'
    
    # UI state
    is_searching: bool = False               # Whether search is in progress
    search_error: Optional[str] = None       # Error message if search failed
    
    def has_label(self) -> bool:
        """Check if a label is currently selected."""
        return self.label_name is not None
    
    def clear_label(self):
        """Clear the current label and all results."""
        self.label_name = None
        self.label_definition = None
        self.label_id = None
        self.clear_all_results()
    
    def clear_all_results(self):
        """Clear results for all columns."""
        for column_results in self.results_per_column.values():
            column_results.clear()
        self.is_searching = False
        self.search_error = None
    
    def get_column_results(self, column_key: str) -> ColumnResults:
        """Get results for a specific column."""
        if column_key not in self.results_per_column:
            self.results_per_column[column_key] = ColumnResults(
                column_key=column_key,
                column_label=column_key
            )
        return self.results_per_column[column_key]
    
    def get_ai_column_keys(self) -> List[str]:
        """Get all possible AI column keys (Text and Multimodal)."""
        return ["AI-Text", "AI-Multimodal"]
    
    def get_open_ai_column_keys(self) -> List[str]:
        """Get AI column keys that are open (not closed)."""
        return [key for key in self.get_ai_column_keys() if key not in self.closed_boxes]
    
    def get_validated_column_keys(self) -> List[str]:
        """Get all validated column keys."""
        return [VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT]
    
    def get_open_validated_column_keys(self) -> List[str]:
        """Get validated column keys that are open (not closed)."""
        return [key for key in self.get_validated_column_keys() if key not in self.closed_boxes]
    
    def is_box_open(self, box_key: str) -> bool:
        """Check if a box is open (not closed)."""
        return box_key not in self.closed_boxes
    
    def toggle_box(self, box_key: str):
        """Toggle a box open/closed state."""
        if box_key in self.closed_boxes:
            self.closed_boxes.remove(box_key)
        else:
            self.closed_boxes.append(box_key)
        
        # Sync selected algorithms for AI boxes
        if box_key.startswith("AI-"):
            algo_name = box_key.split("-", 1)[1]
            if box_key in self.closed_boxes and algo_name in self.selected_algorithms:
                self.selected_algorithms.remove(algo_name)
            elif box_key not in self.closed_boxes and algo_name not in self.selected_algorithms:
                self.selected_algorithms.append(algo_name)
    
    def has_any_results(self) -> bool:
        """Check if any column has results."""
        return any(col.total_count > 0 for col in self.results_per_column.values())
