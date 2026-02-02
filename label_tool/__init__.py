"""
Label tool package for the Fabritius-NG application.

ARCHITECTURE
============
This package handles all label validation logic, following the same architecture
pattern as the search_pipeline package. It provides a complete multi-level 
validation system with support for EXPERT, HUMAN, and AI validation levels.

PACKAGE STRUCTURE
=================
- state.py: LabelState and LevelResults classes for state management
- level_config.py: ValidationLevel definitions (EXPERT, HUMAN, AI)
- thesaurus_registry.py: Available thesauri (Garnier, AAT, Iconclass, Fabritius)
- algorithm_registry.py: Validation algorithms (Semantic Search, CLIP, BLIP)
- label_service.py: API interface for thesaurus CRUD operations
- validation_engine.py: Core validation logic
- views/: Reusable view components (search_bar, label_card, level_column)

CORE COMPONENTS
===============

State Management (state.py):
----------------------------
- LabelState: Main state container with selected thesaurus, label, algorithms,
  and results_per_level dictionary
- LevelResults: Results for a single validation level (EXPERT/HUMAN/AI) with
  artwork results, loading state, and error handling

Level Configuration (level_config.py):
--------------------------------------
- ValidationLevel: Level properties (name, display_name, color, enabled, order)
- DEFAULT_LEVELS: Pre-configured EXPERT (amber), HUMAN (blue), AI (green) levels
- get_enabled_levels(): Returns active levels in display order

Registries:
-----------
- ThesaurusInfo: Thesaurus metadata with CRUD support flags
  * Garnier: Full CRUD support
  * AAT: Read-only (Getty)
  * Iconclass: Read-only
  * Fabritius: Full CRUD support

- AlgorithmInfo: Validation algorithm metadata with model requirements
  * Semantic Search: Text-based similarity
  * CLIP: Vision-language model
  * BLIP: Image-text pre-training

Services:
---------
- LabelService: API interface for thesaurus operations
  * search_labels(query): Search in thesaurus
  * get_label(label_id): Fetch specific label
  * create_label(name, definition): Create new label
  * update_label(), delete_label(): Modify labels

- ValidationEngine: Core validation logic
  * validate_label(): Run validation across all enabled levels
  * Returns LevelResults per level with ranked artwork matches

USAGE EXAMPLE
=============
```python
from label_tool import (
    LabelState,
    get_enabled_levels,
    LabelService,
    ValidationEngine
)

# Initialize state
state = LabelState()
state.selected_thesaurus = "Garnier"
state.label_name = "Landscape"
state.selected_algorithms = ["Semantic Search", "CLIP"]

# Create label service and validation engine
service = LabelService("garnier")
engine = ValidationEngine()

# Run validation
results = await engine.validate_label(
    label_name=state.label_name,
    label_definition=state.label_definition,
    algorithms=state.selected_algorithms,
    state=state
)

# Access results per level
for level in get_enabled_levels():
    level_results = state.get_level_results(level.name)
    print(f"{level.display_name}: {level_results.total_count} results")
```

INTEGRATION WITH pages/label.py
================================
The page module uses the Controller Pattern:
- LabelPageController owns LabelState and ValidationEngine instances
- Delegates all business logic to this package
- Uses view components from label_tool.views
- Maintains only UI state and coordinates rendering

DATA FLOW
=========
1. User selects label → LabelService.create_label()
2. User selects algorithms → state.selected_algorithms updated
3. User clicks Search → ValidationEngine.validate_label()
4. For each level (EXPERT, HUMAN, AI):
   - Set level.is_loading = True
   - Run validation algorithms
   - Store results in LevelResults
   - Render column with results

MULTI-LEVEL ARCHITECTURE
========================
- Each validation level (EXPERT, HUMAN, AI) gets independent results
- Levels are defined in level_config.py with display properties
- Results stored in state.results_per_level: Dict[str, LevelResults]
- Validation engine runs queries per level
- UI renders columns side-by-side for comparison
"""

from .state import LabelState, ColumnResults
from .level_config import (
    ValidationLevel, 
    DEFAULT_LEVELS, 
    get_enabled_levels, 
    get_level_by_name,
    VALIDATION_LEVEL_AI,
    VALIDATION_LEVEL_HUMAN,
    VALIDATION_LEVEL_EXPERT
)
from .thesaurus_registry import ThesaurusInfo, AVAILABLE_THESAURI, get_thesaurus_names, get_thesaurus_by_name
from .algorithm_registry import AlgorithmInfo, AVAILABLE_ALGORITHMS, get_algorithm_names, get_algorithm_by_name
from .label_service import LabelService
from .validation_engine import ValidationEngine

__all__ = [
    # State
    'LabelState',
    'ColumnResults',
    
    # Level config
    'ValidationLevel',
    'DEFAULT_LEVELS',
    'get_enabled_levels',
    'get_level_by_name',
    'VALIDATION_LEVEL_AI',
    'VALIDATION_LEVEL_HUMAN',
    'VALIDATION_LEVEL_EXPERT',
    
    # Thesaurus
    'ThesaurusInfo',
    'AVAILABLE_THESAURI',
    'get_thesaurus_names',
    'get_thesaurus_by_name',
    
    # Algorithms
    'AlgorithmInfo',
    'AVAILABLE_ALGORITHMS',
    'get_algorithm_names',
    'get_algorithm_by_name',
    
    # Services
    'LabelService',
    'ValidationEngine',
]
