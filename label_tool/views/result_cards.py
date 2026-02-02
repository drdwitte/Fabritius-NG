"""
Result display views for label validation.

Renders artworks in gallery or list view format.
"""

from nicegui import ui
from typing import List, Dict, Any


def render_result_grid_view(results: List[Dict[str, Any]], is_ai_column: bool = False, grid_cols: int = None):
    """
    Render results in gallery grid view.
    
    Args:
        results: List of artwork results
        is_ai_column: Whether this is an AI algorithm column (shows confidence scores)
        grid_cols: Number of columns in grid (if None, auto-determine based on column type)
    """
    # Determine grid layout
    if grid_cols is None:
        if is_ai_column:
            # AI Results: default 3 columns
            grid_cols = 3
        else:
            # Validated rows: 2 columns
            grid_cols = 2
    
    with ui.element('div').classes(f'grid grid-cols-{grid_cols} gap-4 w-full'):
        for result in results:
            # Gallery tile with image and metadata overlay
            with ui.card().classes('w-full p-0 overflow-hidden cursor-pointer hover:shadow-xl transition relative').style('aspect-ratio: 1/1;'):
                # Image (full card background)
                img = ui.image(result.get('image_url', '')).classes('w-full h-full object-cover absolute inset-0')
                
                # Metadata overlay (bottom of card, semi-transparent dark background)
                with ui.element('div').classes('absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 p-2'):
                    # Title (truncated)
                    title = result.get('title', 'Untitled')
                    if len(title) > 25:
                        title = title[:22] + '...'
                    ui.label(title).classes('text-sm font-bold text-white truncate')
                    
                    # Artist and date
                    artist = result.get('artist', 'Unknown')
                    date = result.get('date', '')
                    ui.label(f'{artist} • {date}').classes('text-xs text-gray-300 truncate')
                    
                    # AI confidence score (if applicable)
                    if is_ai_column and 'confidence' in result:
                        confidence_pct = int(result['confidence'] * 100)
                        ui.label(f'{confidence_pct}% confidence').classes('text-xs text-green-400 mt-1')


def render_result_list_view(results: List[Dict[str, Any]], is_ai_column: bool = False):
    """
    Render results in list view format.
    
    Args:
        results: List of artwork results
        is_ai_column: Whether this is an AI algorithm column (shows confidence scores)
    """
    with ui.column().classes('w-full gap-3'):
        for result in results:
            # List item card with thumbnail and metadata side by side
            with ui.card().classes('w-full hover:shadow-lg transition cursor-pointer'):
                with ui.row().classes('w-full items-center gap-4 p-2'):
                    # Square thumbnail (fixed size)
                    ui.image(result.get('image_url', '')).classes('w-24 h-24 object-cover rounded')
                    
                    # Metadata (always visible)
                    with ui.column().classes('flex-1 gap-1'):
                        ui.label(result.get('title', 'Untitled')).classes('text-base font-bold text-gray-800')
                        ui.label(result.get('artist', 'Unknown')).classes('text-sm text-gray-600')
                        
                        # Date and confidence/validation badges
                        with ui.row().classes('gap-2 mt-1'):
                            ui.badge(result.get('date', '')).props('color=grey')
                            
                            # AI confidence or validation level
                            if is_ai_column and 'confidence' in result:
                                confidence_pct = int(result['confidence'] * 100)
                                ui.badge(f'{confidence_pct}% confidence').props('color=green')
                            elif 'validation_level' in result:
                                level = result['validation_level'].replace('AI-validated', 'AI ✓')
                                ui.badge(level).props('color=purple')


def render_view_toggle(current_view: str, on_toggle_view):
    """
    Render view mode toggle buttons (grid/list).
    
    Args:
        current_view: Current view mode ('grid' or 'list')
        on_toggle_view: Callback function for view toggle
    """
    with ui.row().classes('gap-2'):
        ui.button(
            icon='grid_view',
            on_click=lambda: on_toggle_view('grid')
        ).props(f'flat dense {"color=primary" if current_view == "grid" else "color=grey"}').tooltip('Gallery View')
        
        ui.button(
            icon='view_list',
            on_click=lambda: on_toggle_view('list')
        ).props(f'flat dense {"color=primary" if current_view == "list" else "color=grey"}').tooltip('List View')
