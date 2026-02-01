"""
Pipeline view component.

This module handles the rendering of the operator pipeline chain,
including operator tiles with reordering via arrow buttons.
"""

from nicegui import ui
from loguru import logger
from config import settings
from search_pipeline.operator_registry import OperatorRegistry
from search_pipeline.preview_coordinator import show_preview_for_operator
from search_pipeline.views.config_panel import show_operator_config

def render_pipeline(controller):
    """
    Renders the pipeline area with all operators as tiles.
    
    Args:
        controller: SearchPageController instance with pipeline_state and ui_state
    """
    pipeline = controller.pipeline_state.get_all_operators()  # Get the current pipeline

    # Clear the pipeline area before re-rendering
    if controller.ui_state.pipeline_area is not None:
        controller.ui_state.pipeline_area.clear()

    # Create a new container for the pipeline
    with controller.ui_state.pipeline_area:
        pipeline_container = (
            ui.element('div')
            .classes('flex items-start gap-4 bg-white p-4 rounded')
        )

        with pipeline_container:
            for op_data in pipeline:
                op_id = op_data['id']
                op_name = op_data['name']
                operator = OperatorRegistry.get_metadata(op_name)
                icon = operator['icon']

                # Create a tile for the operator
                tile = (ui.element('div')
                    .classes('flex flex-col gap-0 px-2 py-2 rounded-xl bg-white shadow-sm min-w-[180px] hover:shadow-md transition')
                )

                with tile:
                    with ui.row().classes('items-center w-full'):
                        # Reorder buttons (left/right arrows)
                        with ui.row().classes('gap-0'):
                            # Left arrow (disabled if first operator)
                            ui.icon('chevron_left').classes('text-lg text-gray-400 cursor-pointer hover:text-gray-700').on(
                                'click', lambda _, op_id=op_id: controller.move_operator_left(op_id)
                            ).tooltip('Move Left')

                            # Right arrow (disabled if last operator)
                            ui.icon('chevron_right').classes('text-lg text-gray-400 cursor-pointer hover:text-gray-700').on(
                                'click', lambda _, op_id=op_id: controller.move_operator_right(op_id)
                            ).tooltip('Move Right')
                        
                        # Operator icon and name
                        ui.icon(icon).classes('text-xl text-gray-700 ml-2')
                        ui.label(op_name).classes('text-gray-800 font-medium ml-2')
                        
                        # Preview icon to show results for this operator
                        ui.icon('visibility').classes(f'text-xl text-[{settings.primary_color}] cursor-pointer ml-auto').on(
                            'click', lambda _, op_id=op_id, name=op_name: show_preview_for_operator(
                                operator_id=op_id,
                                operator_name=name,
                                controller=controller
                            )
                        ).tooltip('Preview Results')
                        
                        # Settings icon to configure operator
                        ui.icon('settings').classes('text-xl text-gray-700 cursor-pointer').on(
                            'click', lambda _, op_id=op_id: show_operator_config(
                                op_id,
                                controller.pipeline_state,
                                controller.ui_state,
                                controller.ui_state.pipeline_area,
                                lambda: render_pipeline(controller)
                            )
                        ).tooltip('Configure')
                        
                        # Delete icon
                        ui.icon('delete').classes('text-xl text-red-500 cursor-pointer').on(
                            'click', lambda _, op_id=op_id, name=op_name, t=tile: controller.delete_operator(op_id, name, t)
                        ).tooltip('Delete')

                    # Show actual operator parameters
                    params = op_data.get('params', {})
                    if params:
                        for param_name, param_value in list(params.items())[:settings.max_visible_params]:
                            # Format the value nicely
                            if isinstance(param_value, dict) and 'filename' in param_value:
                                # For image type, show filename only (not base64 data)
                                display_value = f'📷 {param_value["filename"]}'
                            elif isinstance(param_value, list):
                                if all(isinstance(x, (int, float)) for x in param_value):
                                    # Convert to int for year ranges to avoid .0 display
                                    val0 = int(param_value[0]) if param_value[0] is not None else None
                                    val1 = int(param_value[1]) if param_value[1] is not None else None
                                    display_value = f"{val0} - {val1}"
                                else:
                                    display_value = ', '.join(str(v) for v in param_value[:3])
                                    if len(param_value) > 3:
                                        display_value += '...'
                            elif isinstance(param_value, float) and param_value.is_integer():
                                # Convert float to int if it has no decimal part (e.g., 15.0 -> 15)
                                display_value = str(int(param_value))
                            else:
                                display_value = str(param_value)[:30]
                            ui.label(f"{param_name}: {display_value}").classes('text-sm text-gray-400 italic w-full leading-tight mt-1')
                    else:
                        ui.label("No filters applied").classes('text-sm text-gray-400 italic w-full mt-2')
                    
                    # Show result count (None = not executed yet, int = actual count)
                    result_count = op_data.get('result_count')
                    if result_count is None:
                        count_text = "? results"
                    else:
                        count_text = f"{result_count} results"
                    
                    ui.label(count_text).classes(
                        f'inline-block mt-3 px-2 py-1 text-xs font-medium rounded-md bg-[{settings.primary_color}] text-white'
                    )

    # No JavaScript needed - reordering handled by Python buttons
