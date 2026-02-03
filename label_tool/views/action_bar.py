"""
Action bar component for bulk operations on selected artworks.

Shows promote, demote, delete, and hide buttons when artworks are selected.
"""

from nicegui import ui
from typing import Callable, Optional


def render_action_bar(
    selected_count: int,
    can_promote: bool = True,
    can_demote: bool = True,
    on_promote: Optional[Callable] = None,
    on_demote: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_hide: Optional[Callable] = None
) -> None:
    """
    Render an action bar with bulk operation buttons.
    
    Only shown when selected_count > 0.
    
    Args:
        selected_count: Number of selected artworks
        can_promote: Whether promote action is available (e.g., EXPERT row can't be promoted)
        can_demote: Whether demote action is available (e.g., AI Results can't be demoted)
        on_promote: Callback for promote action (move to next level)
        on_demote: Callback for demote action (move to previous level)
        on_delete: Callback for delete action (remove label)
        on_hide: Callback for hide action (replace with next results)
    """
    if selected_count == 0:
        return
    
    # Action bar with blue background
    with ui.row().classes('w-full bg-blue-100 border border-blue-300 rounded-lg px-4 py-3 items-center justify-between shadow-md'):
        # Left side: Selection count
        with ui.row().classes('items-center gap-2'):
            ui.icon('check_circle').classes('text-blue-600')
            ui.label(f'{selected_count} selected').classes('text-blue-900 font-semibold')
        
        # Right side: Action buttons
        with ui.row().classes('items-center gap-2'):
            # Demote button (arrow up)
            if can_demote and on_demote:
                ui.button(
                    icon='arrow_upward',
                    on_click=on_demote
                ).props('flat').classes('text-blue-700').tooltip('Demote to previous level')
            
            # Promote button (arrow down)
            if can_promote and on_promote:
                ui.button(
                    icon='arrow_downward',
                    on_click=on_promote
                ).props('flat').classes('text-blue-700').tooltip('Promote to next level')
            
            # Delete button (trash)
            if on_delete:
                ui.button(
                    icon='delete',
                    on_click=on_delete
                ).props('flat').classes('text-red-600').tooltip('Delete labels')
            
            # Hide button (eye off)
            if on_hide:
                ui.button(
                    icon='visibility_off',
                    on_click=on_hide
                ).props('flat').classes('text-gray-600').tooltip('Hide and replace with next results')
