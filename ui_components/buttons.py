"""
Reusable button components for the Fabritius-NG application.
"""

from nicegui import ui


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
