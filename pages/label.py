"""
Label validation page for the Fabritius-NG application.

ARCHITECTURE: Controller Pattern with label_tool package
=========================================================
This module acts as a THIN COORDINATOR following the same pattern as search.py.

Responsibilities:
- Define page route
- Create UI layout structure
- Maintain UIState references to UI elements
- Delegate to label_tool package for business logic
- Coordinate between views and state
"""

from nicegui import ui, app
from ui_components.header import render_header
from loguru import logger
import routes

from label_tool import (
    LabelState,
    get_thesaurus_names,
    get_algorithm_names,
    get_enabled_levels,
    LabelService,
    ValidationEngine,
    VALIDATION_LEVEL_AI,
    VALIDATION_LEVEL_HUMAN,
    VALIDATION_LEVEL_EXPERT
)
from label_tool.thesaurus_terms import get_thesaurus_terms
from label_tool.views import (
    render_search_bar, 
    render_level_column,
    render_result_grid_view,
    render_result_list_view,
    render_view_toggle,
    render_column_header,
    render_algorithm_header
)


class LabelPageUIState:
    """Container for label page UI element references."""
    def __init__(self):
        self.search_container = None
        self.definition_container = None
        self.columns_area = None


class LabelPageController:
    """
    Controller for the label validation page.
    Manages label state, UI state, and coordinates all interactions.
    
    IMPORTANT: Each user gets their own controller instance via app.storage.client
    to prevent state leaking between users.
    """
    
    def __init__(self):
        self.ui_state = LabelPageUIState()
        self.state = LabelState()
        self.validation_engine = ValidationEngine()
        
        # Load initial thesaurus terms
        self._load_thesaurus_terms()
        
        logger.info("LabelPageController initialized")
    
    # ========== Thesaurus Actions ==========
    
    def select_thesaurus(self, thesaurus: str):
        """Handle thesaurus selection."""
        logger.info(f"Thesaurus changed to: {thesaurus}")
        
        # Clear current label when switching thesaurus
        if self.state.has_label():
            logger.info(f"Clearing current label '{self.state.label_name}' due to thesaurus change")
            self.state.clear_label()
        
        self.state.selected_thesaurus = thesaurus
        
        # Load thesaurus terms for autocomplete
        self._load_thesaurus_terms()
        
        ui.notify(f'Selected thesaurus: {thesaurus}')
        
        # Re-render UI
        self.render_search_bar()
        self.render_definition()
        self.render_columns()
    
    def _load_thesaurus_terms(self):
        """Load terms from selected thesaurus for autocomplete."""
        if self.state.selected_thesaurus:
            # Convert thesaurus name to ID (lowercase)
            thesaurus_id = self.state.selected_thesaurus.lower()
            self.state.cached_thesaurus_terms = get_thesaurus_terms(thesaurus_id)
            logger.info(f"Loaded {len(self.state.cached_thesaurus_terms)} terms from {self.state.selected_thesaurus}")
        else:
            self.state.cached_thesaurus_terms = []
    
    def select_term(self, term: str):
        """Handle term selection from autocomplete."""
        if term:
            logger.info(f"Term selected from autocomplete: {term}")
            self.state.label_name = term
            ui.notify(f'Selected label: {term}', type='positive')
            
            # Re-render UI
            self.render_search_bar()
            self.render_definition()
            self.render_columns()
    
    # ========== Algorithm Actions ==========
    
    def toggle_algorithm(self, algorithm: str, is_selected: bool):
        """Toggle algorithm selection."""
        if is_selected:
            # Check max 2 algorithms
            if len(self.state.selected_algorithms) >= 2:
                ui.notify('Maximum 2 algorithms can be selected', type='warning')
                return
            if algorithm not in self.state.selected_algorithms:
                self.state.selected_algorithms.append(algorithm)
                logger.info(f"Algorithm '{algorithm}' selected")
                # Open the corresponding box
                box_key = f"AI-{algorithm}"
                if box_key in self.state.closed_boxes:
                    self.state.closed_boxes.remove(box_key)
        else:
            if algorithm in self.state.selected_algorithms:
                self.state.selected_algorithms.remove(algorithm)
                logger.info(f"Algorithm '{algorithm}' deselected")
                # Close the corresponding box
                box_key = f"AI-{algorithm}"
                if box_key not in self.state.closed_boxes:
                    self.state.closed_boxes.append(box_key)
        
        logger.info(f"Currently selected algorithms: {self.state.selected_algorithms}")
        ui.notify(f'Selected algorithms: {", ".join(self.state.selected_algorithms) if self.state.selected_algorithms else "None"}')
        
        # Re-render columns
        self.render_columns()
    
    def toggle_level(self, level: str, is_checked: bool):
        """Toggle a validation level on/off."""
        if is_checked:
            if level not in self.state.selected_levels:
                self.state.selected_levels.append(level)
                logger.info(f"Validation level '{level}' selected")
        else:
            if level in self.state.selected_levels:
                self.state.selected_levels.remove(level)
                logger.info(f"Validation level '{level}' deselected")
        
        logger.info(f"Currently selected levels: {self.state.selected_levels}")
        ui.notify(f'Selected levels: {", ".join(self.state.selected_levels) if self.state.selected_levels else "None"}')
        
        # Re-render columns
        self.render_columns()
    
    # ========== Label Actions ==========
    
    def open_new_label_dialog(self):
        """Opens a dialog to create a new label."""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Create New Label').classes('text-xl font-bold mb-4')
            
            label_name = ui.input('Label name').props('outlined').classes('w-full mb-2')
            label_definition = ui.textarea('Definition').props('outlined').classes('w-full mb-2')
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('outline')
                ui.button('Create', on_click=lambda: self.create_label(
                    label_name.value, label_definition.value, dialog
                ))
        
        dialog.open()
    
    async def create_label(self, name: str, definition: str, dialog):
        """Creates a new label in the selected thesaurus."""
        if not name:
            logger.warning("Label creation failed: name is required")
            ui.notify('Label name is required', type='warning')
            return
        
        logger.info(f"Creating new label: '{name}' in {self.state.selected_thesaurus}")
        
        try:
            # Get thesaurus service
            label_service = LabelService(self.state.selected_thesaurus.lower())
            
            # Create label
            result = await label_service.create_label(name, definition or '')
            
            # Update state
            self.state.label_name = result['name']
            self.state.label_definition = result.get('definition', '')
            self.state.label_id = result.get('id')
            
            logger.info(f"Label '{name}' created and set as current label")
            ui.notify(f'Created label: {name}')
            
            dialog.close()
            
            # Re-render UI
            self.render_search_bar()
            self.render_definition()
            
        except Exception as e:
            logger.error(f"Failed to create label: {str(e)}")
            ui.notify(f'Error creating label: {str(e)}', type='negative')
    
    def clear_label(self):
        """Clears the currently selected label."""
        logger.info(f"Label '{self.state.label_name}' manually cleared by user")
        
        self.state.clear_label()
        ui.notify('Label cleared')
        
        # Re-render UI
        self.render_search_bar()
        self.render_definition()
        self.render_columns()
    
    # ========== Search Actions ==========
    
    async def execute_search(self):
        """Execute label validation search for open boxes only."""
        # Get open boxes
        open_ai_boxes = self.state.get_open_ai_column_keys()
        open_validated_boxes = self.state.get_open_validated_column_keys()
        
        if not open_ai_boxes and not open_validated_boxes:
            logger.warning("Search attempted with all boxes closed")
            ui.notify('Please open at least one result box', type='warning')
            return
        
        logger.info(
            f"Executing search for label '{self.state.label_name}' | "
            f"Open AI boxes: {open_ai_boxes} | Open validated boxes: {open_validated_boxes}"
        )
        
        try:
            # Clear all previous results
            self.state.clear_all_results()
            
            self.state.is_searching = True
            self.state.search_error = None
            
            # Re-render columns to show loading state
            self.render_columns()
            
            # Notify which queries are being executed
            if self.state.selected_algorithms:
                ui.notify(f'Running AI algorithms: {", ".join(self.state.selected_algorithms)}')
            
            if self.state.selected_levels:
                level_display = {
                    'AI': 'AI',
                    'HUMAN': 'Human', 
                    'EXPERT': 'Expert'
                }
                level_names = [level_display.get(l, l) for l in self.state.selected_levels]
                ui.notify(f'Fetching validated data: {", ".join(level_names)}')
            
            # Run validation only for selected algorithms and levels
            results = await self.validation_engine.validate_label(
                label_name=self.state.label_name,
                label_definition=self.state.label_definition or '',
                algorithms=self.state.selected_algorithms,  # Use selected algorithms, not open boxes
                state=self.state,
                validated_boxes=self.state.selected_levels  # Use selected levels, not open boxes
            )
            
            # Update state with results
            for column_key, column_results in results.items():
                self.state.results_per_column[column_key] = column_results
            
            self.state.is_searching = False
            
            logger.info("Search completed successfully")
            ui.notify('Validation complete')
            
            # Re-render columns with results
            self.render_columns()
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            self.state.is_searching = False
            self.state.search_error = str(e)
            ui.notify(f'Search failed: {str(e)}', type='negative')
            
            # Re-render columns to show error state
            self.render_columns()
    
    # ========== Rendering Methods ==========
    
    def render_search_bar(self):
        """Render the search bar."""
        if not self.ui_state.search_container:
            return
        
        self.ui_state.search_container.clear()
        
        with self.ui_state.search_container:
            render_search_bar(
                selected_thesaurus=self.state.selected_thesaurus,
                selected_algorithms=self.state.selected_algorithms,
                selected_levels=self.state.selected_levels,
                label_name=self.state.label_name,
                thesaurus_terms=self.state.cached_thesaurus_terms,
                on_thesaurus_change=self.select_thesaurus,
                on_new_label_click=self.open_new_label_dialog,
                on_algorithm_toggle=self.toggle_algorithm,
                on_level_toggle=self.toggle_level,
                on_search_click=self.execute_search,
                on_clear_label=self.clear_label,
                on_term_select=self.select_term
            )
    
    def render_definition(self):
        """Render the definition text below the search bar in italics."""
        if not self.ui_state.definition_container:
            return
        
        self.ui_state.definition_container.clear()
        
        # Show definition if there's a current label with a definition
        if self.state.has_label() and self.state.label_definition:
            with self.ui_state.definition_container:
                # Truncate to 100 characters and add ellipsis if needed
                truncated_def = self.state.label_definition[:100]
                if len(self.state.label_definition) > 100:
                    truncated_def += '...'
                ui.label(truncated_def).classes('text-sm text-gray-600 italic mt-1')
    
    def render_columns(self):
        """Render all result boxes in layered structure."""
        if not self.ui_state.columns_area:
            return
        
        self.ui_state.columns_area.clear()
        
        with self.ui_state.columns_area:
            # Layer 1: AI Results (collapsible row with colored header)
            if self.state.selected_algorithms:
                self.render_ai_results_row()
            
            # Layer 2-4: Validated rows (only show selected levels)
            if VALIDATION_LEVEL_AI in self.state.selected_levels:
                self.render_validated_row(VALIDATION_LEVEL_AI, "Level: AI", "Label was validated by AI", "purple-600")
            if VALIDATION_LEVEL_HUMAN in self.state.selected_levels:
                self.render_validated_row(VALIDATION_LEVEL_HUMAN, "Level: Human", "Label was validated by a human", "blue-600")
            if VALIDATION_LEVEL_EXPERT in self.state.selected_levels:
                self.render_validated_row(VALIDATION_LEVEL_EXPERT, "Level: Expert", "Label was validated by expert (art historian)", "amber-700")
    
    def render_ai_results_row(self):
        """Render AI Results as a collapsible row like validated rows."""
        box_key = "AI_RESULTS"
        is_collapsed = not self.state.is_box_open(box_key)
        
        # Calculate total results across all algorithms
        total_results = 0
        for algo_name in self.state.selected_algorithms:
            algo_box_key = f"AI-{algo_name}"
            column_results = self.state.get_column_results(algo_box_key)
            if column_results:
                total_results += column_results.total_count
        
        # Create a dummy ColumnResults for the header
        from label_tool.state import ColumnResults
        ai_results = ColumnResults(column_key=box_key, column_label="AI Results")
        ai_results.total_count = total_results
        
        with ui.element('div').classes('w-full mb-4'):
            # Main header with collapse
            with ui.column().classes('w-full bg-white rounded-lg shadow-md overflow-hidden'):
                # AI Results header (gray-600 color)
                result_count = total_results
                render_column_header(
                    title="AI Results",
                    count=result_count,
                    is_collapsed=is_collapsed,
                    on_toggle_collapse=lambda: self.toggle_box(box_key),
                    color="gray-600",
                    subtitle="Labels suggested by AI to be validated"
                )
                
                # Collapsible content area
                content_height = '0px' if is_collapsed else 'none'
                overflow_class = 'overflow-hidden' if is_collapsed else ''
                with ui.column().classes(f'{overflow_class} transition-all duration-500 ease-in-out').style(f'max-height: {content_height};' if is_collapsed else ''):
                    with ui.column().classes('p-4'):
                        # Algorithm columns in a row
                        with ui.row().classes('w-full gap-4'):
                            for i, algo_name in enumerate(self.state.selected_algorithms):
                                algo_box_key = f"AI-{algo_name}"
                                algo_color = "rose-600" if i == 0 else "emerald-600"
                                
                                # Render algorithm box with close button
                                column_results = self.state.get_column_results(algo_box_key)
                                self.render_algorithm_box(
                                    box_key=algo_box_key,
                                    label=f"{algo_name} Embeddings",
                                    color=algo_color,
                                    results=column_results,
                                    on_close=lambda a=algo_name: self.close_algorithm(a)
                                )
    
    def render_validated_row(self, box_key: str, row_label: str, subtitle: str, color: str):
        """Render a validated data row."""
        # Always render result box (header stays visible when collapsed)
        column_results = self.state.get_column_results(box_key)
        with ui.element('div').classes('w-full mb-4'):
            self.render_result_box(
                box_key=box_key,
                label=row_label,
                color=color,
                results=column_results,
                show_label=False,
                subtitle=subtitle
            )
    
    def render_result_box(self, box_key: str, label: str, color: str, results, show_label: bool = False, subtitle: str = None):
        """Render an open result box with column header and results."""
        is_ai_column = box_key.startswith("AI-") and box_key not in [VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT]
        is_validated_column = box_key in [VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT]
        
        # Check if column is collapsed
        is_collapsed = not self.state.is_box_open(box_key)
        
        # Determine grid columns and max items based on row type
        grid_cols = None
        max_items = None
        
        if is_ai_column:
            # AI Results row: varies by algorithm count
            num_algorithms = len(self.state.selected_algorithms) if self.state.selected_algorithms else 1
            if num_algorithms == 1:
                # 1 algorithm: 5 columns x 2 rows = 10 items
                grid_cols = 5
                max_items = 10
            else:
                # 2 algorithms: 3 columns x 2 rows = 6 items per algorithm
                grid_cols = 3
                max_items = 6
        elif is_validated_column:
            # Validated rows (AI/HUMAN/EXPERT): always 5 columns x 2 rows = 10 items
            grid_cols = 5
            max_items = 10
        
        # Determine header color based on column type
        if is_ai_column:
            # For AI algorithm columns, use different colors for each algorithm
            if self.state.selected_algorithms:
                algo_index = None
                for i, algo in enumerate(self.state.selected_algorithms):
                    if box_key == f"AI-{algo}":
                        algo_index = i
                        break
                
                if algo_index == 0:
                    header_color = "rose-600"     # Rose for first algorithm
                elif algo_index == 1:
                    header_color = "emerald-600"  # Emerald for second algorithm
                else:
                    header_color = "purple-700"   # Fallback purple
            else:
                header_color = "purple-700"       # Default purple if no algorithms
        elif box_key == VALIDATION_LEVEL_AI:
            header_color = "purple-600"  # Purple for AI validated
        elif box_key == VALIDATION_LEVEL_HUMAN:
            header_color = "blue-600"    # Blue for Human
        elif box_key == VALIDATION_LEVEL_EXPERT:
            header_color = "amber-700"   # Amber for Expert (Fabritius branding)
        elif box_key == "":
            header_color = "gray-400"    # Light gray for empty AI Results (no algorithm selected)
        else:
            header_color = "amber-800"   # Default Fabritius brown
        
        with ui.column().classes('flex-1 bg-white rounded-lg shadow-md overflow-hidden'):
            # Column header with title, count badge, and collapse button
            result_count = results.total_count if results else 0
            render_column_header(
                title=label,
                count=result_count,
                is_collapsed=is_collapsed,
                on_toggle_collapse=lambda: self.toggle_box(box_key),
                color=header_color,
                subtitle=subtitle  # Pass subtitle to header
            )
            
            # Content area with smooth collapse animation
            # Use a large max-height for smooth transition (2000px should accommodate most content)
            content_height = '0px' if is_collapsed else 'none'
            overflow_class = 'overflow-hidden' if is_collapsed else ''
            with ui.column().classes(f'{overflow_class} transition-all duration-500 ease-in-out').style(f'max-height: {content_height};' if is_collapsed else ''):
                with ui.column().classes('p-4'):
                    # View toggle in top right
                    with ui.row().classes('w-full items-center justify-end mb-4'):
                        render_view_toggle(
                            current_view=self.state.view_mode,
                            on_toggle_view=self.toggle_view
                        )
                    
                    # Results area
                    if results and results.results:
                        # Limit results based on max_items
                        display_results = results.results[:max_items] if max_items else results.results
                        
                        logger.info(f"Rendering {len(display_results)} results for {box_key}, view mode: {self.state.view_mode}")
                        
                        if self.state.view_mode == 'grid':
                            render_result_grid_view(display_results, is_ai_column=is_ai_column, grid_cols=grid_cols)
                        else:
                            render_result_list_view(display_results, is_ai_column=is_ai_column)
                    else:
                        logger.warning(f"No results to display for {box_key}: results={results}, has results={results.results if results else 'None'}")
                        ui.label('No results').classes('text-gray-500 italic')
    
    def render_algorithm_box(self, box_key: str, label: str, color: str, results, on_close):
        """Render an algorithm box with close button instead of collapse."""
        is_ai_column = True
        
        # Determine grid columns and max items for AI columns
        num_algorithms = len(self.state.selected_algorithms) if self.state.selected_algorithms else 1
        if num_algorithms == 1:
            grid_cols = 5
            max_items = 10
        else:
            grid_cols = 3
            max_items = 6
        
        # Use flex-1 for single algorithm (takes full width), flex-1 for 2 algorithms (50% each)
        if num_algorithms == 1:
            width_class = 'flex-1'
        else:
            width_class = 'flex-1'  # Each takes 50% of available space with gap-4
        
        with ui.column().classes(f'{width_class} bg-white rounded-lg shadow-md overflow-hidden'):
            # Algorithm header with close button (X)
            result_count = results.total_count if results else 0
            render_algorithm_header(
                title=label,
                count=result_count,
                on_close=on_close,
                color=color
            )
            
            # Content always visible (no collapse for algorithms)
            with ui.column().classes('p-4'):
                # View toggle in top right
                with ui.row().classes('w-full items-center justify-end mb-4'):
                    render_view_toggle(
                        current_view=self.state.view_mode,
                        on_toggle_view=self.toggle_view
                    )
                
                # Results area
                if results and results.results:
                    # Limit results based on max_items
                    display_results = results.results[:max_items] if max_items else results.results
                    
                    logger.info(f"Rendering {len(display_results)} algo results for {box_key}, view mode: {self.state.view_mode}")
                    
                    if self.state.view_mode == 'grid':
                        render_result_grid_view(display_results, is_ai_column=is_ai_column, grid_cols=grid_cols)
                    else:
                        render_result_list_view(display_results, is_ai_column=is_ai_column)
                else:
                    logger.warning(f"No algo results for {box_key}")
                    ui.label('No results').classes('text-gray-500 italic')
    
    def close_algorithm(self, algo_name: str):
        """Close (remove) an algorithm from the selected list."""
        if algo_name in self.state.selected_algorithms:
            self.state.selected_algorithms.remove(algo_name)
            logger.info(f"Closed algorithm: {algo_name}")
            
            # Re-render search bar to update checkboxes and columns
            self.render_search_bar()
            self.render_columns()
    
    def toggle_box(self, box_key: str):
        """Toggle a box open/closed and sync with algorithms."""
        self.state.toggle_box(box_key)
        
        is_open = self.state.is_box_open(box_key)
        logger.info(f"Box '{box_key}' {'opened' if is_open else 'closed'}")
        
        # Re-render search bar to update checkboxes and columns
        self.render_search_bar()
        self.render_columns()
    
    def toggle_view(self, view_mode: str):
        """Toggle between grid and list view."""
        self.state.view_mode = view_mode
        logger.info(f"View mode changed to: {view_mode}")
        
        # Re-render columns with new view
        self.render_columns()


# ========== Page Definition ==========

@ui.page(routes.ROUTE_LABEL)
def label_page():
    """Label validation page."""
    logger.info("Label validation page loaded")
    
    # Get or create controller for this user session
    if 'label_controller' not in app.storage.client:
        app.storage.client['label_controller'] = LabelPageController()
    
    controller = app.storage.client['label_controller']
    
    # Header
    render_header()
    
    # Main container
    with ui.column().classes('w-full max-w-7xl mx-auto p-4 gap-4'):
        # Search bar section
        with ui.card().classes('w-full p-4'):
            controller.ui_state.search_container = ui.column().classes('w-full gap-4')
            controller.render_search_bar()
            
            # Definition (appears when label is selected)
            controller.ui_state.definition_container = ui.element('div').classes('w-full')
            controller.render_definition()
        
        # Validation level columns section
        controller.ui_state.columns_area = ui.column().classes('w-full')
        controller.render_columns()
