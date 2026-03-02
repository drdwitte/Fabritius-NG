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

# Third-party libraries
from nicegui import ui, app
from ui_components.header import render_header
from loguru import logger
import routes

from label_tool import LabelState, LabelService, ValidationEngine
from label_tool import VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT

from label_tool.thesaurus_terms import get_thesaurus_terms
from label_tool.views import render_search_bar, render_ai_results_row, render_validated_row

# Module-level storage: Safe because each tab gets unique ID from browser storage
# Memory persists during app runtime (acceptable tradeoff for state preservation)
_label_controllers = {}

class LabelPageUIState:
    """Container for label page UI element references."""
    def __init__(self):
        
        self.search_container = None # Top section: thesaurus selector, label search bar, and algorithm checkboxes
        self.definition_container = None # Middle section: label definition display (shown when ' new label' is clicked)
        self.boxes_area = None # Bottom section: validation level boxes (AI, Human, Expert) with result cards

class LabelPageController:
    """
    Controller for the label validation page.
    Manages label state, UI state, and coordinates all interactions.
    
    IMPORTANT: Each user gets their own controller instance via app.storage.client
    to prevent state leaking between users.
    """
    
    def __init__(self):
        
        self.ui_state = LabelPageUIState() #manages UI elements
        self.state = LabelState() # Execution logic state: label data, selected algorithms, validation result
        self.validation_engine = ValidationEngine() #engine to run validation across three levels of validation
        
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
        self.update_boxes()
    
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
            
            # Check if tag already exists in database
            from backend.supabase_client import SupabaseClient
            db = SupabaseClient()
            existing_tag = db.get_tag_by_label(term)
            
            if existing_tag:
                self.state.tag_id = existing_tag['id']
                self.state.tag_source = existing_tag.get('source', 'UNKNOWN')
                logger.info(f"Label '{term}' exists in database: tag_id={self.state.tag_id}, source={self.state.tag_source}")
                ui.notify(f'Selected label: {term} (exists as {self.state.tag_source})', type='positive')
            else:
                self.state.tag_id = None
                self.state.tag_source = None
                logger.info(f"Label '{term}' does not exist in database yet (will be created as CUSTOM)")
                ui.notify(f'Selected label: {term} (new label)', type='positive')
            
            # Re-render UI
            self.update_search_bar()
            self.update_definition()
            self.update_boxes()
    
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
        self.update_boxes()
    
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
        self.update_boxes()
    
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
            
            # Check if tag exists in database and update state
            from backend.supabase_client import SupabaseClient
            db = SupabaseClient()
            existing_tag = db.get_tag_by_label(result['name'])
            if existing_tag:
                self.state.tag_id = existing_tag['id']
                self.state.tag_source = existing_tag.get('source', 'CUSTOM')
                logger.info(f"Tag already exists: tag_id={self.state.tag_id}, source={self.state.tag_source}")
            else:
                self.state.tag_id = None
                self.state.tag_source = None
                logger.info(f"Tag does not exist yet in database")
            
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
        self.update_boxes()
    
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
            self.update_boxes()
            
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
            self.update_boxes()
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            self.state.is_searching = False
            self.state.search_error = str(e)
            ui.notify(f'Search failed: {str(e)}', type='negative')
            
            # Re-render boxes to show error state
            self.update_boxes()
    
    def update_boxes(self):
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
        self.update_boxes()
    
    def select_all_in_box(self, box_key: str):
        """Select all artworks in a box."""
        self.state.select_all_artworks(box_key)
        logger.info(f"Selected all artworks in {box_key}")
        self.update_boxes()
    
    def deselect_all_in_box(self, box_key: str):
        """Deselect all artworks in a box."""
        self.state.deselect_all_artworks(box_key)
        logger.info(f"Deselected all artworks in {box_key}")
        self.update_boxes()
    
    def promote_selected(self, from_box_key: str):
        """
        Promote selected artworks to the next validation level.
        
        Promotion flow:
        - Algorithm results (AI-Text, AI-Image) → Level: AI
        - Level: AI → Level: HUMAN
        - Level: HUMAN → Level: EXPERT
        - Level: EXPERT → cannot promote
        """
        selected_ids = self.state.get_selected_artworks(from_box_key)
        if not selected_ids:
            return
        
        logger.info(f"Promoting {len(selected_ids)} artworks from {from_box_key}")
        
        # Determine target level
        if from_box_key.startswith('AI-'):  # Algorithm boxes (AI-Text, AI-Image)
            to_box_key = VALIDATION_LEVEL_AI  # Go to Level: AI
        elif from_box_key == VALIDATION_LEVEL_AI:  # Level: AI
            to_box_key = VALIDATION_LEVEL_HUMAN  # Go to Level: HUMAN
        elif from_box_key == VALIDATION_LEVEL_HUMAN:  # Level: HUMAN
            to_box_key = VALIDATION_LEVEL_EXPERT  # Go to Level: EXPERT
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
        
        # Filter out duplicates: check if artwork already exists in target box
        existing_ids_in_target = {a.get('id', a.get('inventory_number')) for a in target_results.results}
        new_artworks = [a for a in promoted_artworks if a.get('id', a.get('inventory_number')) not in existing_ids_in_target]
        
        if len(new_artworks) < len(promoted_artworks):
            skipped = len(promoted_artworks) - len(new_artworks)
            logger.info(f"Skipped {skipped} duplicate(s) already in target box '{to_box_key}'")
        
        # Update target box (add new promoted to the beginning - prepend)
        target_results.results = new_artworks + target_results.results
        target_results.total_count = len(target_results.results)
        
        # Debug logging
        promoted_ids = [a.get('id', a.get('inventory_number')) for a in new_artworks]
        logger.info(f"Promoted artwork IDs (in order): {promoted_ids}")
        
        # Show full list with titles
        full_list = []
        for idx, artwork in enumerate(target_results.results[:10]):  # First 10
            artwork_id = artwork.get('id', artwork.get('inventory_number'))
            title = artwork.get('title', artwork.get('name', 'No title'))[:30]  # First 30 chars
            full_list.append(f"{idx}: {artwork_id} - {title}")
        
        logger.info(f"Target box '{to_box_key}' after promotion (first 10):")
        for item in full_list:
            logger.info(f"  {item}")
        
        # Backend call to update validation levels in database (only for new artworks)
        success_count, failed_count, protected_count = self._update_provenance_in_db(
            new_artworks,  # Only process artworks that aren't duplicates
            from_box_key, 
            to_box_key,
            is_promotion=True
        )
        
        # Calculate duplicates that were skipped
        duplicate_count = len(promoted_artworks) - len(new_artworks)
        
        if duplicate_count > 0 and failed_count > 0:
            ui.notify(f'Promoted {success_count}, skipped {duplicate_count} duplicates, failed {failed_count}, protected {protected_count}', type='warning')
        elif duplicate_count > 0:
            ui.notify(f'Promoted {success_count} artworks (skipped {duplicate_count} duplicates)', type='info')
        elif failed_count > 0:
            ui.notify(f'Promoted {success_count}, failed {failed_count}, protected {protected_count}', type='warning')
        elif protected_count > 0:
            ui.notify(f'Promoted {success_count} artworks (skipped {protected_count} FABRITIUS tags)', type='info')
        else:
            ui.notify(f'Promoted {success_count} artworks to {to_box_key}', type='positive')
        
        self.state.deselect_all_artworks(from_box_key)
        
        # Force complete UI refresh to ensure correct order
        ui.timer(0.1, lambda: self.update_boxes(), once=True)
    
    def demote_selected(self, from_box_key: str):
        """
        Demote selected artworks to the previous validation level.
        
        Demotion flow:
        - Level: EXPERT → Level: HUMAN
        - Level: HUMAN → Level: AI
        - Level: AI → cannot demote (cannot go back to algorithm boxes)
        - Algorithm results (AI-Text, AI-Image) → cannot demote
        """
        selected_ids = self.state.get_selected_artworks(from_box_key)
        if not selected_ids:
            return
        
        logger.info(f"Demoting {len(selected_ids)} artworks from {from_box_key}")
        
        # Determine target level
        if from_box_key == VALIDATION_LEVEL_EXPERT:  # Level: EXPERT
            to_box_key = VALIDATION_LEVEL_HUMAN  # Go to Level: HUMAN
        elif from_box_key == VALIDATION_LEVEL_HUMAN:  # Level: HUMAN
            to_box_key = VALIDATION_LEVEL_AI  # Go to Level: AI
        else:
            logger.warning(f"Cannot demote from {from_box_key}")
            ui.notify('Cannot demote from AI level or algorithm boxes', type='warning')
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
        
        # Filter out duplicates: check if artwork already exists in target box
        existing_ids_in_target = {a.get('id', a.get('inventory_number')) for a in target_results.results}
        new_artworks = [a for a in demoted_artworks if a.get('id', a.get('inventory_number')) not in existing_ids_in_target]
        
        if len(new_artworks) < len(demoted_artworks):
            skipped = len(demoted_artworks) - len(new_artworks)
            logger.info(f"Skipped {skipped} duplicate(s) already in target box '{to_box_key}'")
        
        # Update target box (add new demoted to the beginning)
        target_results.results = new_artworks + target_results.results
        target_results.total_count = len(target_results.results)
        
        # Backend call to update validation levels in database (only for new artworks)
        success_count, failed_count, protected_count = self._update_provenance_in_db(
            new_artworks,  # Only process artworks that aren't duplicates
            from_box_key,
            to_box_key,
            is_promotion=False
        )
        
        # Calculate duplicates that were skipped
        duplicate_count = len(demoted_artworks) - len(new_artworks)
        
        if duplicate_count > 0 and failed_count > 0:
            ui.notify(f'Demoted {success_count}, skipped {duplicate_count} duplicates, failed {failed_count}, protected {protected_count}', type='warning')
        elif duplicate_count > 0:
            ui.notify(f'Demoted {success_count} artworks (skipped {duplicate_count} duplicates)', type='info')
        elif failed_count > 0:
            ui.notify(f'Demoted {success_count}, failed {failed_count}, protected {protected_count}', type='warning')
        elif protected_count > 0:
            ui.notify(f'Demoted {success_count} artworks (skipped {protected_count} FABRITIUS tags)', type='info')
        else:
            ui.notify(f'Demoted {success_count} artworks to {to_box_key}', type='positive')
        
        self.state.deselect_all_artworks(from_box_key)
        self.update_boxes()
    
    def _update_provenance_in_db(
        self, 
        artworks: list, 
        from_box_key: str, 
        to_box_key: str,
        is_promotion: bool
    ) -> tuple:
        """
        Update provenance in database for promoted/demoted artworks.
        
        Args:
            artworks: List of artwork dicts to update
            from_box_key: Source validation level
            to_box_key: Target validation level
            is_promotion: True if promoting, False if demoting
            
        Returns:
            Tuple of (success_count, failed_count, protected_count)
        """
        from backend.supabase_client import SupabaseClient
        
        # Map validation levels to provenance values
        provenance_map = {
            VALIDATION_LEVEL_AI: "AI",
            VALIDATION_LEVEL_HUMAN: "HUMAN",
            VALIDATION_LEVEL_EXPERT: "EXPERT"
        }
        
        db = SupabaseClient()
        success_count = 0
        failed_count = 0
        protected_count = 0
        
        for artwork in artworks:
            inventory_number = artwork.get('id') or artwork.get('inventory_number')
            tag_id = artwork.get('tag_id')
            current_provenance = artwork.get('provenance')
            
            # Skip if missing inventory number
            if not inventory_number:
                logger.warning(f"Missing inventory_number for artwork: {artwork}")
                failed_count += 1
                continue
            
            # Handle AI algorithm results (no tag_id yet, need to create)
            if from_box_key.startswith('AI-') and not current_provenance:
                # This is a new tag from AI algorithm results
                to_provenance = provenance_map[to_box_key]
                
                # Check if we already have tag_id from state (checked during label selection)
                if self.state.tag_id:
                    tag_id_to_use = self.state.tag_id
                    logger.info(f"Using cached tag_id from state: {tag_id_to_use} (source: {self.state.tag_source})")
                else:
                    # First, ensure the tag exists in the tags table
                    tag_label = self.state.label_name
                    existing_tag = db.get_tag_by_label(tag_label)
                    
                    if not existing_tag:
                        # Create tag if it doesn't exist
                        logger.info(f"Creating new tag: {tag_label}")
                        if not db.insert_new_tag(tag_label, source="CUSTOM"):
                            logger.error(f"Failed to create tag: {tag_label}")
                            failed_count += 1
                            continue
                        existing_tag = db.get_tag_by_label(tag_label)
                    else:
                        # Tag already exists - log it
                        tag_source = existing_tag.get('source', 'UNKNOWN')
                        logger.info(f"Tag '{tag_label}' found with tag_id={existing_tag['id']}, source={tag_source}")
                    
                    tag_id_to_use = existing_tag['id']
                    # Update state for future use
                    self.state.tag_id = tag_id_to_use
                    self.state.tag_source = existing_tag.get('source', 'CUSTOM')
                
                # Now create the artwork-tag link with AI provenance
                if db.insert_artwork_tag_link(inventory_number, tag_id_to_use, to_provenance):
                    logger.info(f"Created new tag link: {inventory_number} → {tag_label} (provenance: {to_provenance})")
                    success_count += 1
                else:
                    logger.error(f"Failed to create tag link: {inventory_number}")
                    failed_count += 1
                continue
            
            # Guard: Protect FABRITIUS records
            if current_provenance == "FABRITIUS":
                logger.info(f"Skipping FABRITIUS tag for artwork {inventory_number} (protected)")
                protected_count += 1
                continue
            
            # For normal promote/demote operations, tag_id is required
            if not tag_id:
                logger.warning(f"Missing tag_id for artwork {inventory_number} (not an AI algorithm result)")
                failed_count += 1
                continue
            
            # Determine source and target provenance
            from_provenance = current_provenance or provenance_map.get(from_box_key, "AI")
            to_provenance = provenance_map[to_box_key]
            
            # Update provenance in database
            if db.update_artwork_tag_provenance(
                inventarisnummer=inventory_number,
                tag_id=tag_id,
                from_provenance=from_provenance,
                to_provenance=to_provenance
            ):
                logger.info(f"Updated {inventory_number}: {from_provenance} → {to_provenance}")
                success_count += 1
            else:
                logger.error(f"Failed to update {inventory_number}")
                failed_count += 1
        
        logger.info(
            f"Database update complete: {success_count} success, "
            f"{failed_count} failed, {protected_count} protected"
        )
        
        return success_count, failed_count, protected_count
    
    def delete_selected(self, box_key: str):
        """Delete labels for selected artworks."""
        selected_ids = self.state.get_selected_artworks(box_key)
        if not selected_ids:
            return
        
        # Show confirmation dialog
        with ui.dialog() as dialog, ui.card():
            ui.label('Are you sure?').classes('text-lg font-bold mb-2')
            ui.label(f'Delete the label from {len(selected_ids)} artwork(s) forever?').classes('mb-2')
            ui.label('(Database will be modified)').classes('text-sm text-red-600 mb-4')
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancel', on_click=dialog.close).props('outline')
                ui.button('Delete', color='red', on_click=lambda: self._confirm_delete(box_key, selected_ids, dialog))
        
        dialog.open()
    
    def _confirm_delete(self, box_key: str, selected_ids: set, dialog):
        """Execute deletion after confirmation."""
        logger.info(f"Deleting {len(selected_ids)} labels from {box_key}")
        
        # Get box results
        box_results = self.state.get_box_results(box_key)
        
        # Prepare list for backend deletion
        items_to_delete = []
        remaining_artworks = []
        deleted_count = 0
        
        for artwork in box_results.results:
            artwork_id = artwork.get('id', artwork.get('inventory_number'))
            if artwork_id not in selected_ids:
                remaining_artworks.append(artwork)
            else:
                # Collect info for backend deletion
                items_to_delete.append({
                    'inventarisnummer': artwork_id,
                    'tag': self.state.label_name,
                    'tag_id': artwork.get('tag_id')
                })
                deleted_count += 1
        
        # Backend call to delete labels from database
        try:
            from backend.supabase_client import SupabaseClient
            db = SupabaseClient()
            db.delete_tag_from_artworks(items_to_delete)
            logger.info(f"Deleted {deleted_count} tag-artwork links from database")
        except Exception as e:
            logger.error(f"Failed to delete labels from database: {e}")
            ui.notify(f'Failed to delete labels: {e}', type='negative')
            dialog.close()
            return
        
        # Update box results (remove from UI)
        box_results.results = remaining_artworks
        box_results.total_count = len(remaining_artworks)
        
        ui.notify(f'Deleted {deleted_count} labels', type='positive')
        self.state.deselect_all_artworks(box_key)
        self.update_boxes()
        dialog.close()
    
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
        self.update_boxes()
    
    def close_algorithm(self, algo_name: str):
        """Close (remove) an algorithm from the selected list."""
        if algo_name in self.state.selected_algorithms:
            self.state.selected_algorithms.remove(algo_name)
            logger.info(f"Closed algorithm: {algo_name}")
            
            # Re-render search bar to update checkboxes and boxes
            self.update_search_bar()
            self.update_boxes()
    
    def toggle_box(self, box_key: str):
        """Toggle a box open/closed and sync with algorithms."""
        self.state.toggle_box(box_key)
        
        is_open = self.state.is_box_open(box_key)
        logger.info(f"Box '{box_key}' {'opened' if is_open else 'closed'}")
        
        # Re-render search bar to update checkboxes and boxes
        self.update_search_bar()
        self.update_boxes()
    
    def toggle_view(self, view_mode: str):
        """Toggle between grid and list view."""
        self.state.view_mode = view_mode
        logger.info(f"View mode changed to: {view_mode}")
        
        # Re-render boxes with new view
        self.update_boxes()


# ========== Page Definition ==========

@ui.page(routes.ROUTE_LABEL)
def label_page():
    """Label validation page."""
    logger.info("Label validation page loaded")
    
    # Get or create unique tab ID from browser storage (persists across navigations)
    if 'tab_id' not in app.storage.browser:
        import uuid
        app.storage.browser['tab_id'] = str(uuid.uuid4())
    
    tab_id = app.storage.browser['tab_id']
    
    # Get or create controller for this tab
    if tab_id not in _label_controllers:
        logger.info(f"Creating new LabelPageController for tab {tab_id[:8]}")
        _label_controllers[tab_id] = LabelPageController()
    else:
        logger.info(f"Reusing LabelPageController for tab {tab_id[:8]}")
    
    controller = _label_controllers[tab_id]
    
    # Log current state
    logger.info(f"State - Label: {controller.state.label_name}, Algorithms: {controller.state.selected_algorithms}, Results: {len(controller.state.results_per_box)}")
    
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
        controller.update_boxes()



