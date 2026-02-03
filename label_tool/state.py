"""
State management for label validation.

Manages the state of label validation including search results per box.

Box structure:
- AI algorithm boxes: One per selected algorithm (e.g., "AI-Text", "AI-Multimodal")
- Validated level boxes: Fixed three boxes ("AI", "HUMAN", "EXPERT")
"""

# dataclass: simplified class for managing data attributes; field: for default values
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .level_config import VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT


@dataclass
class ValidationResults:
    """Results for a single validation unit (algorithm or validation level)."""
    box_key: str                             # e.g., "AI-Text", "Human", "Expert"
    box_label: str                           # Display label
    results: List[Dict[str, Any]] = field(default_factory=list)  # Artwork results: field => default empty list
    total_count: int = 0                     # Total results for this box
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
    
    # Selected validation algorithms (for AI algorithm boxes)
    selected_algorithms: List[str] = field(default_factory=list)
    
    # Selected validation levels (for validated level boxes)
    selected_levels: List[str] = field(default_factory=list)  # e.g., ["AI", "HUMAN", "EXPERT"]
    
    # Closed boxes (which boxes are hidden)
    closed_boxes: List[str] = field(default_factory=list)  # e.g., ["AI-Multimodal", "Expert"]
    
    # Results per box (both AI algorithms and validated levels)
    # Keys: "AI-Text", "AI-Multimodal", "AI", "HUMAN", "EXPERT"
    results_per_box: Dict[str, ValidationResults] = field(default_factory=dict)
    
    # Selected artworks per box (for bulk actions)
    # Keys: box_key, Values: set of artwork IDs
    selected_artworks: Dict[str, set] = field(default_factory=dict)
    
    # Hidden artwork IDs (per box)
    hidden_artworks: Dict[str, set] = field(default_factory=dict)
    
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
        """Clear results for all boxes."""
        for box_results in self.results_per_box.values():
            box_results.clear()
        self.is_searching = False
        self.search_error = None
    
    def get_box_results(self, box_key: str) -> ValidationResults:
        """Get results for a specific box."""
        if box_key not in self.results_per_box:
            self.results_per_box[box_key] = ValidationResults(
                box_key=box_key,
                box_label=box_key
            )
        return self.results_per_box[box_key]
    
    def get_ai_box_keys(self) -> List[str]:
        """Get all possible AI algorithm box keys (Text and Multimodal)."""
        return ["AI-Text", "AI-Multimodal"]
    
    def get_open_ai_box_keys(self) -> List[str]:
        """Get AI algorithm box keys that are open (not closed)."""
        return [key for key in self.get_ai_box_keys() if key not in self.closed_boxes]
    
    def get_validated_box_keys(self) -> List[str]:
        """Get all validated level box keys."""
        return [VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT]
    
    def get_open_validated_box_keys(self) -> List[str]:
        """Get validated level box keys that are open (not closed)."""
        return [key for key in self.get_validated_box_keys() if key not in self.closed_boxes]
    
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
        """Check if any box has results."""
        return any(box.total_count > 0 for box in self.results_per_box.values())
    
    # ========== Selection Management ==========
    
    def toggle_artwork_selection(self, box_key: str, artwork_id: str):
        """Toggle artwork selection in a box."""
        if box_key not in self.selected_artworks:
            self.selected_artworks[box_key] = set()
        
        if artwork_id in self.selected_artworks[box_key]:
            self.selected_artworks[box_key].remove(artwork_id)
        else:
            self.selected_artworks[box_key].add(artwork_id)
    
    def select_all_artworks(self, box_key: str):
        """Select all visible (non-hidden) artworks in a box."""
        if box_key in self.results_per_box:
            results = self.results_per_box[box_key].results
            # Only select visible artworks (not marked as hidden)
            self.selected_artworks[box_key] = {
                r.get('id', r.get('inventory_number')) 
                for r in results 
                if not r.get('_hidden', False)
            }
    
    def deselect_all_artworks(self, box_key: str):
        """Deselect all artworks in a box."""
        if box_key in self.selected_artworks:
            self.selected_artworks[box_key].clear()
    
    def get_selected_artworks(self, box_key: str) -> set:
        """Get selected artwork IDs for a box."""
        return self.selected_artworks.get(box_key, set())
    
    def has_selected_artworks(self, box_key: str) -> bool:
        """Check if any artworks are selected in a box."""
        return bool(self.selected_artworks.get(box_key))
    
    def is_artwork_selected(self, box_key: str, artwork_id: str) -> bool:
        """Check if an artwork is selected."""
        return artwork_id in self.selected_artworks.get(box_key, set())
