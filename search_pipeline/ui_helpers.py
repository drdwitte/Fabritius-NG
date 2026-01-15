"""
UI helper functions for the search pipeline.

This module contains reusable UI components and utility functions
that don't belong to a specific component.
"""

from loguru import logger
from nicegui import ui
from config import settings
from pages import detail


def icon_button(icon_name: str, label: str, on_click, bg='bg-white', text='text-gray-700', border='border-gray-300'):
    """
    Creates an icon button with customizable icon, label, and click behavior.
    
    Args:
        icon_name: Material icon name
        label: Button label text
        on_click: Click handler function
        bg: Background color class
        text: Text color class
        border: Border color class
    
    Returns:
        ui.button: The created button element
    """
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes(f'h-9 px-3 flex items-center gap-x-8 rounded-md '
                f'border {border} {bg} {text} hover:bg-gray-50 py-1')
    with btn:
        ui.icon(icon_name).classes(f'{text} text-lg')
        ui.label(label).classes(f'{text} text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn


def run_button(label: str, on_click):
    """
    Creates a run button with a play icon, label, and click behavior.
    
    Args:
        label: Button label text
        on_click: Click handler function
    
    Returns:
        ui.button: The created button element
    """
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes('h-9 px-3 flex items-center gap-x-8 rounded-md '
                'border border-gray-900 bg-black text-white hover:bg-gray-800 py-1')
    with btn:
        ui.icon('play_arrow').classes('text-white text-lg')
        ui.label(label).classes('text-white text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn


def format_param_value(value) -> str:
    """
    Format a parameter value for display in operator tiles.
    
    Args:
        value: Parameter value (can be dict, list, number, string, etc.)
    
    Returns:
        str: Formatted display string
    """
    if isinstance(value, dict) and 'filename' in value:
        # For image type, show filename only
        return f'📷 {value["filename"]}'
    elif isinstance(value, list):
        if all(isinstance(x, (int, float, type(None))) for x in value):
            # Convert to int for year ranges to avoid .0 display
            val0 = int(value[0]) if value[0] is not None else value[0]
            val1 = int(value[1]) if value[1] is not None else value[1]
            return f"{val0} - {val1}"
        else:
            display_value = ', '.join(str(v) for v in value[:3])
            if len(value) > 3:
                display_value += '...'
            return display_value
    elif isinstance(value, float) and value.is_integer():
        # Convert float to int if it has no decimal part (e.g., 15.0 -> 15)
        return str(int(value))
    else:
        return str(value)[:30]


async def save_pipeline(pipeline_state, pipeline_name_input):
    """
    Shows a dialog to save the pipeline with a custom filename.
    
    Args:
        pipeline_state: The PipelineState instance to save
        pipeline_name_input: UI input element containing the pipeline name
    """
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
            ui.button('Save', on_click=handle_save).props('color=none text-color=none').classes(f'bg-[{settings.brown}] text-white')
    
    dialog.open()


async def load_pipeline(pipeline_state, on_complete_callback):
    """
    Opens a file dialog to load a pipeline from a JSON file.
    
    Args:
        pipeline_state: The PipelineState instance to update
        on_complete_callback: Function to call after loading (typically to re-render UI)
    """
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


def show_artwork_detail(artwork_data):
    """
    Navigate to detail view with artwork data.
    
    Args:
        artwork_data: Dictionary containing artwork information
    """
    
    logger.info(f"Navigating to detail view for artwork: {artwork_data.get('inventory')}")
    
    # Store artwork data in detail module's page_state
    detail.page_state.set_artwork(artwork_data)
    
    # Navigate to detail route
    ui.navigate.to('/detail')
