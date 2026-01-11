from nicegui import ui, app
from backend.supabase_client import SupabaseClient
from ui_components.config import IMAGE_BASE_URL, BROWN
from loguru import logger

# Temporary storage for artwork data (simple in-memory dict)
_artwork_storage = {}

def render_detail(ui_instance):
    """Render detail view for a single artwork.
    
    Reads artwork data from module-level _artwork_storage dict
    """
    # Get artwork data from storage
    artwork_data = _artwork_storage.get('current_artwork')
    
    if not artwork_data:
        ui.label('No artwork selected').classes('text-xl text-gray-600')
        ui.button('Back to Search', icon='arrow_back', on_click=lambda: ui.navigate.to('/search')).props('flat')
        return
    
    # Extract artwork data
    inventory = artwork_data.get('inventory', artwork_data.get('inventarisnummer', 'N/A'))
    title = artwork_data.get('title', artwork_data.get('beschrijving_titel', 'Untitled'))
    artist = artwork_data.get('artist', artwork_data.get('beschrijving_kunstenaar', 'Unknown Artist'))
    year = artwork_data.get('year', artwork_data.get('beschrijving_datering', 'N/A'))
    image_path = artwork_data.get('image', artwork_data.get('imageOpacLink', ''))
    
    # Construct full image URL if needed
    if image_path and not image_path.startswith('http'):
        image_url = f"{IMAGE_BASE_URL}{image_path}" if image_path.startswith('/') else f"{IMAGE_BASE_URL}/{image_path}"
    else:
        image_url = image_path
    
    # Back button
    ui.button('← Back to Search', on_click=lambda: ui.navigate.to('/search')).props('flat').classes(f'mb-4 text-[{BROWN}]')
    
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
                ui.icon('person').classes(f'text-[{BROWN}]')
                ui.label(artist).classes('text-lg text-gray-700')
            
            # Year
            with ui.row().classes('items-center gap-2'):
                ui.icon('calendar_today').classes(f'text-[{BROWN}]')
                ui.label(year).classes('text-lg text-gray-700')
            
            # Inventory number
            with ui.row().classes('items-center gap-2'):
                ui.icon('tag').classes(f'text-[{BROWN}]')
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
                        ui.icon(icon).classes(f'text-[{BROWN}] mt-1')
                        with ui.column().classes('gap-0'):
                            ui.label(label).classes('text-xs text-gray-500 uppercase')
                            ui.label(str(artwork_data[field_key])).classes('text-sm text-gray-700')