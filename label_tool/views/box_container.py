"""
Box container views for label validation.

Renders result boxes (validated level boxes and algorithm boxes).
Follows the thin coordinator pattern - contains only UI rendering logic.
"""

from nicegui import ui
from loguru import logger
from typing import Callable, Optional

from ..level_config import VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT
from .column_header import render_column_header
from .algorithm_header import render_algorithm_header
from .action_bar import render_action_bar
from .result_cards import render_view_toggle, render_result_grid_view, render_result_list_view


def render_result_box(
    box_key: str,
    label: str,
    color: str,
    results,
    state,
    show_label: bool = False,
    subtitle: Optional[str] = None,
    on_toggle_collapse: Optional[Callable] = None,
    on_select_all: Optional[Callable] = None,
    on_deselect_all: Optional[Callable] = None,
    on_toggle_selection: Optional[Callable[[str], None]] = None,
    on_promote: Optional[Callable] = None,
    on_demote: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_hide: Optional[Callable] = None,
    on_toggle_view: Optional[Callable[[str], None]] = None
):
    """
    Render a result box with column header and results.
    
    Used for validated level boxes (AI, HUMAN, EXPERT) with collapse functionality.
    
    Args:
        box_key: Unique identifier for the box
        label: Display label for the box
        color: Color scheme (not used directly, derived from box type)
        results: ValidationResults object with artwork data
        state: LabelState object for accessing view mode and selection state
        show_label: Whether to show label info (currently unused)
        subtitle: Optional subtitle text
        on_toggle_collapse: Callback when collapse button is clicked
        on_select_all: Callback to select all artworks
        on_deselect_all: Callback to deselect all artworks
        on_toggle_selection: Callback when artwork selection is toggled (receives artwork_id)
        on_promote: Callback to promote selected artworks
        on_demote: Callback to demote selected artworks
        on_delete: Callback to delete selected artworks
        on_hide: Callback to hide selected artworks
        on_toggle_view: Callback when view mode is toggled (receives view_mode)
    """
    is_ai_column = box_key.startswith("AI-") and box_key not in [VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT]
    is_validated_column = box_key in [VALIDATION_LEVEL_AI, VALIDATION_LEVEL_HUMAN, VALIDATION_LEVEL_EXPERT]
    
    # Check if column is collapsed
    is_collapsed = not state.is_box_open(box_key)
    
    # Determine grid columns and max items based on row type
    grid_cols = None
    max_items = None
    
    if is_ai_column:
        # AI Results row: varies by algorithm count
        num_algorithms = len(state.selected_algorithms) if state.selected_algorithms else 1
        if num_algorithms == 1:
            # 1 algorithm: 5 columns x 2 rows = 10 items
            grid_cols = 5
            max_items = 10
        else:
            # 2 algorithms: 3 columns x 2 rows = 6 items per algorithm
            grid_cols = 3
            max_items = 6
    elif is_validated_column:
        # Validated rows (AI/HUMAN/EXPERT): always 5 columns x 2 rows = 10 items
        grid_cols = 5
        max_items = 10
    
    # Determine header color based on column type
    if is_ai_column:
        # For AI algorithm columns, use different colors for each algorithm
        if state.selected_algorithms:
            algo_index = None
            for i, algo in enumerate(state.selected_algorithms):
                if box_key == f"AI-{algo}":
                    algo_index = i
                    break
            
            if algo_index == 0:
                header_color = "rose-600"     # Rose for first algorithm
            elif algo_index == 1:
                header_color = "emerald-600"  # Emerald for second algorithm
            else:
                header_color = "purple-700"   # Fallback purple
        else:
            header_color = "purple-700"       # Default purple if no algorithms
    elif box_key == VALIDATION_LEVEL_AI:
        header_color = "purple-600"  # Purple for AI validated
    elif box_key == VALIDATION_LEVEL_HUMAN:
        header_color = "blue-600"    # Blue for Human
    elif box_key == VALIDATION_LEVEL_EXPERT:
        header_color = "amber-700"   # Amber for Expert (Fabritius branding)
    elif box_key == "":
        header_color = "gray-400"    # Light gray for empty AI Results (no algorithm selected)
    else:
        header_color = "amber-800"   # Default Fabritius brown
    
    with ui.column().classes('flex-1 bg-white rounded-lg shadow-md overflow-hidden'):
        # Column header with title, count badge, and collapse button
        # Count only visible (non-hidden) results
        if results:
            visible_count = len([r for r in results.results if not r.get('_hidden', False)])
        else:
            visible_count = 0
        
        render_column_header(
            title=label,
            count=visible_count,
            is_collapsed=is_collapsed,
            on_toggle_collapse=on_toggle_collapse,
            color=header_color,
            subtitle=subtitle,
            on_select_all=on_select_all,
            on_deselect_all=on_deselect_all
        )
        
        # Content area with smooth collapse animation
        content_height = '0px' if is_collapsed else 'none'
        overflow_class = 'overflow-hidden' if is_collapsed else ''
        with ui.column().classes(f'{overflow_class} transition-all duration-500 ease-in-out').style(f'max-height: {content_height};' if is_collapsed else ''):
            with ui.column().classes('p-4'):
                # Get selection state for action bar
                selected_ids = state.get_selected_artworks(box_key)
                selected_count = len(selected_ids)
                
                # Action bar (shown when items are selected)
                if selected_count > 0:
                    # Determine promote/demote availability based on level
                    can_promote = box_key not in ['EXPERT']
                    can_demote = box_key not in ['AI', 'AI-Text Embeddings', 'AI-Image Embeddings']
                    
                    render_action_bar(
                        selected_count=selected_count,
                        can_promote=can_promote,
                        can_demote=can_demote,
                        on_promote=on_promote,
                        on_demote=on_demote,
                        on_delete=on_delete,
                        on_hide=on_hide
                    )
                
                # View toggle in top right
                with ui.row().classes('w-full items-center justify-end mb-4'):
                    render_view_toggle(
                        current_view=state.view_mode,
                        on_toggle_view=on_toggle_view
                    )
                
                # Results area
                if results and results.results:
                    # Filter out hidden artworks (marked with _hidden flag)
                    visible_results = [r for r in results.results if not r.get('_hidden', False)]
                    
                    # Limit results based on max_items
                    display_results = visible_results[:max_items] if max_items else visible_results
                    
                    logger.info(f"Rendering {len(display_results)} results for {box_key}, view mode: {state.view_mode}")
                    
                    if state.view_mode == 'grid':
                        render_result_grid_view(
                            display_results, 
                            is_ai_column=is_ai_column, 
                            grid_cols=grid_cols,
                            column_key=box_key,
                            selected_ids=selected_ids,
                            on_toggle_selection=lambda aid: on_toggle_selection(aid) if on_toggle_selection else None
                        )
                    else:
                        render_result_list_view(
                            display_results, 
                            is_ai_column=is_ai_column,
                            column_key=box_key,
                            selected_ids=selected_ids,
                            on_toggle_selection=lambda aid: on_toggle_selection(aid) if on_toggle_selection else None
                        )
                else:
                    ui.label('No results').classes('text-gray-500 italic')


def render_algorithm_box(
    box_key: str,
    label: str,
    color: str,
    results,
    state,
    on_close: Optional[Callable] = None,
    on_toggle_selection: Optional[Callable[[str], None]] = None,
    on_promote: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_hide: Optional[Callable] = None,
    on_toggle_view: Optional[Callable[[str], None]] = None
):
    """
    Render an algorithm box with close button instead of collapse.
    
    Used for AI algorithm boxes (e.g., "AI-Text", "AI-Multimodal") in the AI Results row.
    
    Args:
        box_key: Unique identifier for the box
        label: Display label for the box
        color: Header color (rose-600 for first algo, emerald-600 for second)
        results: ValidationResults object with artwork data
        state: LabelState object for accessing view mode and selection state
        on_close: Callback when close (X) button is clicked
        on_toggle_selection: Callback when artwork selection is toggled (receives artwork_id)
        on_promote: Callback to promote selected artworks
        on_delete: Callback to delete selected artworks
        on_hide: Callback to hide selected artworks
        on_toggle_view: Callback when view mode is toggled (receives view_mode)
    """
    is_ai_column = True
    
    # Determine grid columns and max items for AI columns
    num_algorithms = len(state.selected_algorithms) if state.selected_algorithms else 1
    if num_algorithms == 1:
        grid_cols = 5
        max_items = 10
    else:
        grid_cols = 3
        max_items = 6
    
    # Use flex-1 for responsive width distribution
    width_class = 'flex-1'
    
    with ui.column().classes(f'{width_class} bg-white rounded-lg shadow-md overflow-hidden'):
        # Algorithm header with close button (X)
        # Count only visible (non-hidden) results
        if results:
            visible_count = len([r for r in results.results if not r.get('_hidden', False)])
        else:
            visible_count = 0
        
        render_algorithm_header(
            title=label,
            count=visible_count,
            on_close=on_close,
            color=color
        )
        
        # Content always visible (no collapse for algorithms)
        with ui.column().classes('p-4'):
            # Get selection state for action bar
            selected_ids = state.get_selected_artworks(box_key)
            selected_count = len(selected_ids)
            
            # Action bar (shown when items are selected)
            if selected_count > 0:
                # Algorithm columns can always promote (to HUMAN), never demote
                render_action_bar(
                    selected_count=selected_count,
                    can_promote=True,
                    can_demote=False,
                    on_promote=on_promote,
                    on_demote=None,
                    on_delete=on_delete,
                    on_hide=on_hide
                )
            
            # View toggle in top right
            with ui.row().classes('w-full items-center justify-end mb-4'):
                render_view_toggle(
                    current_view=state.view_mode,
                    on_toggle_view=on_toggle_view
                )
            
            # Results area
            if results and results.results:
                # Filter out hidden artworks (marked with _hidden flag)
                visible_results = [r for r in results.results if not r.get('_hidden', False)]
                
                # Limit results based on max_items
                display_results = visible_results[:max_items] if max_items else visible_results
                
                logger.info(f"Rendering {len(display_results)} algo results for {box_key}, view mode: {state.view_mode}")
                
                if state.view_mode == 'grid':
                    render_result_grid_view(
                        display_results, 
                        is_ai_column=is_ai_column, 
                        grid_cols=grid_cols,
                        column_key=box_key,
                        selected_ids=selected_ids,
                        on_toggle_selection=lambda aid: on_toggle_selection(aid) if on_toggle_selection else None
                    )
                else:
                    render_result_list_view(
                        display_results, 
                        is_ai_column=is_ai_column,
                        column_key=box_key,
                        selected_ids=selected_ids,
                        on_toggle_selection=lambda aid: on_toggle_selection(aid) if on_toggle_selection else None
                    )
            else:
                ui.label('No results').classes('text-gray-500 italic')
