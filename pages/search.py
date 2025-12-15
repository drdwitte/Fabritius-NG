from nicegui import ui, app
from ui_components.config import BROWN, OPERATORS
import json

# Global variable (these are the initial operators in the pipeline upon loading the page)
pipeline = [
    'Metadata Filter',
    'Semantic Search',
    'Similarity Search'
]  # List of operators in the current pipeline

pipeline_area = None  # This is where the pipeline operators will be rendered
pipeline_name_input = None  # Reference to the pipeline name input field
selected_operator = None  # Currently selected operator for configuration
config_panel = None  # Configuration panel reference

def get_pipeline():
    """
    Returns the current pipeline (list of operators).
    """
    global pipeline
    return pipeline

def add_operator(op_name: str):
    """
    Adds an operator to the pipeline and re-renders the pipeline.
    """
    pipeline = get_pipeline()
    pipeline.append(op_name)  # Add the operator to the pipeline
    ui.notify(f'Added {op_name}')  # Notify the user
    render_pipeline()  # Re-render the pipeline to reflect the changes

def save_pipeline():
    """
    Shows a dialog to save the pipeline with a custom filename.
    """
    global pipeline_name_input
    pipeline = get_pipeline()
    
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
            pipeline_json = json.dumps(pipeline, indent=2)
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
            ui.button('Save', on_click=handle_save).props('color=primary')
    
    dialog.open()

async def load_pipeline():
    """
    Opens a file dialog to load a pipeline from a JSON file.
    """
    global pipeline
    
    async def handle_upload(e):
        """Handle the uploaded file"""
        try:
            content = e.content.read().decode('utf-8')
            pipeline = json.loads(content)
            ui.notify('Pipeline loaded successfully!')
            render_pipeline()
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
            icon_button('folder_open', 'Load', load_pipeline)
            icon_button('save', 'Save', save_pipeline)
            run_button('Run', lambda: ui.notify('Run clicked'))
    
    # Layout: operator library + operator chain + results preview
    with ui.row().classes('w-full'):
        # Sidebar (left), titled OPERATOR LIBRARY
        with ui.column().classes('w-80 p-4 bg-gray-50 rounded-xl gap-4'):
            ui.label('OPERATOR LIBRARY').classes('text-sm font-bold text-gray-600 mb-2')

            # Render operator cards from the centralized OPERATORS configuration
            for operator_name in OPERATORS.keys():
                operator_card(operator_name, lambda op=operator_name: add_operator(op))

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
    pipeline = get_pipeline()  # Get the current pipeline

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
            for op in pipeline:
                operator = OPERATORS.get(op, {'icon': 'tune', 'description': 'Unknown operator'})
                icon = operator['icon']

                # Create a tile for the operator
                tile = ui.element('div').classes(
                    'flex flex-col gap-0 px-2 py-2 rounded-xl bg-white shadow-sm min-w-[180px] cursor-pointer hover:shadow-md transition'
                ).on('click', lambda _, name=op: show_operator_config(name))

                with tile:
                    with ui.row().classes('items-center w-full'):
                        ui.icon('drag_indicator').classes('text-xl text-gray-400 cursor-move')
                        ui.icon(icon).classes('text-xl text-gray-700')
                        ui.label(op).classes('text-gray-800 font-medium ml-2')
                        # Delete icon with proper closure to avoid issues with lambda variable binding
                        ui.icon('delete').classes('text-xl text-red-500 cursor-pointer ml-auto').on(
                            'click', lambda _, name=op, t=tile: delete_operator_by_name(name, t)
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

def delete_operator_by_name(op_name: str, tile):
    """
    Deletes an operator from the pipeline by name and removes its tile from the UI.
    
    Args:
        op_name: The name of the operator to delete
        tile: The UI tile element to remove from the DOM
    """
    pipeline = get_pipeline()
    if op_name in pipeline:
        pipeline.remove(op_name)  # Remove the operator from the pipeline
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
        
        # Fake parameters (placeholder for future implementation)
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





