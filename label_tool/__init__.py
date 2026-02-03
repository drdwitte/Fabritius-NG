"""
Label tool package for the Fabritius-NG application.

ARCHITECTURE: Page Controller Pattern
======================================

This package follows the Page Controller Pattern:

- Page Controller Pattern: LabelPageController orchestrates all interactions for the label page.
  It manages three types of state:
  - Model: label_state (validation levels & results) + selection_state (bulk actions)
  - View References: ui_state (handles to UI containers, not the view itself)
  - View: views/*.py (actual UI rendering: result_cards, column_header, action_bar)

The controller manipulates the state (LabelState) which tracks artworks across multiple 
validation levels (AI, HUMAN, EXPERT). Artworks flow between levels via promote/demote operations.


PACKAGE: Label Validation
==========================

This package provides multi-row label validation with AI algorithms and human oversight.

Key Components:
- state.py: LabelState, ValidationResults - manages validation state & results
  - LabelState: Tracks selected label, thesaurus, levels, results per row, selections
  - ValidationResults: Holds results for each validation row (AI algorithms + levels)

- level_config.py: ValidationLevel definitions (AI, HUMAN, EXPERT)
- algorithm_registry.py: Available algorithms (Text/Image Embeddings) + auto-registration (registry pattern)
- validation_engine.py: Query engine with core validation logic & artwork ranking (currently stub with mock data)
- label_service.py: Thesaurus CRUD operations
- views/: UI view layer (result_cards, column_header, action_bar, search_bar)

Entry Point:
- pages/label.py: Creates LabelPageController per client session
- Controller manages: label_state, ui_state, selection_state
- Algorithms are auto-registered when algorithm_registry.py is imported

User Flows:
===========

Flow 1: Search with Thesaurus Label
------------------------------------
1. User selects thesaurus from dropdown (e.g., "Iconclass", "AAT")
2. Searches for label in thesaurus via search_bar.py
3. Selects label from thesaurus results
4. If label is not found in Fabritius give the option to create it in Fabritius thesaurus
4. Selects AI algorithms (Text/Image Embeddings)
5. Clicks search → validation_engine.validate_label()
6. Results appear in AI Results row (one column per algorithm)
7. User validates results → promotes to HUMAN → EXPERT levels

Flow 2: Search with Free-Text Label (Non-Existing)
---------------------------------------------------
1. User types arbitrary text in search_bar.py (e.g., "blue sky")
2. Label not found in any thesaurus
3. System offers option: "Create new label in Fabritius?"
4. If yes → label created in Fabritius thesaurus
5. Proceeds with validation flow (select algorithms → search → validate)
6. If no → user can refine search or select different thesaurus

Flow 3: Search with Existing Fabritius Label
---------------------------------------------
1. User selects "Fabritius" thesaurus
2. Searches for label (e.g., "portrait", "landscape")
3. Selects existing Fabritius label
4. Option available: "Delete label" (removes from Fabritius thesaurus)
5. If not deleted → proceeds with validation flow
6. Results shown in AI Results → HUMAN → EXPERT levels

Flow 4: Create Custom Label with Definition
--------------------------------------------
1. User creates new label with custom definition
2. Types label name + definition text in search_bar.py
3. Optional: Enrich definition with external data sources:
   - Search Wikidata for related concepts
   - Import descriptions, synonyms, related terms
   - Add contextual information to build better search query
4. System constructs enhanced search query from label + definition + external data
5. Label saved to Fabritius thesaurus with enriched metadata
6. Proceeds with validation flow (select algorithms → search → validate)
7. AI algorithms use enriched query for better artwork matching

Flow 5: Validation & Promotion
-------------------------------
1. After search, results populate AI Results row (per algorithm column)
2. User reviews artworks in grid/list view
3. Selects artworks via checkboxes (individual or "Select All")
4. Action bar appears with bulk actions:
   - Promote ⬇️: Move selected to next level (AI Results → HUMAN → EXPERT)
   - Demote ⬆️: Move back to previous level
   - Delete 🗑️: Remove label assignments from backend
   - Hide 👁️: Hide artworks, show next results
5. Results re-rendered via result_cards.py
6. Process repeats until expert validation complete

Provenance Levels:
==================
Labels can be validated in three provenance levels: AI, HUMAN, and EXPERT.
On top we can run multiple AI algorithms (e.g. Text Embeddings, Image Embeddings) in parallel, 
which populate the AI Results row. 

Users can then promote results from these AI Algorithm columns to the AI row, and from there to HUMAN and EXPERT, 
or demote them back down. Bulk actions (select, promote, demote, delete, hide) are supported 
to speed up the human validation process.


UI Layout:
==========

1. AI Results Row (collapsible, gray-600 header):
   - Contains multiple algorithm columns side-by-side
   - Columns: "AI-Text Embeddings", "AI-Image Embeddings"
   - Each algorithm column shows results from that specific model
   - Algorithms can be added/removed dynamically via checkboxes
   - Rose-600 for first algorithm, Emerald-600 for second

2. Validated Rows (full-width, one per level):
   - AI Row (purple-600): Combined AI results awaiting validation
   - HUMAN Row (blue-600): Human-validated labels
   - EXPERT Row (amber-700): Expert-validated labels (Fabritius brown)
   
Each row contains a grid/list of artwork results and can be collapsed independently.


Bulk Actions:
=============
- Checkboxes on each artwork tile (grid and list view)
- Select all / Deselect all buttons in column headers
- Action bar appears when items selected:
  * Promote ⬇️: AI algorithms → HUMAN → EXPERT
  * Demote ⬆️: EXPERT → HUMAN → AI Results
  * Delete 🗑️: Remove labels from backend
  * Hide 👁️: Hide artworks and show next results

Note: Algorithms are auto-registered when algorithm_registry.py is imported.
This happens automatically - no manual registration needed.

Note: ValidationEngine currently uses mock data (mock_data.py) for testing.
Production implementation will integrate with backend/llms.py (embeddings) 
and backend/supabase_client.py (vector similarity search).
"""

from .state import LabelState, ValidationResults
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

# Define what will be imported with 'from label_tool import *'
__all__ = [
    # State
    'LabelState',
    'ValidationResults',
    
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
