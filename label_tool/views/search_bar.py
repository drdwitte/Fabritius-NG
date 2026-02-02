"""
Search bar view component for label validation.

Renders the thesaurus selector, algorithm menu, and search controls.
"""

from nicegui import ui
from typing import Callable
from loguru import logger
import asyncio

from ui_components.buttons import icon_button, run_button
from label_tool.thesaurus_registry import get_thesaurus_names
from label_tool.algorithm_registry import get_algorithm_names
from label_tool.level_config import get_enabled_levels


def render_search_input(
    label_name: str,
    on_clear: Callable
) -> None:
    """
    Render the search input or label tag.
    
    Args:
        label_name: Current label name (None if no label selected)
        on_clear: Callback when label is cleared
    """
    if label_name:
        # Show label tag with Fabritius colors (brown background, white text)
        with ui.element('div').classes('flex items-center gap-2 bg-amber-900 text-white px-3 py-1 rounded'):
            ui.icon('local_offer').classes('text-white text-sm')
            ui.label(label_name).classes('font-semibold')
            ui.button(icon='close', on_click=on_clear).props('flat dense round size=sm').classes('text-white')
    else:
        # Show input field when no label is selected
        ui.input(
            placeholder='Free (semantic) text search, or use the buttons on the right to limit the search to a thesaurus or create and define your own label', 
            value=''
        ).props('borderless dense').classes('flex-grow')


def render_search_bar(
    selected_thesaurus: str,
    selected_algorithms: list,
    selected_levels: list,
    label_name: str,
    on_thesaurus_change: Callable,
    on_new_label_click: Callable,
    on_algorithm_toggle: Callable,
    on_level_toggle: Callable,
    on_search_click: Callable,
    on_clear_label: Callable
) -> None:
    """
    Render the search bar with thesaurus selector and controls.
    
    Args:
        selected_thesaurus: Currently selected thesaurus name
        selected_algorithms: List of selected algorithm names
        selected_levels: List of selected validation level names
        label_name: Current label name (None if no label)
        on_thesaurus_change: Callback when thesaurus is changed
        on_new_label_click: Callback when New Label button is clicked
        on_algorithm_toggle: Callback when algorithm is toggled
        on_level_toggle: Callback when validation level is toggled
        on_search_click: Callback when Search button is clicked
        on_clear_label: Callback when label is cleared
    """
    # Top bar: full width, left input, right buttons
    with ui.row().props('flat').classes('w-full flex items-center justify-between'):
        # Left: search container with tag or input
        with ui.element('div').classes('flex-grow flex items-center gap-2 min-h-9'):
            render_search_input(label_name, on_clear_label)
        
        # Right: action buttons
        with ui.row().classes('gap-2'):
            # Thesaurus selector with icon_button style
            with ui.element('div').classes('relative'):
                thesaurus_btn = ui.button(on_click=lambda: None)
                thesaurus_btn.props('color=none text-color=none')
                thesaurus_btn.classes('h-9 px-3 flex items-center gap-x-8 rounded-md '
                                     'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 py-1')
                with thesaurus_btn:
                    ui.icon('book').classes('text-gray-700 text-lg')
                    ui.label(selected_thesaurus or 'Thesaurus').classes('text-gray-700 text-base font-bold').style('text-transform: none; margin-left: 10px;')
                    with ui.menu():
                        ui.menu_item('None (Free search)', on_click=lambda: on_thesaurus_change(None))
                        ui.separator()
                        for thesaurus_name in get_thesaurus_names():
                            ui.menu_item(
                                thesaurus_name,
                                on_click=lambda t=thesaurus_name: on_thesaurus_change(t)
                            )
            
            # New Label button
            icon_button('add', 'New Label', on_new_label_click)
            
            # Search button with algorithm selector dropdown
            with ui.element('div').classes('relative'):
                search_btn = run_button('Search', lambda: None)
                with search_btn:
                    with ui.menu() as search_menu:
                        with ui.card().classes('p-4'):
                            # Text/Multimodal Embeddings section
                            ui.label('Embeddings').classes('text-sm font-bold mb-2 text-gray-700')
                            ui.label('(Select max 2)').classes('text-xs text-gray-500 mb-2')
                            
                            for algo_name in get_algorithm_names():
                                is_selected = algo_name in selected_algorithms
                                is_disabled = not is_selected and len(selected_algorithms) >= 2
                                ui.checkbox(
                                    algo_name, 
                                    value=is_selected,
                                    on_change=lambda e, a=algo_name: on_algorithm_toggle(a, e.value)
                                ).classes('mb-2').props('disable' if is_disabled else '')
                            
                            ui.separator().classes('my-3')
                            
                            # Human Labels section
                            ui.label('Human Labels').classes('text-sm font-bold mb-2 text-gray-700')
                            
                            # Show AI, HUMAN, EXPERT checkboxes
                            from label_tool.level_config import VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT
                            
                            validation_levels = [
                                (VALIDATION_LEVEL_AI, 'AI'),
                                (VALIDATION_LEVEL_HUMAN, 'Human'),
                                (VALIDATION_LEVEL_EXPERT, 'Expert')
                            ]
                            
                            for level_key, level_display in validation_levels:
                                is_selected = level_key in selected_levels
                                ui.checkbox(
                                    level_display, 
                                    value=is_selected,
                                    on_change=lambda e, l=level_key: on_level_toggle(l, e.value)
                                ).classes('mb-2')
                            
                            ui.separator().classes('my-3')
                            
                            # Run button inside menu
                            with ui.row().classes('justify-end w-full'):
                                async def run_search():
                                    search_menu.close()
                                    await on_search_click()
                                
                                ui.button('Run Search', on_click=run_search).props('color=primary')



