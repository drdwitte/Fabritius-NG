"""
Algorithm column header component with close button.

Renders a header bar for algorithm columns with:
- Title
- Result count badge
- Close button (X)
"""

from nicegui import ui
from typing import Callable


def render_algorithm_header(
    title: str,
    count: int,
    on_close: Callable,
    color: str = "amber-800"
) -> None:
    """
    Render an algorithm column header with title, badge, and close button.
    
    Args:
        title: Column title (e.g., "Text Embeddings")
        count: Number of results
        on_close: Callback when close button is clicked
        color: Tailwind color class for header background (default: amber-800 for Fabritius branding)
    """
    # Header bar with black styling (more compact to prevent wrapping)
    with ui.row().classes(f'w-full bg-gray-800 text-white px-3 py-2 rounded-t-lg items-center justify-between'):
        # Left side: Title and badge in one row
        with ui.row().classes('items-center gap-2 flex-1 min-w-0'):
            ui.label(title).classes('text-sm font-bold truncate')
            
            # Result count badge (compact version)
            if count > 0:
                with ui.element('div').classes('bg-white text-gray-800 px-2 py-0.5 rounded-full flex-shrink-0'):
                    ui.label(f'{count}').classes('text-xs font-semibold')
        
        # Right side: Close button (X)
        ui.button(
            icon='close',
            on_click=on_close
        ).props('flat dense round size=sm').classes('text-white flex-shrink-0').style('margin: -4px')
