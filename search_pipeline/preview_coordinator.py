"""
Preview coordinator for operator results.

This module coordinates the preview functionality for operators,
showing loading states, executing searches, and rendering results.

Now uses the Strategy pattern with OperatorFactory for cleaner,
more extensible operator handling.
"""

from nicegui import ui
from loguru import logger
from search_pipeline.operator_registry import OperatorRegistry


def show_preview_for_operator(operator_id: str, operator_name: str, controller):
    """
    Show results preview for a specific operator using Strategy pattern.
    
    This function now uses OperatorFactory to get the operator instance,
    eliminating the need for hardcoded if/else logic for each operator type.
    
    Args:
        operator_id: ID of the operator to preview
        operator_name: Name of the operator
        controller: SearchPageController instance with pipeline_state, ui_state, and results_state
    """
    logger.info(f"Showing preview for operator: {operator_name} (ID: {operator_id})")
    
    # Get operator params from pipeline state
    operator_data = None
    for op in controller.pipeline_state.get_all_operators():
        if op['id'] == operator_id:
            operator_data = op
            break
    
    if not operator_data:
        logger.error(f"Operator {operator_id} not found in pipeline")
        ui.notify('Operator not found', type='negative')
        return
    
    params = operator_data.get('params', {})
    
    # Clear results area immediately
    results_area = controller.ui_state.results_area
    if not results_area:
        return
    
    results_area.clear()
    
    # Get operator instance from factory (Strategy pattern)
    try:
        operator = OperatorRegistry.create(operator_name)
    except KeyError:
        logger.error(f"Unknown operator type: {operator_name}")
        with results_area:
            ui.label('⚠️ Unknown operator type').classes('text-red-600 font-medium')
        return
    
    # Check if operator is configured
    if not operator.is_configured(params):
        with results_area:
            ui.label(f'⚠️ {operator.get_unconfigured_message()}').classes('text-orange-600 font-medium')
            ui.label('Click the settings icon to add parameters').classes('text-sm text-gray-500 mt-2')
        return
    
    # Show loading spinner
    with results_area:
        with ui.row().classes('w-full items-center justify-center p-8 gap-3'):
            ui.spinner('dots', size='lg', color='primary')
            ui.label(operator.get_loading_message()).classes('text-gray-600 font-medium')
    
    # Execute operator asynchronously
    def execute_operator():
        try:
            # Execute the operator (polymorphism!)
            preview_results, total_count = operator.execute(params)
            
            # Update result count in pipeline state
            controller.pipeline_state.update_result_count(operator_id, total_count)
            
            # Re-render pipeline to show updated count
            from search_pipeline.views import pipeline_view
            pipeline_view.render_pipeline(controller)
            
            # Clear spinner and show results
            results_area.clear()
            
            if not preview_results:
                with results_area:
                    ui.label('No results found').classes('text-gray-600 font-medium')
                    ui.label('Try adjusting your parameters').classes('text-sm text-gray-500 mt-2')
                return
            
            # Render results with controller's results_state
            from search_pipeline.views import results_view
            results_view.render_results_ui(
                preview_results, 
                operator_id, 
                operator_name, 
                results_area,
                controller.results_state
            )
            
        except Exception as e:
            logger.error(f"Error executing operator {operator_name}: {e}")
            results_area.clear()
            with results_area:
                ui.label('⚠️ Error executing operator').classes('text-red-600 font-medium')
                ui.label(str(e)).classes('text-sm text-gray-500 mt-2')
    
    # Execute after short delay to let UI update
    ui.timer(0.1, execute_operator, once=True)
