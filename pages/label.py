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
    render_algorithm_header,
    render_action_bar,
    render_ai_results_row,
    render_validated_row
)


class LabelPageUIState:
    """Container for label page UI element references."""
    def __init__(self):
        self.search_container = None
        self.definition_container = None
        self.boxes_area = None


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
        logger.info(f"State updated: selected_thesaurus = '{thesaurus}'")
        
        # Load thesaurus terms for autocomplete
        self._load_thesaurus_terms()
        
        ui.notify(f'Selected thesaurus: {thesaurus}')
        
        # Re-render UI
        self.update_search_bar()
        self.update_definition()
        self._update_boxes()
    
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
            logger.info(f"State updated: label_name = '{term}'")
            ui.notify(f'Selected label: {term}', type='positive')
            
            # Re-render UI
            self.update_search_bar()
            self.update_definition()
            self._update_boxes()
    
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
        
        # Re-render boxes
        self._update_boxes()
    
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
        
        # Re-render boxes
        self._update_boxes()
    
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
            self.update_search_bar()
            self.update_definition()
            
        except Exception as e:
            logger.error(f"Failed to create label: {str(e)}")
            ui.notify(f'Error creating label: {str(e)}', type='negative')
    
    def clear_label(self):
        """Clears the currently selected label."""
        logger.info(f"Label '{self.state.label_name}' manually cleared by user")
        
        self.state.clear_label()
        ui.notify('Label cleared')
        
        # Re-render UI
        self.update_search_bar()
        self.update_definition()
        self._update_boxes()
    
    # ========== Search Actions ==========
    
    async def execute_search(self):
        """Execute label validation search for open boxes only."""
        # Get open boxes
        open_ai_boxes = self.state.get_open_ai_box_keys()
        open_validated_boxes = self.state.get_open_validated_box_keys()
        
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
            
            # Re-render boxes to show loading state
            self._update_boxes()
            
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
            for box_key, box_results in results.items():
                self.state.results_per_box[box_key] = box_results
            
            self.state.is_searching = False
            
            logger.info("Search completed successfully")
            ui.notify('Validation complete')
            
            # Re-render boxes with results
            self._update_boxes()
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            self.state.is_searching = False
            self.state.search_error = str(e)
            ui.notify(f'Search failed: {str(e)}', type='negative')
            
            # Re-render boxes to show error state
            self._update_boxes()
    
    def _update_boxes(self):
        """Re-render all result boxes."""
        if not self.ui_state.boxes_area:
            return
        self.ui_state.boxes_area.clear()
        with self.ui_state.boxes_area:
            # AI Results row
            if self.state.selected_algorithms:
                render_ai_results_row(self)
            
            # Validated rows
            if VALIDATION_LEVEL_AI in self.state.selected_levels:
                render_validated_row(
                    self,
                    box_key=VALIDATION_LEVEL_AI,
                    row_label="Level: AI",
                    subtitle="Label was validated by AI",
                    color="purple-600"
                )
            if VALIDATION_LEVEL_HUMAN in self.state.selected_levels:
                render_validated_row(
                    self,
                    box_key=VALIDATION_LEVEL_HUMAN,
                    row_label="Level: Human",
                    subtitle="Label was validated by a human",
                    color="blue-600"
                )
            if VALIDATION_LEVEL_EXPERT in self.state.selected_levels:
                render_validated_row(
                    self,
                    box_key=VALIDATION_LEVEL_EXPERT,
                    row_label="Level: Expert",
                    subtitle="Label was validated by expert (art historian)",
                    color="amber-700"
                )
    
    # ========== Rendering Methods ==========
    
    def update_search_bar(self):
        """Render the search bar."""
        if not self.ui_state.search_container:
            return
        
        self.ui_state.search_container.clear()
        
        with self.ui_state.search_container:
            render_search_bar(self)
    
    def update_definition(self):
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
    
    # ========== Selection Management ==========
    
    def toggle_artwork_selection(self, box_key: str, artwork_id: str):
        """Toggle selection of an artwork."""
        self.state.toggle_artwork_selection(box_key, artwork_id)
        logger.info(f"Toggled selection for {artwork_id} in {box_key}")
        
        # Re-render boxes to update checkboxes and show/hide action bar
        self._update_boxes()
    
    def select_all_in_box(self, box_key: str):
        """Select all artworks in a box."""
        self.state.select_all_artworks(box_key)
        logger.info(f"Selected all artworks in {box_key}")
        self._update_boxes()
    
    def deselect_all_in_box(self, box_key: str):
        """Deselect all artworks in a box."""
        self.state.deselect_all_artworks(box_key)
        logger.info(f"Deselected all artworks in {box_key}")
        self._update_boxes()
    
    def promote_selected(self, from_box_key: str):
        """
        Promote selected artworks to the next validation level.
        
        Promotion flow:
        - Algorithm results (AI-*) → HUMAN
        - AI Results → HUMAN
        - HUMAN → EXPERT
        - EXPERT → cannot promote
        """
        selected_ids = self.state.get_selected_artworks(from_box_key)
        if not selected_ids:
            return
        
        logger.info(f"Promoting {len(selected_ids)} artworks from {from_box_key}")
        
        # Determine target level
        if from_box_key.startswith('AI'):
            to_box_key = VALIDATION_LEVEL_HUMAN
        elif from_box_key == 'HUMAN':
            to_box_key = VALIDATION_LEVEL_EXPERT
        else:
            logger.warning(f"Cannot promote from {from_box_key}")
            ui.notify('Cannot promote from EXPERT level', type='warning')
            return
        
        # Get source and target results
        source_results = self.state.get_box_results(from_box_key)
        target_results = self.state.get_box_results(to_box_key)
        
        # Find artworks to promote
        promoted_artworks = []
        remaining_artworks = []
        
        for artwork in source_results.results:
            artwork_id = artwork.get('id', artwork.get('inventory_number'))
            if artwork_id in selected_ids:
                promoted_artworks.append(artwork)
            else:
                remaining_artworks.append(artwork)
        
        # Update source box (remove promoted)
        source_results.results = remaining_artworks
        source_results.total_count = len(remaining_artworks)
        
        # Update target box (add promoted to the beginning)
        target_results.results = promoted_artworks + target_results.results
        target_results.total_count = len(target_results.results)
        
        # TODO: Backend call to update validation levels
        # self.label_service.update_validation_level(selected_ids, to_box_key)
        
        ui.notify(f'Promoted {len(selected_ids)} artworks to {to_box_key}', type='positive')
        self.deselect_all_in_box(from_box_key)
        self._update_boxes()
    
    def demote_selected(self, from_box_key: str):
        """
        Demote selected artworks to the previous validation level.
        
        Demotion flow:
        - EXPERT → HUMAN
        - HUMAN → AI Results
        - AI Results → cannot demote
        - Algorithm results (AI-*) → cannot demote
        """
        selected_ids = self.state.get_selected_artworks(from_box_key)
        if not selected_ids:
            return
        
        logger.info(f"Demoting {len(selected_ids)} artworks from {from_box_key}")
        
        # Determine target level
        if from_box_key == 'EXPERT':
            to_box_key = VALIDATION_LEVEL_HUMAN
        elif from_box_key == 'HUMAN':
            to_box_key = VALIDATION_LEVEL_AI
        else:
            logger.warning(f"Cannot demote from {from_box_key}")
            ui.notify('Cannot demote from AI level', type='warning')
            return
        
        # Get source and target results
        source_results = self.state.get_box_results(from_box_key)
        target_results = self.state.get_box_results(to_box_key)
        
        # Find artworks to demote
        demoted_artworks = []
        remaining_artworks = []
        
        for artwork in source_results.results:
            artwork_id = artwork.get('id', artwork.get('inventory_number'))
            if artwork_id in selected_ids:
                demoted_artworks.append(artwork)
            else:
                remaining_artworks.append(artwork)
        
        # Update source box (remove demoted)
        source_results.results = remaining_artworks
        source_results.total_count = len(remaining_artworks)
        
        # Update target box (add demoted to the beginning)
        target_results.results = demoted_artworks + target_results.results
        target_results.total_count = len(target_results.results)
        
        # TODO: Backend call to update validation levels
        # self.label_service.update_validation_level(selected_ids, to_box_key)
        
        ui.notify(f'Demoted {len(selected_ids)} artworks to {to_box_key}', type='positive')
        self.deselect_all_in_box(from_box_key)
        self._update_boxes()
    
    def delete_selected(self, box_key: str):
        """Delete labels for selected artworks."""
        selected_ids = self.state.get_selected_artworks(box_key)
        if not selected_ids:
            return
        
        logger.info(f"Deleting {len(selected_ids)} labels from {box_key}")
        
        # Get box results
        box_results = self.state.get_box_results(box_key)
        
        # Remove deleted artworks from results
        remaining_artworks = []
        deleted_count = 0
        
        for artwork in box_results.results:
            artwork_id = artwork.get('id', artwork.get('inventory_number'))
            if artwork_id not in selected_ids:
                remaining_artworks.append(artwork)
            else:
                deleted_count += 1
        
        # Update box results
        box_results.results = remaining_artworks
        box_results.total_count = len(remaining_artworks)
        
        # TODO: Backend call to delete labels
        # try:
        #     self.label_service.delete_labels(list(selected_ids), self.state.label_name)
        # except Exception as e:
        #     logger.error(f"Failed to delete labels: {e}")
        #     ui.notify(f'Failed to delete labels: {e}', type='negative')
        #     return
        
        ui.notify(f'Deleted {deleted_count} labels', type='positive')
        self.deselect_all_in_box(box_key)
        self._update_boxes()
    
    def hide_selected(self, box_key: str):
        """
        Hide selected artworks and replace with next results.
        
        If 10 results are shown and 3 are hidden, results 11-13 become visible.
        Hidden artworks are moved to the end of the results list and marked as hidden.
        """
        selected_ids = self.state.get_selected_artworks(box_key)
        if not selected_ids:
            return
        
        logger.info(f"Hiding {len(selected_ids)} artworks from {box_key}")
        
        # Get box results
        box_results = self.state.get_box_results(box_key)
        
        # Separate visible and hidden artworks
        visible_artworks = []
        hidden_artworks_list = []
        
        for artwork in box_results.results:
            artwork_id = artwork.get('id', artwork.get('inventory_number'))
            if artwork_id in selected_ids:
                # Mark as hidden and move to end
                artwork['_hidden'] = True
                hidden_artworks_list.append(artwork)
                # Add to hidden tracking
                if box_key not in self.state.hidden_artworks:
                    self.state.hidden_artworks[box_key] = set()
                self.state.hidden_artworks[box_key].add(artwork_id)
            else:
                visible_artworks.append(artwork)
        
        # Reorder: visible first, then hidden (so next ones become visible)
        box_results.results = visible_artworks + hidden_artworks_list
        
        # Note: We keep the same total_count but only show non-hidden in views
        # The render functions will need to filter out _hidden artworks
        
        ui.notify(f'Hidden {len(selected_ids)} artworks', type='positive')
        self.deselect_all_in_box(box_key)
        self._update_boxes()
    
    def close_algorithm(self, algo_name: str):
        """Close (remove) an algorithm from the selected list."""
        if algo_name in self.state.selected_algorithms:
            self.state.selected_algorithms.remove(algo_name)
            logger.info(f"Closed algorithm: {algo_name}")
            
            # Re-render search bar to update checkboxes and boxes
            self.update_search_bar()
            self._update_boxes()
    
    def toggle_box(self, box_key: str):
        """Toggle a box open/closed and sync with algorithms."""
        self.state.toggle_box(box_key)
        
        is_open = self.state.is_box_open(box_key)
        logger.info(f"Box '{box_key}' {'opened' if is_open else 'closed'}")
        
        # Re-render search bar to update checkboxes and boxes
        self.update_search_bar()
        self._update_boxes()
    
    def toggle_view(self, view_mode: str):
        """Toggle between grid and list view."""
        self.state.view_mode = view_mode
        logger.info(f"View mode changed to: {view_mode}")
        
        # Re-render boxes with new view
        self._update_boxes()


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
            controller.update_search_bar()
            
            # Definition (appears when label is selected)
            controller.ui_state.definition_container = ui.element('div').classes('w-full')
            controller.update_definition()
        
        # Validation level boxes section
        controller.ui_state.boxes_area = ui.column().classes('w-full')
        controller._update_boxes()



