from nicegui import ui, app
from ui_components.config import BROWN, OPERATORS
import json
import uuid
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TODO: Future refactoring - Class-based operators
# Currently operators are identified by name strings (e.g., 'Metadata Filter').
# Future improvement: Create operator classes with execute() methods that can be
# mapped from operator names (Strategy pattern). This allows each operator type
# to have its own implementation logic while maintaining the same interface.
# Example: OPERATOR_CLASSES = {'Metadata Filter': MetadataFilterOperator, ...}

############################################
############### BACK-END ###################
############################################

class PipelineState:
    """
    Manages the state of the search pipeline.
    Each operator instance has a unique ID and can store parameters.
    """
    
    def __init__(self):
        self._operators: List[Dict] = []
    
    def _find_index(self, operator_id: str) -> int:
        """
        Private helper: finds the index of an operator by ID.
        Returns -1 if not found.
        """
        for i, op in enumerate(self._operators):
            if op['id'] == operator_id:
                return i
        return -1
    
    def add_operator(self, operator_name: str) -> str:
        """
        Adds an operator to the pipeline.
        Returns the unique ID of the operator instance.
        """
        # Generate a unique ID for the operator, 
        # 2 operators with same name can coexist and will have different IDs
        operator_id = str(uuid.uuid4())
        operator = {
            'id': operator_id,
            'name': operator_name,
            'params': {}
        }
        self._operators.append(operator)
        logger.info(f"Added '{operator_name}': {[op['name'] for op in self._operators]}")
        return operator_id
    
    def remove_operator(self, operator_id: str) -> bool:
        """
        Removes an operator by ID.
        Returns True if removed, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            removed_name = self._operators[index]['name']
            self._operators.pop(index)
            logger.info(f"Removed '{removed_name}': {[op['name'] for op in self._operators]}")
            return True
        return False
    
    def get_operator(self, operator_id: str) -> Optional[Dict]:
        """
        Gets a single operator by ID.
        Returns a copy to prevent external mutation.
        """
        index = self._find_index(operator_id)
        if index != -1:
            return self._operators[index].copy()
        return None
    
    def get_all_operators(self) -> List[Dict]:
        """Returns a copy of all operators."""
        # op.copy makes a copy of each operator dict to prevent external mutation
        return [op.copy() for op in self._operators]
    
    def update_params(self, operator_id: str, params: Dict) -> bool:
        """
        Updates the parameters of an operator.
        Replaces the entire params dict.
        Returns True if updated, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators[index]['params'] = params
            return True
        return False
    
    def reorder(self, new_order: List[str]):
        """
        Reorders operators based on a list of IDs.
        Missing IDs are ignored.
        """
        #id_to_operator is a mapping to new index in operator List (uid -> operator dict)
        id_to_operator = {op['id']: op for op in self._operators}
        # Rebuild the operator list in the new order
        self._operators = [id_to_operator[op_id] for op_id in new_order if op_id in id_to_operator]
        logger.info(f"Reordered: {[op['name'] for op in self._operators]}")
        print(f"[Pipeline] Reordered: {[op['name'] for op in self._operators]}")
    
    def clear(self):
        """Removes all operators from the pipeline."""
        self._operators = []
    
    def to_json(self) -> str:
        """Export pipeline to JSON string."""
        return json.dumps(self._operators, indent=2)
    
    def from_json(self, json_string: str):
        """Import pipeline from JSON string."""
        self._operators = json.loads(json_string)

# Global state instance
pipeline_state = PipelineState()

# Initialize with default operators (NOTE: we will refactor this into class based operators later)
pipeline_state.add_operator('Metadata Filter')
pipeline_state.add_operator('Semantic Search')
pipeline_state.add_operator('Similarity Search')


############################################
############### FRONT-END ##################
############################################

# The main function in front-end are: 
# - render_search: renders the main search page with operator library and pipeline area
# - render_pipeline: renders the current pipeline in the pipeline area
# - show_operator_config: shows the configuration panel for a selected operator

# Global UI references
pipeline_area = None  # The UI area where the pipeline is rendered (with operator tiles, delete and drag buttons)
pipeline_name_input = None  # Reference to UI element with the name input field
config_panel = None  # Reference to UI Config panel: right-hand side panel for configuration of operators

async def sync_from_dom():
    """Syncs the pipeline state from the DOM order (DOM is source of truth)."""
    # Use JavaScript to read the current order from DOM
    result = await ui.run_javascript('''
        const container = document.getElementById('pipeline-container');
        if (container) {
            return Array.from(container.children)
                .map(tile => tile.getAttribute('data-operator-id'))
                .filter(id => id !== null);
        }
        return [];
    ''', timeout=1.0)
    
    if result:
        pipeline_state.reorder(result)
        logger.info(f"Synced from DOM: {[op['name'] for op in pipeline_state.get_all_operators()]}")

async def save_pipeline(pipeline_name_input):
    """Shows a dialog to save the pipeline with a custom filename."""
    # Sync state from DOM before saving
    await sync_from_dom()
    
    # Get the pipeline name from the input field, or use default
    suggested_name = pipeline_name_input.value.strip() if pipeline_name_input and pipeline_name_input.value.strip() else 'Untitled Pipeline'
    
    def handle_save():
        """Save the pipeline with the given filename"""
        filename = filename_input.value.strip()
        if not filename:
            ui.notify('Please enter a filename')
            return
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            pipeline_json = pipeline_state.to_json()
            ui.download(pipeline_json.encode('utf-8'), filename)
            ui.notify(f'Saving {filename}...')
            dialog.close()
        except Exception as e:
            ui.notify(f'Error saving pipeline: {str(e)}')
    
    # Show a dialog to get the filename
    with ui.dialog() as dialog, ui.card().classes('p-6'):
        ui.label('Save Pipeline As').classes('text-lg font-bold mb-4')
        
        filename_input = ui.input(
            'Filename', 
            value=suggested_name,
            placeholder='my_pipeline'
        ).classes('w-80').on('keydown.enter', handle_save)
        
        ui.label('.json').classes('text-sm text-gray-500 mt-1')
        
        with ui.row().classes('w-full justify-end gap-2 mt-6'):
            ui.button('Cancel', on_click=dialog.close).props('flat color=grey')
            ui.button('Save', on_click=handle_save).props('color=none text-color=none').classes(f'bg-[{BROWN}] text-white')
    
    dialog.open()

async def load_pipeline(on_complete_callback):
    """Opens a file dialog to load a pipeline from a JSON file."""
    async def handle_upload(e):
        """Handle the uploaded file"""
        try:
            content = (await e.file.read()).decode('utf-8')
            pipeline_state.from_json(content)
            ui.notify('Pipeline loaded successfully!')
            on_complete_callback()  # Call the callback to re-render
        except Exception as ex:
            ui.notify(f'Error loading pipeline: {str(ex)}')
    
    # Create a hidden upload component
    upload = ui.upload(on_upload=handle_upload, auto_upload=True).props('accept=.json')
    upload.classes('hidden')
    # Trigger the file dialog
    upload.run_method('pickFiles')

def render_search(ui):
    """
    Renders the main search page, including the operator library and the pipeline area.
    """
    global pipeline_area, pipeline_name_input
    
    # Load Sortable.js for drag-and-drop functionality
    ui.add_head_html("<script src=\"https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js\"></script>")    

    # Title & icon
    with ui.row().classes('items-center gap-2 mb-2'):
        ui.icon('search').classes('text-2xl text-amber-700')
        ui.label('Search Pipeline').classes('text-2xl font-bold')

    # Top bar: full width, left input, right buttons
    with ui.row().props('flat').classes('w-full flex items-center justify-between bg-white shadow-sm px-4 py-2 mb-4 rounded'):
        # Left: input field - store reference for later use
        pipeline_name_input = ui.input(
            placeholder='Pipeline name', 
            value='Untitled Pipeline'
        ).props('borderless dense').classes('w-64')
        # Right: buttons
        with ui.row().classes('gap-2'):
            icon_button('folder_open', 'Load', lambda: load_pipeline(render_pipeline))
            icon_button('save', 'Save', lambda: save_pipeline(pipeline_name_input))
            run_button('Run', lambda: ui.notify('Run clicked'))
    
    # Layout: operator library + operator chain + results preview
    with ui.row().classes('w-full'):
        # Sidebar (left), titled OPERATOR LIBRARY
        with ui.column().classes('w-80 p-4 bg-gray-50 rounded-xl gap-4'):
            ui.label('OPERATOR LIBRARY').classes('text-sm font-bold text-gray-600 mb-2')

            # Render operator cards from the centralized OPERATORS configuration
            for operator_name in OPERATORS.keys():
                operator_card(operator_name, lambda op=operator_name: (pipeline_state.add_operator(op), ui.notify(f'Added {op}'), render_pipeline()))

        # Main content (right)
        with ui.column().classes('flex-grow p-4'):
            ui.label('OPERATOR CHAIN').classes('text-xl font-bold mb-2')
            pipeline_area = ui.element('div').props('id=pipeline-area')  # Define the pipeline area
            render_pipeline()  # Render the pipeline
            ui.label('Results will appear here...')

def icon_button(icon_name, label, on_click, bg='bg-white', text='text-gray-700', border='border-gray-300'):
    """
    Creates an icon button with customizable icon, label, and click behavior.
    """
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes(f'h-9 px-3 flex items-center gap-x-8 rounded-md '
                f'border {border} {bg} {text} hover:bg-gray-50 py-1')
    with btn:
        ui.icon(icon_name).classes(f'{text} text-lg')
        ui.label(label).classes(f'{text} text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn

def run_button(label, on_click):
    """
    Creates a run button with a play icon, label, and click behavior.
    """
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes('h-9 px-3 flex items-center gap-x-8 rounded-md '
                'border border-gray-900 bg-black text-white hover:bg-gray-800 py-1')
    with btn:
        ui.icon('play_arrow').classes('text-white text-lg')
        ui.label(label).classes('text-white text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn

def operator_card(operator_name, on_add):
    """
    Creates an operator card using the centralized OPERATORS configuration.
    """
    operator = OPERATORS[operator_name]
    with ui.row().classes('w-full items-center gap-3 p-3 rounded-lg bg-white shadow hover:bg-gray-100 transition'):
        # Operator icon
        ui.icon(operator['icon']).classes(f'text-3xl text-[{BROWN}]')
        
        # Operator title + description
        with ui.column().classes('flex-1 items-start gap-0'):
            ui.label(operator_name).classes('text-base font-bold text-gray-800 mb-0')
            ui.label(operator['description']).classes('text-xs text-gray-500 mt-0')
        
        # Plus button to add operator
        (
            ui.button(icon='add', on_click=on_add)
                .props('round color=none text-color=none')
                .classes(f'bg-[{BROWN}] text-white ml-auto text-xs p-0')
        )

def render_pipeline():
    """
    Renders the pipeline area with all operators as tiles.
    """
    global pipeline_area
    pipeline = pipeline_state.get_all_operators()  # Get the current pipeline

    # Clear the pipeline area before re-rendering
    if pipeline_area is not None:
        pipeline_area.clear()

    # Create a new container for the pipeline
    with pipeline_area:
        pipeline_container = (
            ui.element('div')
            .props('id=pipeline-container')
            .classes('flex items-start gap-4 bg-white p-4 rounded')
        )

        with pipeline_container:
            for op_data in pipeline:
                op_id = op_data['id']
                op_name = op_data['name']
                operator = OPERATORS.get(op_name, {'icon': 'tune', 'description': 'Unknown operator'})
                icon = operator['icon']

                # Create a tile for the operator
                tile = (ui.element('div')
                    .classes('flex flex-col gap-0 px-2 py-2 rounded-xl bg-white shadow-sm min-w-[180px] cursor-pointer hover:shadow-md transition')
                    .props(f'data-operator-id="{op_id}"')
                    .on('click', lambda _, op_id=op_id: show_operator_config(op_id))
                )

                with tile:
                    with ui.row().classes('items-center w-full'):
                        ui.icon('drag_indicator').classes('text-xl text-gray-400 cursor-move')
                        ui.icon(icon).classes('text-xl text-gray-700')
                        ui.label(op_name).classes('text-gray-800 font-medium ml-2')
                        # Delete icon with proper closure to avoid issues with lambda variable binding
                        ui.icon('delete').classes('text-xl text-red-500 cursor-pointer ml-auto').on(
                            'click', lambda _, op_id=op_id, name=op_name, t=tile: delete_operator_by_id(op_id, name, t)
                        )

                    # Show actual operator parameters
                    params = op_data.get('params', {})
                    if params:
                        for param_name, param_value in list(params.items())[:3]:  # Show max 3 params
                            # Format the value nicely
                            if isinstance(param_value, dict) and 'filename' in param_value:
                                # For image type, show filename only (not base64 data)
                                display_value = f'📷 {param_value["filename"]}'
                            elif isinstance(param_value, list):
                                if all(isinstance(x, (int, float)) for x in param_value):
                                    display_value = f"{param_value[0]} - {param_value[1]}"
                                else:
                                    display_value = ', '.join(str(v) for v in param_value[:3])
                                    if len(param_value) > 3:
                                        display_value += '...'
                            else:
                                display_value = str(param_value)[:30]
                            ui.label(f"{param_name}: {display_value}").classes('text-sm text-gray-400 italic w-full leading-tight mt-1')
                    else:
                        ui.label("No filters applied").classes('text-sm text-gray-400 italic w-full mt-2')
                    
                    ui.label("89 results").classes(
                        f'inline-block mt-3 px-2 py-1 text-xs font-medium rounded-md bg-[{BROWN}] text-white'
                    )

    # Reinitialize Sortable.js for drag-and-drop functionality
    ui.run_javascript("""
    new Sortable(document.getElementById('pipeline-container'), {
        animation: 150,
        ghostClass: 'opacity-50'
    });
    """)

def delete_operator_by_id(operator_id: str, op_name: str, tile):
    """
    Deletes an operator from the pipeline by ID and removes its tile from the UI.
    
    Args:
        operator_id: The unique ID of the operator to delete
        op_name: The name of the operator (for notification)
        tile: The UI tile element to remove from the DOM
    """
    pipeline_state.remove_operator(operator_id)  # Remove the operator from the pipeline
    tile.delete()  # Remove the tile directly from the DOM
    ui.notify(f'Removed {op_name}')  # Notify the user
    render_pipeline()  # Re-render the pipeline

def show_operator_config(operator_id: str):
    """
    Shows a configuration panel for the selected operator.
    For operators with multiple filter options, allows dynamic adding/removing of filters.
    Loads existing parameters from the operator state.
    """
    global selected_operator, config_panel
    
    # Get the operator data from state
    operator_data = pipeline_state.get_operator(operator_id)
    if not operator_data:
        ui.notify('Operator not found')
        return
    
    op_name = operator_data['name']
    existing_params = operator_data.get('params', {})
    selected_operator = operator_id
    
    # Remove existing panel completely if it exists
    if config_panel:
        config_panel.delete()
        config_panel = None
    
    # Create new panel
    config_panel = ui.column().classes(
        'fixed right-0 top-0 h-screen w-96 bg-white shadow-2xl p-6 border-l border-gray-200 z-50 overflow-y-auto'
    )
    
    def close_panel():
        """Completely remove the config panel"""
        global config_panel
        if config_panel:
            config_panel.delete()
            config_panel = None
    
    with config_panel:
        # Header with close button
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label(f'Configure {op_name}').classes('text-xl font-bold')
            ui.button(icon='close', on_click=close_panel).props('flat round dense')
        
        # Get operator info
        operator = OPERATORS.get(op_name, {})
        
        # Operator icon and description
        with ui.row().classes('items-center gap-3 mb-6 p-3 bg-gray-50 rounded-lg'):
            ui.icon(operator.get('icon', 'tune')).classes(f'text-2xl text-[{BROWN}]')
            ui.label(operator.get('description', 'No description')).classes('text-sm text-gray-600')
        
        # Parameters section
        params_schema = operator.get('params', {})
        
        if params_schema:
            # Determine UI pattern: Metadata Filter uses dynamic filters, others use static form
            use_dynamic_filters = (op_name == 'Metadata Filter')
            
            if use_dynamic_filters:
                # DYNAMIC FILTER UI (Metadata Filter)
                render_dynamic_filter_ui(params_schema, existing_params, operator_id, op_name, close_panel)
            else:
                # STATIC FORM UI (Semantic Search, Similarity Search, etc.)
                render_static_form_ui(params_schema, existing_params, operator_id, op_name, close_panel)
        else:
            # No parameters defined for this operator
            ui.label('No parameters available for this operator.').classes('text-sm text-gray-500 italic')

def render_dynamic_filter_ui(params_schema, existing_params, operator_id, op_name, close_panel):
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
                                        import base64
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
                                import base64
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
        ).props('outline').classes(f'text-[{BROWN}]')
    
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
                    import base64
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
            render_pipeline()
    
    with ui.row().classes('w-full justify-end gap-2 mt-6'):
        ui.button('Cancel', on_click=close_panel).props('flat color=grey')
        ui.button('Apply', on_click=apply_params).props('color=primary')

def render_static_form_ui(params_schema, existing_params, operator_id, op_name, close_panel):
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
                                import base64
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
                    import base64
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
                    import base64
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
            render_pipeline()
    
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






