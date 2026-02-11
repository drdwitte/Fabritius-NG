"""
Row container views for label validation.

Renders full-width row containers (AI Results row and validated level rows).
Follows the thin coordinator pattern - contains only UI rendering logic.
"""

from nicegui import ui
from loguru import logger
from typing import Callable, Optional, List

from ..state import ValidationResults
from .column_header import render_column_header
from .box_container import render_algorithm_box, render_result_box


def render_ai_results_row(controller):
    """
    Render AI Results as a collapsible row containing algorithm columns.
    
    This is the top row showing results from multiple AI algorithms side-by-side.
    Each algorithm (e.g., Text Embeddings, Image Embeddings) gets its own column.
    
    Args:
        controller: LabelPageController with state and callback methods
    """
    state = controller.state
    box_key = "AI_RESULTS"
    is_collapsed = not state.is_box_open(box_key)
    
    with ui.element('div').classes('w-full mb-4'):
        # Main header with collapse
        with ui.column().classes('w-full bg-white rounded-lg shadow-md overflow-hidden'):
            # AI Results header (gray-600 color)
            # Count total visible results across all algorithm columns
            total_results = 0
            for algo_name in state.selected_algorithms:
                algo_box_key = f"AI-{algo_name}"
                algo_results = state.results_per_box.get(algo_box_key)
                if algo_results:
                    total_results += len([r for r in algo_results.results if not r.get('_hidden', False)])
            
            render_column_header(
                title="AI Results",
                count=total_results,
                is_collapsed=is_collapsed,
                on_toggle_collapse=lambda: controller.toggle_box("AI_RESULTS"),
                color="gray-600",
                subtitle="Labels suggested by AI to be validated",
                on_select_all=None,  # No select all for AI Results section (each algorithm has its own)
                on_deselect_all=None
            )
            
            # Collapsible content area
            content_height = '0px' if is_collapsed else 'none'
            overflow_class = 'overflow-hidden' if is_collapsed else ''
            with ui.column().classes(f'{overflow_class} transition-all duration-500 ease-in-out').style(f'max-height: {content_height};' if is_collapsed else ''):
                with ui.column().classes('p-4'):
                    # Algorithm columns in a row
                    with ui.row().classes('w-full gap-4'):
                        for i, algo_name in enumerate(state.selected_algorithms):
                            algo_box_key = f"AI-{algo_name}"
                            algo_color = "rose-600" if i == 0 else "emerald-600"
                            
                            # Render algorithm box with close button
                            algo_results = state.results_per_box.get(algo_box_key)
                            render_algorithm_box(
                                box_key=algo_box_key,
                                label=f"{algo_name} Embeddings",
                                color=algo_color,
                                results=algo_results,
                                state=state,
                                on_close=lambda a=algo_name: controller.close_algorithm(a),
                                on_toggle_selection=lambda aid, bk=algo_box_key: (controller.state.toggle_artwork_selection(bk, aid), controller.update_boxes()),
                                on_promote=lambda bk=algo_box_key: controller.promote_selected(bk),
                                on_delete=lambda bk=algo_box_key: controller.delete_selected(bk),
                                on_hide=lambda bk=algo_box_key: controller.hide_selected(bk),
                                on_toggle_view=lambda vm: (setattr(controller.state, 'view_mode', vm), controller.update_boxes())
                            )


def render_validated_row(
    controller,
    box_key: str,
    row_label: str,
    subtitle: str,
    color: str
):
    """
    Render a validated level row (AI, HUMAN, or EXPERT).
    
    These are full-width rows showing artworks at a specific validation level.
    
    Args:
        controller: LabelPageController with state and callback methods
        box_key: Unique identifier for the level (e.g., "AI", "HUMAN", "EXPERT")
        row_label: Display label for the row
        subtitle: Subtitle text describing the validation level
        color: Color scheme (not used directly, derived in render_result_box)
    """
    state = controller.state
    # Always render result box (header stays visible when collapsed)
    box_results = state.results_per_box.get(box_key)
    with ui.element('div').classes('w-full mb-4'):
        render_result_box(
            box_key=box_key,
            label=row_label,
            color=color,
            results=box_results,
            state=state,
            show_label=False,
            subtitle=subtitle,
            on_toggle_collapse=lambda: controller.toggle_box(box_key),
            on_select_all=lambda: (controller.state.select_all_artworks(box_key), controller.update_boxes()),
            on_deselect_all=lambda: (controller.state.deselect_all_artworks(box_key), controller.update_boxes()),
            on_toggle_selection=lambda aid: (controller.state.toggle_artwork_selection(box_key, aid), controller.update_boxes()),
            on_promote=lambda: controller.promote_selected(box_key),
            on_demote=lambda: controller.demote_selected(box_key),
            on_delete=lambda: controller.delete_selected(box_key),
            on_hide=lambda: controller.hide_selected(box_key),
            on_toggle_view=lambda vm: (setattr(controller.state, 'view_mode', vm), controller.update_boxes())
        )
