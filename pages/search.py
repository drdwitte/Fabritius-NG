"""
Search page for the Fabritius-NG application.

ARCHITECTURE: Thin Coordinator Pattern
======================================
This module acts as a THIN COORDINATOR - it only handles UI layout and routing. No business logic lives here!

Responsibilities:
- Define page route (using route constants from routes.py)
- Create UI layout structure (header, pipeline area, config panel, results area)
- Maintain UIState references to UI elements
- Provide wrapper functions that delegate to specialized modules

UI Layout Structure:
┌─────────────────────────────────────┐
│ Header (logo, navigation)           │ ← ui_components.header.build_header()
├─────────────────────────────────────┤
│ Pipeline Area                       │
│ - Pipeline Name Input & Actions     │
│ - Operator Library (left sidebar)   │ ← operator_library.render_operator_library()
│ - Operator Blocks (visual chain)    │ ← pipeline_view.render_pipeline()
├─────────────────────────────────────┤
│ Config Panel (dynamic)              │ ← config_panel.show_operator_config()
│ (only shown if operator selected)   │    (replaces itself on each selection)
│ - Operator parameters               │
├─────────────────────────────────────┤
│ Results Preview (bottom grid)       │ ← preview_coordinator
│ - Artwork thumbnails                │    .show_preview_for_operator()
└─────────────────────────────────────┘

User Flow Example:
1. User clicks operator from library → chooses "Semantic Search"
2. config_panel.show_operator_config() renders parameter inputs (query_text, top_k)
3. User types "paintings with horses" and clicks preview
4. preview_coordinator.show_preview_for_operator() uses OperatorFactory
5. operator_instance.execute() runs the search via operator_implementations.py
6. results_view.render_results_ui() renders thumbnail grid

All actual logic lives in search_pipeline package!
"""

# Third-party libraries
from nicegui import ui, app
from loguru import logger
import routes

# UI components
from ui_components.header import render_header
from ui_components.buttons import icon_button, run_button

# Search pipeline - state & helpers
from search_pipeline.state import PipelineState
from search_pipeline.operator_registry import OperatorNames

# Search pipeline - components
from search_pipeline.views import operator_library, results_view, pipeline_view

# Module-level storage: Safe because each tab gets unique ID from browser storage
# Memory persists during app runtime (acceptable tradeoff for state preservation)
_search_controllers = {}


class SearchPageUIState:
    """Container for search page UI element references."""
    def __init__(self):
        self.pipeline_area = None
        self.pipeline_name_input = None
        self.results_area = None
        self.config_panel = None  # Floating config panel (cleaned up automatically)


class SearchPageController:
    """
    Controller for the search page.
    Manages pipeline state, UI state, and coordinates all interactions.
    Eliminates the need for helper closures by encapsulating state and behavior.
    
    IMPORTANT: Each user gets their own controller instance via app.storage.user
    to prevent state leaking between users.
    """
    
    def __init__(self):
        self.ui_state = SearchPageUIState()
        self.pipeline_state = PipelineState()
        self.results_state = results_view.ResultsViewState()  # Per-user results cache
        
        # Initialize with default operators
        self.pipeline_state.add_operator(OperatorNames.METADATA_FILTER)
        self.pipeline_state.add_operator(OperatorNames.SEMANTIC_SEARCH)
        self.pipeline_state.add_operator(OperatorNames.SIMILARITY_SEARCH)
    
    def delete_operator(self, operator_id: str, op_name: str, tile):
        """Delete an operator from the pipeline."""
        self.pipeline_state.remove_operator(operator_id)
        tile.delete()
        ui.notify(f'Removed {op_name}')
        results_view.clear_results(self.ui_state.results_area)
        pipeline_view.render_pipeline(self)
    
    def move_operator_left(self, operator_id: str):
        """Move operator left and re-render."""
        if self.pipeline_state.move_left(operator_id):
            pipeline_view.render_pipeline(self)
    
    def move_operator_right(self, operator_id: str):
        """Move operator right and re-render."""
        if self.pipeline_state.move_right(operator_id):
            pipeline_view.render_pipeline(self)
    
    def on_operator_added(self):
        """Called when a new operator is added from the library."""
        results_view.clear_results(self.ui_state.results_area)
        pipeline_view.render_pipeline(self)
    
    def render_search(self, ui_module):
        """
        Renders the main search page, including the operator library and the pipeline area.
        """
        # Title & icon
        with ui_module.row().classes('items-center gap-2 mb-2'):
            ui_module.icon('search').classes('text-2xl text-amber-700')
            ui_module.label('Search Pipeline').classes('text-2xl font-bold')

        # Top bar: full width, left input, right buttons
        with ui_module.row().props('flat').classes('w-full flex items-center justify-between bg-white shadow-sm px-4 py-2 mb-4 rounded'):
            # Left: input field - store reference for later use
            self.ui_state.pipeline_name_input = ui_module.input(
                placeholder='Pipeline name', 
                value='Untitled Pipeline'
            ).props('borderless dense').classes('w-64')
            # Right: buttons
            with ui_module.row().classes('gap-2'):
                icon_button('folder_open', 'Load', lambda: self.load_pipeline())
                icon_button('save', 'Save', lambda: self.save_pipeline())
                run_button('Run', lambda: ui_module.notify('Run clicked'))
        
        # Layout: operator library + operator chain + results preview
        with ui_module.row().classes('w-full gap-4 flex-nowrap'):
            # Render operator library
            operator_library.render_operator_library(self.pipeline_state, self.on_operator_added)

            # Main content (right)
            with ui_module.column().classes('flex-1 min-w-0 p-4'):
                ui_module.label('OPERATOR CHAIN').classes('text-xl font-bold mb-2')
                self.ui_state.pipeline_area = ui_module.element('div').props('id=pipeline-area')
                pipeline_view.render_pipeline(self)
                
                # Results section
                ui_module.label('RESULTS').classes('text-xl font-bold mt-6 mb-2')
                self.ui_state.results_area = ui_module.element('div').props('id=results-area').classes('w-full')
                
                # Restore cached results if available
                cached_results, cached_operator_id = results_view.get_cached_results(self.results_state)
                if cached_results:
                    logger.info(f"Restoring cached results: {len(cached_results)} results")
                    # Find operator name from id
                    operator = self.pipeline_state.get_operator(cached_operator_id)
                    operator_name = operator['name'] if operator else 'Unknown'
                    results_view.render_results_ui(cached_results, cached_operator_id, operator_name, self.ui_state.results_area, self.results_state)


# Register page routes
@ui.page(routes.ROUTE_HOME)
@ui.page(routes.ROUTE_SEARCH)
def page():
    """Search pipeline page - main application page."""
    logger.info("Loading Search page")
    
    # Get or create unique tab ID from browser storage (persists across navigations)
    if 'tab_id' not in app.storage.browser:
        import uuid
        app.storage.browser['tab_id'] = str(uuid.uuid4())
    
    tab_id = app.storage.browser['tab_id']
    
    # Get or create controller for this tab
    if tab_id not in _search_controllers:
        logger.info(f"Creating new SearchPageController for tab {tab_id[:8]}")
        _search_controllers[tab_id] = SearchPageController()
    else:
        logger.info(f"Reusing SearchPageController for tab {tab_id[:8]}")
    
    controller = _search_controllers[tab_id]
    
    render_header()
    controller.render_search(ui)










