from nicegui import ui, app
from ui_components.config import BROWN, OPERATORS
import json
import uuid
from typing import List, Dict, Optional

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
        return operator_id
    
    def remove_operator(self, operator_id: str) -> bool:
        """
        Removes an operator by ID.
        Returns True if removed, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators.pop(index)
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
        Returns True if updated, False if not found.
        """
        index = self._find_index(operator_id)
        if index != -1:
            self._operators[index]['params'].update(params)
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

# Global UI references
pipeline_area = None  # The UI area where the pipeline is rendered (with operator tiles, delete and drag buttons)
pipeline_name_input = None  # Reference to UI element with the name input field
config_panel = None  # Reference to UI Config panel: right-hand side panel for configuration of operators

def save_pipeline(pipeline_name_input):
    """Shows a dialog to save the pipeline with a custom filename."""
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
            content = e.content.read().decode('utf-8')
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
                tile = ui.element('div').classes(
                    'flex flex-col gap-0 px-2 py-2 rounded-xl bg-white shadow-sm min-w-[180px] cursor-pointer hover:shadow-md transition'
                ).on('click', lambda _, name=op_name: show_operator_config(name))

                with tile:
                    with ui.row().classes('items-center w-full'):
                        ui.icon('drag_indicator').classes('text-xl text-gray-400 cursor-move')
                        ui.icon(icon).classes('text-xl text-gray-700')
                        ui.label(op_name).classes('text-gray-800 font-medium ml-2')
                        # Delete icon with proper closure to avoid issues with lambda variable binding
                        ui.icon('delete').classes('text-xl text-red-500 cursor-pointer ml-auto').on(
                            'click', lambda _, op_id=op_id, name=op_name, t=tile: delete_operator_by_id(op_id, name, t)
                        )

                    # Additional operator details
                    ui.label("param1: value").classes('text-sm text-gray-400 italic w-full mt-2')
                    ui.label("param2: value").classes('text-sm text-gray-400 italic w-full')
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

def show_operator_config(op_name: str):
    """
    Shows a configuration panel for the selected operator.
    """
    global selected_operator, config_panel
    selected_operator = op_name
    
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
        
        # Parameters
        ui.label('PARAMETERS').classes('text-sm font-bold text-gray-600 mb-3')
        
        ui.label('Parameter 1')
        ui.input(placeholder='Enter value').classes('w-full mb-4')
        
        ui.label('Parameter 2')
        ui.input(placeholder='Enter value').classes('w-full mb-4')
        
        ui.label('Parameter 3')
        ui.select(['Option 1', 'Option 2', 'Option 3'], value='Option 1').classes('w-full mb-4')

        # Action buttons
        with ui.row().classes('w-full justify-end gap-2 mt-6'):
            ui.button('Cancel', on_click=close_panel).props('flat color=grey')
            ui.button('Apply', on_click=lambda: (ui.notify(f'{op_name} updated!'), close_panel())).props('color=primary')





