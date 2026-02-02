"""
Label validation page for the Fabritius-NG application.

ARCHITECTURE: Controller Pattern (following search.py structure)
================================================================
This module acts as a THIN COORDINATOR following the same pattern as search.py.

Responsibilities:
- Define page route
- Create UI layout structure (search bar, label info, level columns)
- Maintain UIState references to UI elements
- Delegate to controller for all interactions

Future expansion:
- label_tool/ package with:
  - state.py (LabelState for business logic)
  - views/ (search_bar.py, label_card.py, level_columns.py)
  - label_service.py (API calls to thesaurus)
"""

from nicegui import ui, app
from ui_components.header import render_header
from ui_components.buttons import icon_button, run_button
from loguru import logger
import routes


class LabelPageUIState:
    """Container for label page UI element references."""
    def __init__(self):
        self.search_input = None
        self.search_container = None
        self.definition_container = None
        self.thesaurus_label = None
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
        
        # Label state
        self.current_label = None
        self.current_definition = None
        self.selected_thesaurus = None
        self.selected_algorithms = ['Semantic Search']
        
        # Configuration
        self.thesaurus_options = ['Garnier', 'AAT', 'Iconclass', 'Fabritius']
        self.algorithm_options = ['Semantic Search', 'CLIP', 'BLIP']
        self.visible_levels = []  # TODO: Load from config or state
    
    # ========== Thesaurus Actions ==========
    
    def select_thesaurus(self, thesaurus: str):
        """Handle thesaurus selection."""
        logger.info(f"Thesaurus changed to: {thesaurus if thesaurus else 'None (Free search)'}")
        
        self.selected_thesaurus = thesaurus
        
        # Clear current label when switching thesaurus
        if self.current_label:
            logger.info(f"Clearing current label '{self.current_label}' due to thesaurus change")
            self.clear_label()
        
        # Update button label
        if self.ui_state.thesaurus_label:
            if thesaurus:
                self.ui_state.thesaurus_label.set_text(thesaurus)
                ui.notify(f'Selected thesaurus: {thesaurus}')
            else:
                self.ui_state.thesaurus_label.set_text('Thesaurus')
                ui.notify('Free search mode enabled')
    
    # ========== Algorithm Actions ==========
    
    def toggle_algorithm(self, algorithm: str, is_selected: bool):
        """Toggle algorithm selection."""
        if is_selected and algorithm not in self.selected_algorithms:
            self.selected_algorithms.append(algorithm)
            logger.info(f"Algorithm '{algorithm}' selected")
        elif not is_selected and algorithm in self.selected_algorithms:
            self.selected_algorithms.remove(algorithm)
            logger.info(f"Algorithm '{algorithm}' deselected")
        
        logger.info(f"Currently selected algorithms: {self.selected_algorithms}")
        ui.notify(f'Selected algorithms: {", ".join(self.selected_algorithms) if self.selected_algorithms else "None"}')
    
    # ========== Label Actions ==========
    
    def open_new_label_dialog(self):
        """Opens a dialog to create a new label."""
        # Switch to Fabritius thesaurus when opening dialog
        self.select_thesaurus('Fabritius')
        
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
    
    def create_label(self, name: str, definition: str, dialog):
        """Creates a new label in the Fabritius thesaurus."""
        if not name:
            logger.warning("Label creation failed: name is required")
            ui.notify('Label name is required', type='warning')
            return
        
        logger.info(f"Creating new label: '{name}' with definition: '{definition[:50] if definition else '(none)'}...'")
        
        # TODO: Implement actual label creation logic
        # label_service.create_label(name, definition, 'Fabritius')
        
        ui.notify(f'Created label: {name}')
        dialog.close()
        
        # Set current label and definition
        self.current_label = name
        self.current_definition = definition or ''
        logger.info(f"Label '{name}' set as current label")
        
        # Reset thesaurus button label (but keep Fabritius selected internally)
        if self.ui_state.thesaurus_label:
            self.ui_state.thesaurus_label.set_text('Thesaurus')
        
        # Update UI
        self.render_search_input()
        self.render_definition()
    
    def clear_label(self):
        """Clears the currently selected label."""
        logger.info(f"Label '{self.current_label}' manually cleared by user")
        
        self.current_label = None
        self.current_definition = None
        
        # Update UI
        self.render_search_input()
        self.render_definition()
    
    # ========== Search Actions ==========
    
    def execute_search(self):
        """Executes the search based on current state."""
        logger.info("Search button clicked")
        
        search_text = self.ui_state.search_input.value if self.ui_state.search_input else ''
        
        if not search_text:
            logger.warning("Search failed: no search query entered")
            ui.notify('Please enter a search query', type='warning')
            return
        
        if not self.selected_algorithms:
            logger.warning("Search failed: no algorithms selected")
            ui.notify('Please select at least one algorithm', type='warning')
            return
        
        # Determine search mode
        if self.selected_thesaurus:
            # Mode 1a: Search within selected thesaurus
            logger.info(f"Executing thesaurus search | Thesaurus: {self.selected_thesaurus} | Query: '{search_text}' | Algorithms: {self.selected_algorithms}")
            ui.notify(f'Searching in {self.selected_thesaurus} for: {search_text} using {", ".join(self.selected_algorithms)}')
            # TODO: Implement thesaurus-specific search
        else:
            # Mode 1c: Free semantic search with selected algorithms
            logger.info(f"Executing free search | Query: '{search_text}' | Algorithms: {self.selected_algorithms}")
            ui.notify(f'Running search for: {search_text} using {", ".join(self.selected_algorithms)}')
            # TODO: Implement semantic search with selected algorithms
    
    # ========== UI Rendering ==========
    
    def render_search_input(self):
        """Renders either the label tag or the input field in the search container."""
        if not self.ui_state.search_container:
            return
        
        # Clear existing content
        self.ui_state.search_container.clear()
        
        with self.ui_state.search_container:
            if self.current_label:
                # Show label tag with Fabritius colors (brown background, white text)
                with ui.element('div').classes('flex items-center gap-2 bg-amber-900 text-white px-3 py-1 rounded'):
                    ui.icon('local_offer').classes('text-white text-sm')
                    ui.label(self.current_label).classes('font-semibold')
                    ui.button(icon='close', on_click=lambda: self.clear_label()).props('flat dense round size=sm').classes('text-white')
            else:
                # Show input field when no label is selected
                self.ui_state.search_input = ui.input(
                    placeholder='Search labels or type freely for semantic search...', 
                    value=''
                ).props('borderless dense').classes('flex-grow')
    
    def render_definition(self):
        """Renders the definition text below the search bar in italics."""
        if not self.ui_state.definition_container:
            return
        
        # Clear existing content
        self.ui_state.definition_container.clear()
        
        # Show definition if there's a current label with a definition
        if self.current_label and self.current_definition:
            with self.ui_state.definition_container:
                # Truncate to 100 characters and add ellipsis if needed
                truncated_def = self.current_definition[:100]
                if len(self.current_definition) > 100:
                    truncated_def += '...'
                ui.label(truncated_def).classes('text-sm text-gray-600 italic mt-1')
    
    def render_search_bar(self):
        """Renders the search bar with thesaurus, algorithm, and action buttons."""
        
        # Top bar: full width, left input, right buttons
        with ui.row().props('flat').classes('w-full flex items-center justify-between'):
            # Left: search container with tag or input
            self.ui_state.search_container = ui.element('div').classes('flex-grow flex items-center gap-2 min-h-9')
            self.render_search_input()
            
            # Right: action buttons
            with ui.row().classes('gap-2'):
                # Thesaurus selector as icon_button with menu
                with ui.element('div').classes('relative'):
                    thesaurus_btn = ui.button(on_click=lambda: None)
                    thesaurus_btn.props('color=none text-color=none')
                    thesaurus_btn.classes('h-9 px-3 flex items-center gap-x-8 rounded-md '
                                         'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 py-1')
                    with thesaurus_btn:
                        ui.icon('book').classes('text-gray-700 text-lg')
                        self.ui_state.thesaurus_label = ui.label('Thesaurus').classes('text-gray-700 text-base font-bold').style('text-transform: none; margin-left: 10px;')
                        with ui.menu():
                            ui.menu_item('None (Free search)', on_click=lambda: self.select_thesaurus(None))
                            ui.separator()
                            for thesaurus in self.thesaurus_options:
                                ui.menu_item(thesaurus, on_click=lambda t=thesaurus: self.select_thesaurus(t))
                
                # New Label button
                icon_button('add', 'New Label', lambda: self.open_new_label_dialog())
                
                # Search button with algorithm selector dropdown
                with ui.element('div').classes('relative'):
                    search_btn = run_button('Search', lambda: None)
                    with search_btn:
                        with ui.menu() as search_menu:
                            with ui.card().classes('p-4'):
                                ui.label('Select Algorithms').classes('text-lg font-bold mb-3')
                                
                                # Algorithm checkboxes
                                for algo in self.algorithm_options:
                                    ui.checkbox(
                                        algo, 
                                        value=algo in self.selected_algorithms,
                                        on_change=lambda e, a=algo: self.toggle_algorithm(a, e.value)
                                    ).classes('mb-2')
                                
                                ui.separator().classes('my-3')
                                
                                # Run button inside menu
                                with ui.row().classes('justify-end w-full'):
                                    ui.button('Run Search', on_click=lambda: [search_menu.close(), self.execute_search()]).props('color=primary')
        
        # Definition row below search bar
        self.ui_state.definition_container = ui.element('div').classes('w-full')
        self.render_definition()
    
    def render_level_column(self, level_name: str):
        """Renders a single level column."""
        with ui.column().classes('min-w-80'):  # min-width 320px
            ui.label(level_name).classes('text-lg font-semibold mb-2')
            # TODO: Render actual level content
    
    def render_columns_section(self):
        """Renders the columns section with all visible levels."""
        with ui.row().classes('flex-1 overflow-x-auto gap-4 p-4'):
            # For each visible level
            for level in self.visible_levels:
                self.render_level_column(level)
    
    def render_label_tool(self):
        """Renders the complete label tool structure."""
        
        # Title & icon
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.icon('local_offer').classes('text-2xl text-amber-700')
            ui.label('Label Validation').classes('text-2xl font-bold')
        
        # Main column (h-screen, no gap, full width)
        with ui.column().classes('h-screen w-full'):
            
            # HEADER SECTION - with shadow for visual separation
            with ui.column().classes('bg-white shadow-sm px-4 py-2 gap-4 border-b w-full'):
                # Search bar row
                self.render_search_bar()
            
            # COLUMNS SECTION
            self.render_columns_section()


# Register page route
@ui.page(routes.ROUTE_LABEL)
def page():
    """Label validation page."""
    logger.info("Loading Label page")
    
    # Create controller per client session (in-memory, not persisted)
    # app.storage.client is session-based and doesn't require JSON serialization
    # This ensures each user/browser tab has their own label state
    if 'label_controller' not in app.storage.client:
        logger.info("Creating new LabelPageController for client session")
        app.storage.client['label_controller'] = LabelPageController()
    
    controller = app.storage.client['label_controller']
    
    # Fullscreen page
    ui.query('body').classes('m-0 p-0')
    
    render_header()
    controller.render_label_tool()
