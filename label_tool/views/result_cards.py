"""
Result display views for label validation.

Renders artworks in gallery or list view format.
"""

from nicegui import ui
from typing import List, Dict, Any, Callable, Optional
from loguru import logger
import routes
from pages import detail


def show_artwork_detail(artwork_data):
    """
    Navigate to detail view with artwork data.
    
    Args:
        artwork_data: Dictionary containing artwork information
    """
    logger.info(f"Navigating to detail view for artwork: {artwork_data.get('id', artwork_data.get('inventory'))}")
    
    # Store artwork data in detail module's page_state with source
    detail.page_state.set_artwork(artwork_data, source='label')
    
    # Navigate to detail route
    ui.navigate.to(routes.ROUTE_DETAIL)


def render_result_grid_view(
    results: List[Dict[str, Any]], 
    is_ai_column: bool = False, 
    grid_cols: int = None,
    column_key: str = None,
    selected_ids: set = None,
    on_toggle_selection: Optional[Callable] = None
):
    """
    Render results in gallery grid view.
    
    Args:
        results: List of artwork results
        is_ai_column: Whether this is an AI algorithm column (shows confidence scores)
        grid_cols: Number of columns in grid (if None, auto-determine based on column type)
        column_key: Column identifier for selection tracking
        selected_ids: Set of selected artwork IDs
        on_toggle_selection: Callback for toggling artwork selection
    """
    # Determine grid layout
    if grid_cols is None:
        if is_ai_column:
            grid_cols = 3  # Smaller grid for AI columns (3 per row)
        else:
            grid_cols = 5  # Larger grid for validated columns (5 per row)
    
    # Use inline style for grid columns to ensure compatibility
    with ui.element('div').classes('grid gap-4 w-full').style(f'grid-template-columns: repeat({grid_cols}, minmax(0, 1fr));'):
        for result in results:
            artwork_id = result.get('id', result.get('inventory_number'))
            is_selected = selected_ids and artwork_id in selected_ids if selected_ids else False
            
            # Gallery tile with image and metadata overlay
            # Use fixed min-height to ensure cards render properly
            border_class = 'ring-4 ring-blue-500' if is_selected else ''
            card = ui.card().classes(f'w-full p-0 overflow-hidden cursor-pointer hover:shadow-xl transition relative {border_class}').style('aspect-ratio: 1/1; min-height: 200px;')
            
            # Click on card (but not on checkbox) goes to detail
            card.on('click', lambda r=result: show_artwork_detail(r))
            
            with card:
                # Image (full card background)
                ui.image(result.get('image_url', '')).classes('w-full h-full object-cover absolute inset-0').style('min-height: 200px;')
                
                # Selection checkbox (top-left) - stop propagation to prevent detail navigation
                if on_toggle_selection and artwork_id:
                    with ui.element('div').classes('absolute top-2 left-2 z-10').on('click.stop', lambda: None):
                        ui.checkbox(value=is_selected, on_change=lambda e, aid=artwork_id: on_toggle_selection(aid)).classes('bg-white rounded shadow-lg').props('size=lg')
                
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


def render_result_list_view(
    results: List[Dict[str, Any]], 
    is_ai_column: bool = False,
    column_key: str = None,
    selected_ids: set = None,
    on_toggle_selection: Optional[Callable] = None
):
    """
    Render results in list view format.
    
    Args:
        results: List of artwork results
        is_ai_column: Whether this is an AI algorithm column (shows confidence scores)
        column_key: Column identifier for selection tracking
        selected_ids: Set of selected artwork IDs
        on_toggle_selection: Callback for toggling artwork selection
    """
    with ui.column().classes('w-full gap-3'):
        for result in results:
            artwork_id = result.get('id', result.get('inventory_number'))
            is_selected = selected_ids and artwork_id in selected_ids if selected_ids else False
            
            # List item card with thumbnail and metadata side by side
            border_class = 'ring-2 ring-blue-500' if is_selected else ''
            card = ui.card().classes(f'w-full hover:shadow-lg transition cursor-pointer {border_class}')
            
            # Click on card goes to detail
            card.on('click', lambda r=result: show_artwork_detail(r))
            
            with card:
                with ui.row().classes('w-full items-center gap-4 p-2'):
                    # Selection checkbox - stop propagation to prevent detail navigation
                    if on_toggle_selection and artwork_id:
                        with ui.element('div').on('click.stop', lambda: None):
                            ui.checkbox(value=is_selected, on_change=lambda e, aid=artwork_id: on_toggle_selection(aid)).classes('flex-shrink-0').props('size=md')
                    
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
