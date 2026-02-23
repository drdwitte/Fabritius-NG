"""
Detail page for individual artwork view.

ARCHITECTURE: Controller Pattern
=================================
This module acts as a THIN COORDINATOR following the same pattern as search.py and label.py.

Responsibilities:
- Define page route
- Create UI layout structure (search bar, artwork image, metadata)
- Maintain UIState references to UI elements
- Coordinate artwork data display and search functionality
- Per-user state isolation via controller instances

UI Layout Structure:
┌─────────────────────────────────────┐
│ Header (logo, navigation)           │
├─────────────────────────────────────┤
│ Search Bar (inventory number)       │
├─────────────────────────────────────┤
│ Artwork Display                     │
│ ┌──────────────┬──────────────────┐ │
│ │  Image       │  Metadata        │ │
│ │  (2/3)       │  (1/3)           │ │
│ │              │  - Basic Info    │ │
│ │              │  - Technical     │ │
│ │              │  - Artist Info   │ │
│ │              │  - Iconography   │ │
│ │              │  - Location      │ │
│ └──────────────┴──────────────────┘ │
└─────────────────────────────────────┘
"""

from nicegui import ui, app
from backend.supabase_client import SupabaseClient
from config import settings
from ui_components.header import render_header
from loguru import logger
import routes
import uuid

# Module-level storage: Safe because each tab gets unique ID from browser storage
# Memory persists during app runtime (acceptable tradeoff for state preservation)
_detail_controllers = {}


class DetailPageUIState:
    """Container for detail page UI element references."""
    def __init__(self):
        self.search_bar_container = None
        self.main_content_container = None


class DetailPageController:
    """
    Controller for the detail page.
    Manages artwork state, UI state, and coordinates all interactions.
    
    IMPORTANT: Each user gets their own controller instance via app.storage.browser
    to prevent state leaking between users.
    """
    
    def __init__(self):
        self.ui_state = DetailPageUIState()
        self.current_artwork = None
        self.source_page = None  # Track where user came from ('search' or 'label')
        self.current_tags = []  # Existing Fabritius tags
        self.recommended_tags = []  # AI-recommended tags
        self.hidden_tag_ids = set()  # IDs of tags user accepted/rejected (to hide them)
        logger.info("DetailPageController initialized")
    
    def set_artwork(self, artwork_data: dict, source: str = None) -> None:
        """Store artwork data for display.
        
        Args:
            artwork_data: Dictionary with artwork information
            source: Source page ('search' or 'label')
        """
        self.current_artwork = artwork_data
        self.source_page = source
        self.hidden_tag_ids = set()  # Reset hidden tags on new artwork
        logger.info(f"Artwork set: {artwork_data.get('inventarisnummer', 'Unknown')} from {source}")
        
        # Load tags for this artwork
        self.load_tags()
    
    def get_artwork(self) -> dict:
        """Retrieve current artwork data."""
        return self.current_artwork
    
    def get_source(self) -> str:
        """Retrieve source page."""
        return self.source_page
    
    def load_tags(self) -> None:
        """Load current and recommended tags for the artwork."""
        if not self.current_artwork:
            return
        
        inventory = self.current_artwork.get('inventarisnummer')
        if not inventory:
            return
        
        try:
            client = SupabaseClient()
            
            # Get existing tags
            self.current_tags = client.get_tags_for_artwork(inventory)
            logger.info(f"Loaded {len(self.current_tags)} existing tags for artwork {inventory}")
            
            # Get recommended tags
            self.recommended_tags = client.recommend_tags_for_artwork(inventory, limit=10)
            logger.info(f"Loaded {len(self.recommended_tags)} recommended tags for artwork {inventory}")
            
        except Exception as e:
            logger.error(f"Error loading tags for artwork {inventory}: {e}")
            self.current_tags = []
            self.recommended_tags = []
    
    def accept_tag(self, tag_id: int, label: str) -> None:
        """Accept a recommended tag and add it to the artwork.
        
        Args:
            tag_id: ID from iconographic_tags (used for UI tracking)
            label: Label of the tag (for display)
        """
        if not self.current_artwork:
            return
        
        inventory = self.current_artwork.get('inventarisnummer')
        if not inventory:
            return
        
        try:
            client = SupabaseClient()
            
            # Get the correct tag_id from the 'tags' table (not iconographic_tags)
            # artwork-tags has a foreign key to tags.id, not iconographic_tags.id
            correct_tag_id = client.get_tagID_by_label(label)
            
            if correct_tag_id is None:
                ui.notify(f'Tag not found in tags table: {label}', type='negative')
                logger.error(f"Tag '{label}' exists in iconographic_tags but not in tags table")
                return
            
            success = client.insert_artwork_tag_link(inventory, correct_tag_id, provenance='AI')
            
            if success:
                # Add to current tags (use correct_tag_id for consistency)
                self.current_tags.append({'tag_id': correct_tag_id, 'label': label, 'provenance': 'AI'})
                # Hide from recommendations (use iconographic tag_id for UI tracking)
                self.hidden_tag_ids.add(tag_id)
                ui.notify(f'Added tag: {label}', type='positive')
                # Refresh UI
                self.render_content()
            else:
                ui.notify(f'Failed to add tag: {label}', type='negative')
        except Exception as e:
            logger.error(f"Error accepting tag {label}: {e}")
            ui.notify(f'Error adding tag: {str(e)}', type='negative')
    
    def reject_tag(self, tag_id: int, label: str) -> None:
        """Reject a recommended tag (hide it from the list).
        
        Args:
            tag_id: ID of the tag to reject
            label: Label of the tag (for display)
        """
        # Just hide it from the UI
        self.hidden_tag_ids.add(tag_id)
        logger.info(f"Rejected tag: {label}")
        # Refresh UI
        self.render_content()
    
    def search_artwork(self, inventory: str) -> None:
        """Search for artwork by inventory number.
        
        Args:
            inventory: Inventory number to search for
        """
        if not inventory:
            ui.notify('Please enter an inventory number', type='warning')
            return
        
        logger.info(f"Searching for artwork with inventory number: {inventory}")
        
        try:
            client = SupabaseClient()
            artwork = client.get_artwork_by_inventory(inventory)
            
            if artwork:
                # Update state and refresh UI
                self.set_artwork(artwork, source=self.source_page)
                ui.notify(f'Loaded artwork: {inventory}', type='positive')
                
                # Refresh UI
                self.render_page()
            else:
                ui.notify(f'Artwork not found: {inventory}', type='negative')
        except Exception as e:
            logger.error(f"Error searching for artwork {inventory}: {e}")
            ui.notify(f'Database error: {str(e)}', type='negative')
    
    def render_search_bar(self) -> None:
        """Render inventory number search bar."""
        if not self.ui_state.search_bar_container:
            return
        
        self.ui_state.search_bar_container.clear()
        
        with self.ui_state.search_bar_container:
            with ui.card().classes('w-full mb-4 p-3'):
                with ui.row().classes('w-full items-center gap-3'):
                    ui.icon('search').classes(f'text-xl text-[{settings.primary_color}]')
                    
                    search_input = ui.input(
                        placeholder='Enter inventory number (e.g., 10000 / 101, 1352)',
                        value=''
                    ).classes('flex-grow').props('outlined dense')
                    
                    # Allow Enter key to trigger search
                    search_input.on('keydown.enter', lambda: self.search_artwork(search_input.value.strip()))
                    
                    ui.button(
                        'Search',
                        icon='arrow_forward',
                        on_click=lambda: self.search_artwork(search_input.value.strip())
                    ).props(f'flat color={settings.primary_color}')
    
    def render_page(self) -> None:
        """Render the complete detail page (search bar + content)."""
        self.render_search_bar()
        self.render_content()
    
    def render_content(self) -> None:
        """Render main artwork content."""
        if not self.ui_state.main_content_container:
            return
        
        self.ui_state.main_content_container.clear()
        
        with self.ui_state.main_content_container:
            self._render_artwork_display()
    
    def _render_artwork_display(self) -> None:
        """Internal helper to render artwork content."""
        artwork_data = self.current_artwork
        source_page = self.source_page
        
        if not artwork_data:
            ui.label('No artwork selected').classes('text-xl text-gray-600')
            ui.button('Back to Search', icon='arrow_back', on_click=lambda: ui.navigate.to(routes.ROUTE_SEARCH)).props('flat')
            return
        
        # Extract artwork data
        inventory = artwork_data.get('inventory', artwork_data.get('inventarisnummer', 'N/A'))
        title = artwork_data.get('title', artwork_data.get('beschrijving_titel', 'Untitled'))
        artist = artwork_data.get('artist', artwork_data.get('beschrijving_kunstenaar', 'Unknown Artist'))
        
        # Year: try beschrijving_creatiedatum first, then creatie_laatste_datum, then beschrijving_datering
        year = (artwork_data.get('beschrijving_creatiedatum') or 
                artwork_data.get('creatie_laatste_datum') or 
                artwork_data.get('year') or 
                artwork_data.get('beschrijving_datering') or 
                'N/A')
        
        # Combine artist name (first + last)
        first_name = artwork_data.get('kunstenaar_voornaam', '')
        last_name = artwork_data.get('kunstenaar_familienaam', '')
        artist_full_name = ' '.join(filter(None, [first_name, last_name])) if (first_name or last_name) else None
        
        # Combine birth and death dates
        birth_date = artwork_data.get('kunstenaar_geboortedatum', '')
        death_date = artwork_data.get('kunstenaar_overlijdensdatum', '')
        life_dates = None
        if birth_date and death_date:
            life_dates = f"{birth_date} - {death_date}"
        elif birth_date:
            life_dates = f"{birth_date} -"
        elif death_date:
            life_dates = f"- {death_date}"
        
        image_path = artwork_data.get('image_url', artwork_data.get('image', artwork_data.get('imageOpacLink', '')))
        
        # Add combined fields to artwork_data for rendering
        if artist_full_name:
            artwork_data['_combined_artist_name'] = artist_full_name
        if life_dates:
            artwork_data['_combined_life_dates'] = life_dates
        
        # Construct full image URL if needed
        if image_path and not image_path.startswith('http'):
            image_url = f"{settings.image_base_url}{image_path}" if image_path.startswith('/') else f"{settings.image_base_url}/{image_path}"
        else:
            image_url = image_path
        
        # Back buttons - show relevant button based on source
        with ui.row().classes('gap-2 mb-4'):
            if source_page == 'search':
                ui.button('← Back to Search', on_click=lambda: ui.navigate.to(routes.ROUTE_SEARCH)).props('flat').classes(f'text-[{settings.primary_color}]')
            elif source_page == 'label':
                ui.button('← Back to Label Tool', on_click=lambda: ui.navigate.to(routes.ROUTE_LABEL)).props('flat').classes(f'text-[{settings.primary_color}]')
            else:
                ui.button('← Back to Search', on_click=lambda: ui.navigate.to(routes.ROUTE_SEARCH)).props('flat').classes(f'text-[{settings.primary_color}]')
                ui.button('← Back to Label Tool', on_click=lambda: ui.navigate.to(routes.ROUTE_LABEL)).props('flat').classes(f'text-[{settings.primary_color}]')
        
        # Main content: image + metadata side by side
        with ui.row().classes('w-full gap-6 items-start'):
            # Left: Large image (takes 2/3 of space)
            with ui.column().classes('flex-[2]'):
                if image_url:
                    ui.image(image_url).classes('w-full rounded-lg shadow-lg')
                else:
                    with ui.card().classes('w-full h-96 flex items-center justify-center bg-gray-100'):
                        ui.icon('image_not_supported').classes('text-6xl text-gray-400')
                        ui.label('No image available').classes('text-gray-500 mt-2')
            
            # Right: Metadata (takes 1/3 of space, no scrolling)
            with ui.column().classes('flex-[1] gap-4').style('min-width: 350px;'):
                # Title
                ui.label(title).classes('text-2xl font-bold text-gray-800')
                
                # Artist
                ui.label(artist).classes('text-lg text-gray-700')
                
                # Year
                ui.label(year).classes('text-lg text-gray-700')
                
                # Inventory number
                ui.label(f'Inventory: {inventory}').classes('text-sm text-gray-600')
                
                ui.separator()
                
                # Basic Information Section
                basic_fields = [
                    ('classificatie', 'Classification', 'category'),
                    ('soort', 'Object Type', 'art_track'),
                    ('beschrijving_afmetingen', 'Dimensions', 'straighten'),
                ]
                
                self._render_metadata_section('Basic Information', basic_fields, artwork_data)
                
                # Technical Information Section
                technical_fields = [
                    ('materialen', 'Materials', 'palette'),
                    ('beschrijving_materiaal', 'Material (Alt)', 'palette'),
                    ('beschrijving_techniek', 'Technique', 'brush'),
                    ('appearance', 'Physical Appearance', 'visibility'),
                    ('stijl', 'Style', 'style'),
                ]
                
                self._render_metadata_section('Technical Details', technical_fields, artwork_data)
                
                # Artist Information Section
                artist_fields = [
                    ('_combined_artist_name', 'Name', 'person'),
                    ('_combined_life_dates', 'Life Dates', 'calendar_today'),
                    ('kunstenaar_nationaliteit', 'Nationality', 'flag'),
                ]
                
                self._render_metadata_section('Artist Information', artist_fields, artwork_data)
                
                # Iconography Section
                iconography_fields = [
                    ('iconografie_subject', 'Subject', 'image'),
                    ('iconografie_termen', 'Iconographic Terms', 'local_offer'),
                    ('iconografie_conceptueel', 'Conceptual Terms', 'lightbulb'),
                    ('iconografie_interpretatie', 'Interpretation', 'description'),
                    ('iconografie_generiek', 'General Description', 'subject'),
                    ('iconografie_specifiek', 'Specific Identification', 'zoom_in'),
                ]
                
                self._render_metadata_section('Iconography', iconography_fields, artwork_data)
                
                # Location & References Section
                location_fields = [
                    ('locatie_naam', 'Location', 'place'),
                    ('recordID', 'Record ID', 'fingerprint'),
                    ('linkToVubis', 'VUBIS Link', 'link'),
                    ('AuthID', 'Authority ID', 'badge'),
                ]
                
                self._render_metadata_section('Location & References', location_fields, artwork_data)
        
        # Tags section below the main content
        ui.separator().classes('my-6')
        self._render_tags_section()
    
    def _render_metadata_section(self, section_title: str, fields: list, artwork_data: dict) -> None:
        """Render a metadata section with fields."""
        # Check if any field has data
        has_data = any(field_key in artwork_data and artwork_data[field_key] for field_key, _, _ in fields)
        
        if not has_data:
            return  # Don't render empty sections
        
        ui.label(section_title).classes('text-sm font-semibold text-gray-500 uppercase mt-4 mb-2')
        
        for field_key, label, icon in fields:
            if field_key in artwork_data and artwork_data[field_key]:
                value = str(artwork_data[field_key])
                # Skip if value is empty or just whitespace
                if value and value.strip():
                    with ui.column().classes('gap-0 mt-2'):
                        ui.label(label).classes('text-xs text-gray-500 uppercase')
                        ui.label(value).classes('text-sm text-gray-700')
    
    def _render_tags_section(self) -> None:
        """Render tags section: existing tags + recommended tags."""
        if not self.current_artwork:
            return
        
        with ui.column().classes('w-full gap-6'):
            # FABRITIUS TAGS - Existing tags
            ui.label('FABRITIUS TAGS').classes('text-lg font-bold text-gray-800 uppercase')
            
            if self.current_tags:
                with ui.row().classes('flex-wrap gap-2'):
                    for tag_info in self.current_tags:
                        label = tag_info.get('label', 'Unknown')
                        provenance = tag_info.get('provenance', 'N/A')
                        
                        # Color based on provenance
                        if provenance == 'EXPERT':
                            color = 'green'
                        elif provenance == 'AI':
                            color = 'blue'
                        else:
                            color = 'gray'
                        
                        ui.chip(
                            label,
                            color=color,
                            icon='local_offer'
                        ).props('outline')
            else:
                ui.label('No tags assigned yet').classes('text-gray-500 italic')
            
            # RECOMMENDED TAGS - AI suggestions
            ui.label('RECOMMENDED TAGS').classes('text-lg font-bold text-gray-800 uppercase mt-6')
            
            # Filter out hidden tags
            visible_recommendations = [
                tag for tag in self.recommended_tags 
                if tag.get('tag_id') not in self.hidden_tag_ids
            ]
            
            if visible_recommendations:
                with ui.row().classes('flex-wrap gap-2'):
                    for tag_info in visible_recommendations:
                        tag_id = tag_info.get('tag_id')
                        label = tag_info.get('label', 'Unknown')
                        similarity = tag_info.get('similarity', 0)
                        
                        with ui.row().classes('items-center gap-2 p-2 border border-gray-200 rounded-lg').style('min-width: 200px;'):
                            # Tag label with similarity score
                            with ui.column().classes('flex-grow gap-0'):
                                ui.label(label).classes('text-sm font-medium')
                                ui.label(f'{similarity:.2%}').classes('text-xs text-gray-500')
                            
                            # Accept button (checkmark)
                            ui.button(
                                icon='check',
                                on_click=lambda tid=tag_id, lbl=label: self.accept_tag(tid, lbl)
                            ).props(f'flat round color=green').classes('w-8 h-8')
                            
                            # Reject button (cross)
                            ui.button(
                                icon='close',
                                on_click=lambda tid=tag_id, lbl=label: self.reject_tag(tid, lbl)
                            ).props(f'flat round color=red').classes('w-8 h-8')
            else:
                ui.label('No more recommendations available').classes('text-gray-500 italic')


def get_or_create_controller(tab_id: str) -> DetailPageController:
    """Get existing or create new controller for this tab.
    
    Args:
        tab_id: Unique browser tab identifier
        
    Returns:
        DetailPageController instance for this tab
    """
    if tab_id not in _detail_controllers:
        logger.info(f"Creating new DetailPageController for tab {tab_id[:8]}")
        _detail_controllers[tab_id] = DetailPageController()
    else:
        logger.info(f"Reusing DetailPageController for tab {tab_id[:8]}")
    
    return _detail_controllers[tab_id]


@ui.page(routes.ROUTE_DETAIL)
def page() -> None:
    """Detail view page for individual artworks."""
    logger.info("Loading Detail page")
    
    # Tab-specific state: Each tab gets unique controller
    if 'tab_id' not in app.storage.browser:
        app.storage.browser['tab_id'] = str(uuid.uuid4())
    
    tab_id = app.storage.browser['tab_id']
    controller = get_or_create_controller(tab_id)
    
    render_header()
    
    # Create containers for dynamic refresh
    controller.ui_state.search_bar_container = ui.column().classes('w-full')
    controller.ui_state.main_content_container = ui.column().classes('w-full')
    
    # Render initial page
    controller.render_page()


# Public accessor function (for backwards compatibility with search/label pages)
def set_artwork_data(artwork_data: dict, source: str = None) -> None:
    """Store artwork data for display on detail page.
    
    Args:
        artwork_data: Dictionary with artwork information
        source: Source page ('search' or 'label')
    """
    # Get current tab's controller
    if 'tab_id' in app.storage.browser:
        tab_id = app.storage.browser['tab_id']
        controller = get_or_create_controller(tab_id)
        controller.set_artwork(artwork_data, source=source)
