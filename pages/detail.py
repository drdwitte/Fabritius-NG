from nicegui import ui
from backend.supabase_client import SupabaseClient
from config import settings
from ui_components.header import render_header
from loguru import logger
import routes

class DetailPageState:
    """
    Container for detail page state.
    
    Encapsulates artwork data and source page to avoid global variables.
    This makes the code more maintainable, easier to debug, and thread-safe.
    """
    def __init__(self) -> None:
        self.current_artwork = None
        self.source_page = None  # Track where user came from
    
    def set_artwork(self, artwork_data: dict, source: str = None) -> None:
        """Store artwork data for display.
        
        Args:
            artwork_data: Dictionary with artwork information
            source: Source page ('search' or 'label')
        """
        self.current_artwork = artwork_data
        self.source_page = source
    
    def get_artwork(self) -> dict:
        """Retrieve current artwork data."""
        return self.current_artwork
    
    def get_source(self) -> str:
        """Retrieve source page."""
        return self.source_page

# Create single state instance
page_state = DetailPageState()

def render_detail(ui_instance):
    """Render detail view for a single artwork.
    
    Reads artwork data from page_state.
    """
    # Get artwork data from storage
    artwork_data = page_state.get_artwork()
    source_page = page_state.get_source()
    
    if not artwork_data:
        ui.label('No artwork selected').classes('text-xl text-gray-600')
        ui.button('Back to Search', icon='arrow_back', on_click=lambda: ui.navigate.to(routes.ROUTE_SEARCH)).props('flat')
        return
    
    # Extract artwork data
    inventory = artwork_data.get('inventory', artwork_data.get('inventarisnummer', 'N/A'))
    title = artwork_data.get('title', artwork_data.get('beschrijving_titel', 'Untitled'))
    artist = artwork_data.get('artist', artwork_data.get('beschrijving_kunstenaar', 'Unknown Artist'))
    year = artwork_data.get('year', artwork_data.get('beschrijving_datering', 'N/A'))
    image_path = artwork_data.get('image_url', artwork_data.get('image', artwork_data.get('imageOpacLink', '')))
    
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
            # Navigate back to label page - state is cached in app.storage.client
            ui.button('← Back to Label Tool', on_click=lambda: ui.navigate.to(routes.ROUTE_LABEL)).props('flat').classes(f'text-[{settings.primary_color}]')
        else:
            # Show both if source unknown
            ui.button('← Back to Search', on_click=lambda: ui.navigate.to(routes.ROUTE_SEARCH)).props('flat').classes(f'text-[{settings.primary_color}]')
            ui.button('← Back to Label Tool', on_click=lambda: ui.navigate.to(routes.ROUTE_LABEL)).props('flat').classes(f'text-[{settings.primary_color}]')
    
    # Main content: image + metadata side by side
    with ui.row().classes('w-full gap-6'):
        # Left: Large image
        with ui.column().classes('flex-1'):
            if image_url:
                ui.image(image_url).classes('w-full max-w-3xl rounded-lg shadow-lg')
            else:
                with ui.card().classes('w-full h-96 flex items-center justify-center bg-gray-100'):
                    ui.icon('image_not_supported').classes('text-6xl text-gray-400')
                    ui.label('No image available').classes('text-gray-500 mt-2')
        
        # Right: Metadata
        with ui.column().classes('w-96 gap-4'):
            # Title
            ui.label(title).classes('text-2xl font-bold text-gray-800')
            
            # Artist
            with ui.row().classes('items-center gap-2'):
                ui.icon('person').classes(f'text-[{settings.primary_color}]')
                ui.label(artist).classes('text-lg text-gray-700')
            
            # Year
            with ui.row().classes('items-center gap-2'):
                ui.icon('calendar_today').classes(f'text-[{settings.primary_color}]')
                ui.label(year).classes('text-lg text-gray-700')
            
            # Inventory number
            with ui.row().classes('items-center gap-2'):
                ui.icon('tag').classes(f'text-[{settings.primary_color}]')
                ui.label(f'Inventory: {inventory}').classes('text-sm text-gray-600')
            
            ui.separator()
            
            # Additional metadata if available
            metadata_fields = [
                ('beschrijving_afmetingen', 'Dimensions', 'straighten'),
                ('beschrijving_materiaal', 'Material', 'palette'),
                ('beschrijving_techniek', 'Technique', 'brush'),
                ('locatie_naam', 'Location', 'place'),
            ]
            
            for field_key, label, icon in metadata_fields:
                if field_key in artwork_data and artwork_data[field_key]:
                    with ui.row().classes('items-start gap-2 mt-2'):
                        ui.icon(icon).classes(f'text-[{settings.primary_color}] mt-1')
                        with ui.column().classes('gap-0'):
                            ui.label(label).classes('text-xs text-gray-500 uppercase')
                            ui.label(str(artwork_data[field_key])).classes('text-sm text-gray-700')

@ui.page(routes.ROUTE_DETAIL)
def page() -> None:
    """Detail view page for individual artworks."""
    logger.info("Loading Detail page")
    render_header()
    render_detail(ui)


# Public accessor function
def set_artwork_data(artwork_data: dict) -> None:
    """Store artwork data for display on detail page."""
    page_state.set_artwork(artwork_data)
