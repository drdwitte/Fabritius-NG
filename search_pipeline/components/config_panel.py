"""
Operator configuration panel component.

This module handles the rendering of the configuration panel for operators,
including both dynamic filter UI (for Metadata Filter) and static form UI
(for other operators like Semantic Search and Similarity Search).
"""

import base64
from nicegui import ui
from loguru import logger
from config import settings
import search_pipeline.operator_registration  # noqa: F401 - ensures operators are registered
from search_pipeline.operator_registry import OperatorRegistry


def show_operator_config(operator_id: str, pipeline_state, ui_state, pipeline_area, render_pipeline_func):
    """
    Shows a configuration panel for the selected operator.
    For operators with multiple filter options, allows dynamic adding/removing of filters.
    Loads existing parameters from the operator state.
    
    Args:
        operator_id: ID of the operator to configure
        pipeline_state: PipelineState instance
        ui_state: UIState instance with config_panel attribute
        pipeline_area: UI container for the pipeline
        render_pipeline_func: Function to re-render the pipeline
    
    Returns:
        ui.column: The configuration panel
    """
    # Get the operator data from state
    operator_data = pipeline_state.get_operator(operator_id)
    if not operator_data:
        ui.notify('Operator not found')
        return
    
    op_name = operator_data['name']
    existing_params = operator_data.get('params', {})
    
    # Remove existing panel completely if it exists
    if ui_state.config_panel:
        try:
            ui_state.config_panel.delete()
        except RuntimeError:
            # Parent slot was already deleted (e.g., after render_pipeline was called)
            pass
        ui_state.config_panel = None
    
    # Create new panel
    config_panel = ui.column().classes(
        'fixed right-0 top-0 h-screen w-96 bg-white shadow-2xl p-6 border-l border-gray-200 z-50 overflow-y-auto'
    )
    ui_state.config_panel = config_panel
    
    def close_panel():
        """Completely remove the config panel"""
        if ui_state.config_panel:
            try:
                ui_state.config_panel.delete()
            except RuntimeError:
                # Parent slot was already deleted
                pass
            ui_state.config_panel = None
    
    with config_panel:
        # Header with close button
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label(f'Configure {op_name}').classes('text-xl font-bold')
            ui.button(icon='close', on_click=close_panel).props('flat round dense')
        
        # Get operator info
        operator = OperatorRegistry.get_metadata(op_name)
        
        # Operator icon and description
        with ui.row().classes('items-center gap-3 mb-6 p-3 bg-gray-50 rounded-lg'):
            ui.icon(operator.get('icon', 'tune')).classes(f'text-2xl text-[{settings.primary_color}]')
            ui.label(operator.get('description', 'No description')).classes('text-sm text-gray-600')
        
        # Parameters section
        params_schema = operator.get('params', {})
        
        if params_schema:
            # Determine UI pattern: Metadata Filter uses dynamic filters, others use static form
            use_dynamic_filters = (op_name == 'Metadata Filter')
            
            if use_dynamic_filters:
                # DYNAMIC FILTER UI (Metadata Filter)
                render_dynamic_filter_ui(
                    params_schema, existing_params, operator_id, op_name, 
                    close_panel, pipeline_state, pipeline_area, render_pipeline_func
                )
            else:
                # STATIC FORM UI (Semantic Search, Similarity Search, etc.)
                render_static_form_ui(
                    params_schema, existing_params, operator_id, op_name, 
                    close_panel, pipeline_state, pipeline_area, render_pipeline_func
                )
        else:
            # No parameters defined for this operator
            ui.label('No parameters available for this operator.').classes('text-sm text-gray-500 italic')
    
    return config_panel


def render_dynamic_filter_ui(params_schema, existing_params, operator_id, op_name, close_panel, 
                            pipeline_state, pipeline_area, render_pipeline_func):
    """Renders dynamic filter UI for Metadata Filter"""
    ui.label('PARAMETERS').classes('text-sm font-bold text-gray-600 mb-3')
    
    # Container for active filters
    filters_container = ui.column().classes('w-full gap-2 mb-4')
    
    # Track active filters: list of dicts with {param_name, container, inputs}
    active_filters = []
    
    def create_filter_row(param_name=None):
        """Creates a new filter row with dropdown and input"""
        filter_row = ui.row().classes('w-full items-start gap-2 p-3 bg-gray-50 rounded border border-gray-200')
        
        with filter_row:
            filter_data = {'container': filter_row, 'inputs': {}}
            
            with ui.column().classes('flex-1 gap-2'):
                # Dropdown to select filter type
                filter_options = [
                    (name, config.get('label', name)) 
                    for name, config in params_schema.items()
                ]
                
                selected_param = param_name or list(params_schema.keys())[0]
                filter_select = ui.select(
                    options={name: label for name, label in filter_options},
                    value=selected_param,
                    label='Filter Type'
                ).classes('w-full')
                
                filter_data['param_select'] = filter_select
                
                # Container for the input field (will be updated based on selection)
                input_container = ui.column().classes('w-full')
                filter_data['input_container'] = input_container
                
                def update_input_field():
                    """Updates the input field based on selected filter type"""
                    input_container.clear()
                    current_param = filter_select.value
                    param_config = params_schema.get(current_param, {})
                    param_type = param_config.get('type')
                    default = param_config.get('default')
                    
                    with input_container:
                        if param_type == 'text':
                            filter_data['inputs']['value'] = ui.input(
                                placeholder=f'Enter value',
                                value=default or ''
                            ).classes('w-full')
                        
                        elif param_type == 'textarea':
                            filter_data['inputs']['value'] = ui.textarea(
                                placeholder=f'Enter value',
                                value=default or ''
                            ).classes('w-full').props('rows=5')
                        
                        elif param_type == 'image':
                            # Image upload field with preview
                            filter_data['inputs']['filename'] = None
                            filter_data['inputs']['image_data'] = None
                            
                            # Container for image preview
                            preview_container = ui.column().classes('w-full')
                            filter_data['preview_container'] = preview_container
                            
                            async def handle_upload(e):
                                """Handle image upload"""
                                content = await e.file.read()
                                filename = e.file.name
                                filter_data['inputs']['filename'] = filename
                                filter_data['inputs']['image_data'] = content
                                
                                # Update preview
                                preview_container.clear()
                                with preview_container:
                                    with ui.row().classes('w-full items-center gap-2'):
                                        # Show thumbnail using base64 encoding
                                        b64_data = base64.b64encode(content).decode()
                                        ui.image(f'data:image/png;base64,{b64_data}').classes('w-24 h-24 object-cover rounded border')
                                        with ui.column().classes('flex-1'):
                                            ui.label(filename).classes('text-sm font-medium')
                                            ui.label(f'{len(content) // 1024} KB').classes('text-xs text-gray-500')
                            
                            filter_data['inputs']['upload'] = ui.upload(
                                on_upload=handle_upload,
                                auto_upload=True,
                                label='Choose Image'
                            ).props('accept="image/*"').classes('w-full')
                        
                        elif param_type == 'select':
                            options = param_config.get('options', [])
                            option_labels = param_config.get('option_labels', {})
                            # Map options to labels if available
                            options_dict = {opt: option_labels.get(opt, opt) for opt in options} if option_labels else options
                            filter_data['inputs']['value'] = ui.select(
                                options=options_dict,
                                value=default
                            ).classes('w-full')
                        
                        elif param_type == 'multiselect':
                            options = param_config.get('options', [])
                            filter_data['inputs']['value'] = ui.select(
                                options=options,
                                multiple=True,
                                value=default or []
                            ).classes('w-full')
                        
                        elif param_type == 'number':
                            min_val = param_config.get('min', 0)
                            max_val = param_config.get('max', 100)
                            step = param_config.get('step', 1)
                            filter_data['inputs']['value'] = ui.number(
                                placeholder=f'Enter value',
                                value=default if default is not None else min_val,
                                min=min_val,
                                max=max_val,
                                step=step
                            ).classes('w-full')
                        
                        elif param_type == 'range':
                            min_val = param_config.get('min', 0)
                            max_val = param_config.get('max', 100)
                            
                            with ui.row().classes('w-full gap-2'):
                                filter_data['inputs']['min'] = ui.number(
                                    label='From',
                                    value=default[0] if default and default[0] is not None else min_val,
                                    min=min_val,
                                    max=max_val
                                ).classes('flex-1')
                                
                                filter_data['inputs']['max'] = ui.number(
                                    label='To',
                                    value=default[1] if default and default[1] is not None else max_val,
                                    min=min_val,
                                    max=max_val
                                ).classes('flex-1')
                
                # Initial input field
                update_input_field()
                
                # Update input when filter type changes
                filter_select.on('update:model-value', lambda: update_input_field())
            
            # Remove button
            def remove_filter():
                active_filters.remove(filter_data)
                filter_row.delete()
            
            ui.button(icon='close', on_click=remove_filter).props('flat round dense color=red').classes('mt-6')
        
        active_filters.append(filter_data)
        return filter_data
    
    with filters_container:
        # Load existing filters from operator params
        for param_name, param_value in existing_params.items():
            if param_name in params_schema:
                filter_data = create_filter_row(param_name)
                # Set the value after creation
                param_config = params_schema.get(param_name, {})
                param_type = param_config.get('type')
                
                if param_type == 'range' and isinstance(param_value, list) and len(param_value) == 2:
                    if 'min' in filter_data['inputs']:
                        filter_data['inputs']['min'].value = param_value[0]
                    if 'max' in filter_data['inputs']:
                        filter_data['inputs']['max'].value = param_value[1]
                elif param_type == 'image' and param_value:
                    # For image type, param_value might be string (old) or dict with filename and data
                    if isinstance(param_value, dict):
                        filename = param_value.get('filename')
                        image_data_b64 = param_value.get('data')
                        filter_data['inputs']['filename'] = filename
                        # Show full preview with actual image
                        if 'preview_container' in filter_data and image_data_b64:
                            with filter_data['preview_container']:
                                with ui.row().classes('w-full items-center gap-2'):
                                    ui.image(f'data:image/png;base64,{image_data_b64}').classes('w-24 h-24 object-cover rounded border')
                                    with ui.column().classes('flex-1'):
                                        ui.label(filename).classes('text-sm font-medium')
                                        size_kb = len(base64.b64decode(image_data_b64)) // 1024
                                        ui.label(f'{size_kb} KB').classes('text-xs text-gray-500')
                    else:
                        # Old format: just filename string
                        filter_data['inputs']['filename'] = param_value
                        if 'preview_container' in filter_data:
                            with filter_data['preview_container']:
                                ui.label(f'📷 {param_value}').classes('text-sm text-gray-600')
                elif param_type in ['text', 'textarea', 'select', 'multiselect', 'number']:
                    if 'value' in filter_data['inputs']:
                        filter_data['inputs']['value'].value = param_value
    
    # Add Filter button
    with ui.row().classes('w-full mb-6'):
        ui.button(
            'Add Filter',
            icon='add',
            on_click=lambda: (filters_container.move(create_filter_row()['container']), None)
        ).props('outline').classes(f'text-[{settings.primary_color}]')
    
    # Action buttons for dynamic filters
    def apply_params():
        """Collect parameter values from active filters and update the operator"""
        params = {}
        missing_required = []
        
        for filter_data in active_filters:
            param_name = filter_data['param_select'].value
            param_config = params_schema.get(param_name, {})
            param_type = param_config.get('type')
            is_required = param_config.get('required', False)
            
            if param_type == 'range':
                min_input = filter_data['inputs'].get('min')
                max_input = filter_data['inputs'].get('max')
                if min_input and max_input:
                    params[param_name] = [min_input.value, max_input.value]
            elif param_type == 'image':
                # Store image data as base64 string
                filename = filter_data['inputs'].get('filename')
                image_data = filter_data['inputs'].get('image_data')
                if filename and image_data:
                    params[param_name] = {
                        'filename': filename,
                        'data': base64.b64encode(image_data).decode('utf-8')
                    }
                elif is_required:
                    missing_required.append(param_config.get('label', param_name))
            else:
                value_input = filter_data['inputs'].get('value')
                if value_input:
                    value = value_input.value
                    # Only include non-empty values
                    if value or value == 0:
                        params[param_name] = value
                    elif is_required:
                        missing_required.append(param_config.get('label', param_name))
                elif is_required:
                    missing_required.append(param_config.get('label', param_name))
        
        # Check if required fields are missing
        if missing_required:
            ui.notify(f'Required fields missing: {", ".join(missing_required)}', type='negative')
            return
        
        # Check for Semantic/Similarity Search: must have result_mode and corresponding parameter
        if op_name in ['Semantic Search', 'Similarity Search']:
            if 'result_mode' not in params:
                ui.notify('Please select a result mode', type='negative')
                return
            
            result_mode = params.get('result_mode')
            if result_mode in ['top_n', 'last_n'] and 'n_results' not in params:
                ui.notify('Please specify number of results', type='negative')
                return
            elif result_mode == 'similarity_range' and 'similarity_min' not in params and 'similarity_max' not in params:
                ui.notify('Please specify at least similarity min or max', type='negative')
                return
        
        # Update params in state
        pipeline_state.update_params(operator_id, params)
        
        # Log params with truncated base64 data for readability
        log_params = {}
        for k, v in params.items():
            if isinstance(v, dict) and 'data' in v and 'filename' in v:
                # Truncate base64 data to first 20 chars
                log_params[k] = {'filename': v['filename'], 'data': v['data'][:20] + '...'}
            else:
                log_params[k] = v
        logger.info(f"Applied params for {op_name}: {log_params}")
        ui.notify(f'{op_name} updated with {len(params)} filters!')
        close_panel()
        # Re-render pipeline in a new context using app.storage
        with pipeline_area:
            render_pipeline_func()
    
    with ui.row().classes('w-full justify-end gap-2 mt-6'):
        ui.button('Cancel', on_click=close_panel).props('flat color=grey')
        ui.button('Apply', on_click=apply_params).props('color=primary')


def render_static_form_ui(params_schema, existing_params, operator_id, op_name, close_panel,
                         pipeline_state, pipeline_area, render_pipeline_func):
    """Renders static form UI for Semantic Search, Similarity Search, etc."""
    ui.label('PARAMETERS').classes('text-sm font-bold text-gray-600 mb-3')
    
    # Dictionary to store input references
    param_inputs = {}
    
    # Store result_mode value for conditional rendering
    result_mode_value = existing_params.get('result_mode', params_schema.get('result_mode', {}).get('default', 'top_n'))
    
    # Render all non-conditional parameters first
    for param_name, param_config in params_schema.items():
        if param_config.get('conditional'):
            continue  # Skip conditional params for now
        
        param_type = param_config.get('type')
        label = param_config.get('label', param_name)
        description = param_config.get('description', '')
        default = param_config.get('default')
        is_required = param_config.get('required', False)
        existing_value = existing_params.get(param_name, default)
        
        # Label with required indicator
        label_text = f"{label} {'*' if is_required else ''}"
        ui.label(label_text).classes('text-sm font-medium text-gray-700 mt-3')
        if description:
            ui.label(description).classes('text-xs text-gray-500 mb-1')
        
        # Render input based on type
        if param_type == 'text':
            param_inputs[param_name] = ui.input(
                placeholder=f'Enter {label.lower()}',
                value=existing_value or ''
            ).classes('w-full mb-2')
        
        elif param_type == 'textarea':
            param_inputs[param_name] = ui.textarea(
                placeholder=f'Enter {label.lower()}',
                value=existing_value or ''
            ).classes('w-full mb-2').props('rows=5')
        
        elif param_type == 'image':
            # Image upload with preview
            # existing_value might be a string (old format) or dict with filename and data
            if isinstance(existing_value, dict):
                existing_filename = existing_value.get('filename')
                existing_data = existing_value.get('data')  # base64 string
            else:
                existing_filename = existing_value  # old format: just filename
                existing_data = None
            
            param_inputs[param_name] = {'filename': existing_filename, 'image_data': None}
            preview_container = ui.column().classes('w-full mb-2')
            
            # Show existing image if available
            if existing_filename:
                with preview_container:
                    if existing_data:
                        # Show full preview with actual image
                        with ui.row().classes('w-full items-center gap-2'):
                            ui.image(f'data:image/png;base64,{existing_data}').classes('w-24 h-24 object-cover rounded border')
                            with ui.column().classes('flex-1'):
                                ui.label(existing_filename).classes('text-sm font-medium')
                                size_kb = len(base64.b64decode(existing_data)) // 1024
                                ui.label(f'{size_kb} KB').classes('text-xs text-gray-500')
                    else:
                        # Fallback for old format (filename only)
                        with ui.card().classes('w-full p-3 bg-gray-50'):
                            with ui.row().classes('w-full items-center gap-3'):
                                ui.icon('image', size='lg').classes('text-gray-400')
                                with ui.column().classes('flex-1 gap-1'):
                                    ui.label(existing_filename).classes('text-sm font-medium')
                                    ui.label('Previously uploaded').classes('text-xs text-gray-500')
            
            async def handle_upload(e, pname=param_name, prev=preview_container):
                # e is the upload event, contains the uploaded file
                content = await e.file.read()
                filename = e.file.name
                param_inputs[pname]['filename'] = filename
                param_inputs[pname]['image_data'] = content
                prev.clear()
                with prev:
                    b64_data = base64.b64encode(content).decode()
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.image(f'data:image/png;base64,{b64_data}').classes('w-24 h-24 object-cover rounded border')
                        with ui.column().classes('flex-1'):
                            ui.label(filename).classes('text-sm font-medium')
                            ui.label(f'{len(content) // 1024} KB').classes('text-xs text-gray-500')
            
            ui.upload(on_upload=handle_upload, auto_upload=True, label='Choose Image').props('accept="image/*"').classes('w-full mb-2')
        
        elif param_type == 'select':
            options = param_config.get('options', [])
            option_labels = param_config.get('option_labels', {})
            options_dict = {opt: option_labels.get(opt, opt) for opt in options} if option_labels else options
            param_inputs[param_name] = ui.select(
                options=options_dict,
                value=existing_value
            ).classes('w-full mb-2')
            
            # If this is result_mode, update conditional fields when changed
            if param_name == 'result_mode':
                conditional_container = ui.column().classes('w-full')
                
                def update_conditionals():
                    conditional_container.clear()
                    current_mode = param_inputs['result_mode'].value
                    with conditional_container:
                        render_conditional_fields(params_schema, param_inputs, existing_params, current_mode)
                
                param_inputs[param_name].on('update:model-value', update_conditionals)
                
                # Render initial conditional fields
                with conditional_container:
                    render_conditional_fields(params_schema, param_inputs, existing_params, result_mode_value)
        
        elif param_type == 'number':
            min_val = param_config.get('min', 0)
            max_val = param_config.get('max', 100)
            step = param_config.get('step', 1)
            param_inputs[param_name] = ui.number(
                value=existing_value if existing_value is not None else default,
                min=min_val,
                max=max_val,
                step=step
            ).classes('w-full mb-2')
    
    # Action buttons
    def apply_params():
        params = {}
        missing_required = []
        
        for param_name, param_config in params_schema.items():
            param_type = param_config.get('type')
            is_required = param_config.get('required', False)
            conditional = param_config.get('conditional')
            
            # Check if field should be included based on conditional logic
            if conditional:
                result_mode = param_inputs.get('result_mode')
                if result_mode and result_mode.value not in conditional:
                    continue  # Skip this param
            
            if param_type == 'image':
                filename = param_inputs[param_name].get('filename')
                image_data = param_inputs[param_name].get('image_data')
                if filename and image_data:
                    params[param_name] = {
                        'filename': filename,
                        'data': base64.b64encode(image_data).decode('utf-8')
                    }
                elif is_required:
                    missing_required.append(param_config.get('label', param_name))
            else:
                input_field = param_inputs.get(param_name)
                if input_field:
                    value = input_field.value
                    if value or value == 0:
                        # Convert number types to int if step is 1 (to avoid .0 floats)
                        if param_type == 'number':
                            step = param_config.get('step', 1)
                            if step == 1 or step is None:
                                value = int(value)
                        # Convert range types to int if step is 1
                        elif param_type == 'range':
                            step = param_config.get('step', 1)
                            if step == 1 or step is None:
                                if isinstance(value, list):
                                    value = [int(v) if v is not None else None for v in value]
                        params[param_name] = value
                    elif is_required:
                        missing_required.append(param_config.get('label', param_name))
        
        if missing_required:
            ui.notify(f'Required fields missing: {", ".join(missing_required)}', type='negative')
            return
        
        # Validate result mode logic
        if op_name in ['Semantic Search', 'Similarity Search']:
            result_mode = params.get('result_mode')
            if result_mode in ['top_n', 'last_n'] and 'n_results' not in params:
                ui.notify('Please specify number of results', type='negative')
                return
            elif result_mode == 'similarity_range' and 'similarity_min' not in params and 'similarity_max' not in params:
                ui.notify('Please specify at least similarity min or max', type='negative')
                return
        
        pipeline_state.update_params(operator_id, params)
        
        # Log params with truncated base64 data for readability
        log_params = {}
        for k, v in params.items():
            if isinstance(v, dict) and 'data' in v and 'filename' in v:
                # Truncate base64 data to first 20 chars
                log_params[k] = {'filename': v['filename'], 'data': v['data'][:20] + '...'}
            else:
                log_params[k] = v
        logger.info(f"Applied params for {op_name}: {log_params}")
        ui.notify(f'{op_name} configured successfully!')
        close_panel()
        with pipeline_area:
            render_pipeline_func()
    
    with ui.row().classes('w-full justify-end gap-2 mt-6'):
        ui.button('Cancel', on_click=close_panel).props('flat color=grey')
        ui.button('Apply', on_click=apply_params).props('color=primary')


def render_conditional_fields(params_schema, param_inputs, existing_params, current_mode):
    """Renders conditional fields based on the current result_mode"""
    for param_name, param_config in params_schema.items():
        conditional = param_config.get('conditional')
        if not conditional or current_mode not in conditional:
            continue
        
        param_type = param_config.get('type')
        label = param_config.get('label', param_name)
        description = param_config.get('description', '')
        default = param_config.get('default')
        existing_value = existing_params.get(param_name, default)
        
        ui.label(label).classes('text-sm font-medium text-gray-700 mt-3')
        if description:
            ui.label(description).classes('text-xs text-gray-500 mb-1')
        
        if param_type == 'number':
            min_val = param_config.get('min', 0)
            max_val = param_config.get('max', 100)
            step = param_config.get('step', 1)
            param_inputs[param_name] = ui.number(
                value=existing_value if existing_value is not None else default,
                min=min_val,
                max=max_val,
                step=step
            ).classes('w-full mb-2')
