"""
Column header component with collapse/expand functionality.

Renders a header bar for result columns with:
- Title
- Result count badge
- Collapse/expand button
"""

from nicegui import ui
from typing import Callable


def render_column_header(
    title: str,
    count: int,
    is_collapsed: bool,
    on_toggle_collapse: Callable,
    color: str = "amber-800",
    subtitle: str = None,
    has_selection: bool = False,
    on_select_all: Callable = None,
    on_deselect_all: Callable = None
) -> None:
    """
    Render a column header with title, badge, and collapse button.
    
    Args:
        title: Column title (e.g., "Text Embeddings")
        count: Number of results
        is_collapsed: Whether column is currently collapsed
        on_toggle_collapse: Callback when collapse button is clicked
        color: Tailwind color class for header background (default: amber-800 for Fabritius branding)
        subtitle: Optional subtitle text to display below title in smaller italic text
        has_selection: Whether any items are selected in this column
        on_select_all: Callback to select all items in column
        on_deselect_all: Callback to deselect all items in column
    """
    # Header bar with Fabritius brown/amber styling
    with ui.row().classes(f'w-full bg-{color} text-white px-4 py-3 rounded-t-lg items-center justify-between'):
        # Left side: Title and subtitle
        with ui.column().classes('gap-0 flex-1 min-w-0'):
            ui.label(title).classes('text-base font-bold')
            
            # Subtitle below title if provided
            if subtitle:
                ui.label(subtitle).classes('text-xs italic opacity-90 mt-0.5')
        
        # Right side: Badge, selection buttons, and collapse/expand button
        with ui.row().classes('items-center gap-3 flex-shrink-0'):
            # Select all / Deselect all buttons (only if callbacks provided)
            if on_select_all and on_deselect_all:
                ui.button(
                    icon='check_box',
                    on_click=on_select_all
                ).props('flat dense').classes('text-white').tooltip('Select all')
                
                ui.button(
                    icon='check_box_outline_blank',
                    on_click=on_deselect_all
                ).props('flat dense').classes('text-white').tooltip('Deselect all')
            
            # Result count badge (white background for contrast)
            if count > 0:
                artwork_text = 'artwork' if count == 1 else 'artworks'
                with ui.element('div').classes('bg-white text-amber-900 px-2.5 py-0.5 rounded-full'):
                    ui.label(f'{count} {artwork_text}').classes('text-sm font-semibold')
            
            # Collapse/expand button
            icon = 'remove' if not is_collapsed else 'add'
            ui.button(
                icon=icon,
                on_click=on_toggle_collapse
            ).props('flat dense round').classes('text-white').style('margin: -8px')  # Negative margin for better alignment
