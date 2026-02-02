"""
Label card view component.

Renders the label tag and definition display.
"""

from nicegui import ui
from typing import Callable, Optional


def render_label_card(
    label_name: str,
    label_definition: Optional[str],
    on_remove: Callable
) -> None:
    """
    Render the label tag with definition.
    
    Args:
        label_name: Name of the label
        label_definition: Definition text (optional)
        on_remove: Callback when remove button is clicked
    """
    with ui.row().classes('w-full items-start gap-2'):
        # Label tag with Fabritius colors (brown bg, white text)
        with ui.element('div').classes(
            'flex items-center gap-2 px-3 py-1 rounded-full '
            'bg-amber-900 text-white'
        ):
            ui.icon('local_offer').classes('text-sm')
            ui.label(label_name).classes('text-sm font-medium')
            
            # Remove button
            with ui.button(icon='close', on_click=on_remove).props('flat dense size=sm'):
                pass
    
    # Definition (if available)
    if label_definition:
        # Truncate to 100 characters
        truncated = label_definition[:100]
        if len(label_definition) > 100:
            truncated += "..."
        
        with ui.row().classes('w-full'):
            ui.label(truncated).classes('text-sm italic text-gray-600')
