"""
Results display component.

This module handles the rendering of search results in both grid and list views.
"""

from nicegui import ui
from loguru import logger
from config import settings
import routes
from pages import detail


def show_artwork_detail(artwork_data):
    """
    Navigate to detail view with artwork data.
    
    Args:
        artwork_data: Dictionary containing artwork information
    """
    logger.info(f"Navigating to detail view for artwork: {artwork_data.get('inventory')}")
    
    # Store artwork data in detail module's page_state with source
    detail.page_state.set_artwork(artwork_data, source='search')
    
    # Navigate to detail route
    ui.navigate.to(routes.ROUTE_DETAIL)


class ResultsViewState:
    """
    Container for results view state.
    
    Encapsulates results caching and view preferences to avoid global variables.
    This makes the code more maintainable, easier to debug, and thread-safe.
    """
    def __init__(self) -> None:
        self.last_preview_results = None
        self.last_preview_operator_id = None
        self.current_view = 'grid'
        self.results_display_container = None


def get_cached_results(results_state: ResultsViewState):
    """Get cached results if available.
    
    Args:
        results_state: Per-user results state instance
    
    Returns:
        tuple: (results, operator_id) or (None, None) if no cache
    """
    if results_state.last_preview_results and results_state.last_preview_operator_id:
        return results_state.last_preview_results, results_state.last_preview_operator_id
    return None, None


def render_results_ui(results, operator_id, operator_name, results_area, results_state: ResultsViewState):
    """
    Render results UI with header and grid/list view.
    
    Args:
        results: List of artwork dictionaries to display
        operator_id: ID of the operator that generated these results
        operator_name: Name of the operator for display
        results_area: UI container to render results in
        results_state: Per-user results state instance
    """
    logger.info(f"render_results_ui called with {len(results)} results for {operator_name}")
    
    # Cache results for fast view toggling
    results_state.last_preview_results = results
    results_state.last_preview_operator_id = operator_id
    
    logger.info("Starting UI rendering...")
    
    with results_area:
        logger.info("Inside results_area context")
        # Header with view toggle
        with ui.row().classes('w-full items-center justify-between mb-4'):
            ui.label(f'Preview: {operator_name}').classes('text-sm text-gray-600')
            
            with ui.row().classes('gap-2'):
                ui.button(
                    icon='grid_view',
                    on_click=lambda: toggle_view_for_operator('grid', operator_id, operator_name, results_area, results_state)
                ).props(f'flat dense {"color=primary" if results_state.current_view == "grid" else "color=grey"}').tooltip('Grid View')
                
                ui.button(
                    icon='view_list',
                    on_click=lambda: toggle_view_for_operator('list', operator_id, operator_name, results_area, results_state)
                ).props(f'flat dense {"color=primary" if results_state.current_view == "list" else "color=grey"}').tooltip('List View')
        
        logger.info("Header rendered, creating results container...")
        # Results display area - wrap in full width container
        results_state.results_display_container = ui.element('div').classes('w-full')
        
        # Render results
        with results_state.results_display_container:
            container = ui.element('div').classes('w-full')
            with container:
                logger.info(f"Rendering {results_state.current_view} view...")
                if results_state.current_view == 'grid':
                    render_grid_view(results)
                else:
                    render_list_view(results)
        
        logger.info("Results rendered successfully")
        
        # Update result count in header
        ui.run_javascript(f"""
            document.querySelector('[id="results-area"] .text-sm.text-gray-600').textContent = 
                'Preview: {operator_name} ({len(results)} results)';
        """)
    
    logger.info(f"render_results_ui complete")
    ui.notify(f'Preview for {operator_name}: {len(results)} results', type='positive')


def toggle_view_for_operator(view_type: str, operator_id: str, operator_name: str, results_area, results_state: ResultsViewState):
    """
    Toggle between grid and list view for a specific operator.
    
    Args:
        view_type: 'grid' or 'list'
        operator_id: ID of the operator
        operator_name: Name of the operator
        results_area: UI container for results
        results_state: Per-user results state instance
    """
    results_state.current_view = view_type
    logger.info(f"Toggled view to: {view_type} for operator: {operator_name}")
    
    # Re-render only the results display container with cached results
    if results_state.results_display_container and results_state.last_preview_results:
        results_state.results_display_container.clear()
        
        # Use cached results instead of re-executing
        with results_state.results_display_container:
            container = ui.element('div').classes('w-full')
            with container:
                if results_state.current_view == 'grid':
                    render_grid_view(results_state.last_preview_results)
                else:
                    render_list_view(results_state.last_preview_results)


def render_grid_view(results):
    """
    Render results in grid view (5 columns).
    
    Args:
        results: List of artwork dictionaries to display
    """
    
    # Grid with 5 columns
    with ui.element('div').classes('grid grid-cols-5 gap-4 w-full'):
        for result in results:
            # Truncate title to max 30 chars
            title = result['title']
            if len(title) > 30:
                title = title[:27] + '...'
            
            # Square tile with image and title below
            with ui.column().classes('gap-2 min-w-0'):
                # Image container with fixed aspect ratio - clickable
                with ui.card().classes('w-full p-0 overflow-hidden cursor-pointer hover:shadow-xl transition').style('aspect-ratio: 1/1;'):
                    img = ui.image(result.get('image_url', result.get('image', ''))).classes('w-full h-full object-cover')
                    img.on('click', lambda r=result: show_artwork_detail(r))
                
                # Metadata below image with truncation
                with ui.column().classes('gap-0 w-full min-w-0'):
                    ui.label(title).classes('text-sm font-bold text-gray-800 truncate')
                    ui.label(result['artist']).classes('text-xs text-gray-600 truncate')
                    ui.label(f"{result['year']} • {result['inventory']}").classes('text-xs text-gray-500 truncate')


def render_list_view(results):
    """
    Render results in list view (1 per row).
    
    Args:
        results: List of artwork dictionaries to display
    """
    
    with ui.column().classes('w-full gap-3'):
        for result in results:
            # List item card - clickable
            with ui.card().classes('w-full hover:shadow-lg transition cursor-pointer'):
                card_row = ui.row().classes('w-full items-center gap-4 p-2')
                card_row.on('click', lambda r=result: show_artwork_detail(r))
                
                with card_row:
                    # Square thumbnail (fixed size)
                    ui.image(result.get('image_url', result.get('image', ''))).classes('w-24 h-24 object-cover rounded')
                    
                    # Metadata (always visible)
                    with ui.column().classes('flex-1'):
                        ui.label(result['title']).classes('text-base font-bold text-gray-800')
                        ui.label(result['artist']).classes('text-sm text-gray-600')
                        with ui.row().classes('gap-2 mt-1'):
                            ui.badge(result['year']).props('color=grey')
                            ui.badge(result['inventory']).props(f'color=none').classes(f'bg-[{settings.primary_color}] text-white')


def clear_results(results_area):
    """
    Clear the results area.
    
    Args:
        results_area: UI container to clear
    """
    if results_area:
        results_area.clear()
