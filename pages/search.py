from nicegui import ui
from ui_components.config import BROWN



#global variable
pipeline = [
    'Metadata Filter',
    'Semantic Search',
    'Similarity Search'
]  # list of operators in the current pipeline

pipeline_bar = None  # will be a ui.column()

def render_search(ui):
    ui.add_head_html("<script src=\"https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js\"></script>")    


    #title
    with ui.row().classes('items-center gap-2 mb-2'):
        ui.icon('search').classes('text-2xl text-amber-700')
        ui.label('Search Pipeline').classes('text-2xl font-bold')

    # Top bar: full width, left input, right buttons
    with ui.row().props('flat').classes('w-full flex items-center justify-between bg-white shadow-sm px-4 py-2 mb-4 rounded'):
 
        # Left: input field
        ( 
            ui.element('input')
                .props('type=text placeholder="Pipeline name" value="Untitled Pipeline"')
                .classes(
                    'h-9 w-64 rounded-md border border-gray-300 bg-white '
                    'px-3 py-1 shadow-sm text-gray-800 placeholder-gray-400 '
                    'focus:outline-none focus:ring-1 focus:ring-gray-400'
                ) #focus: activates border when clicking on text field  
        )
     
        # Right: buttons
        with ui.row().classes('gap-2'):
            icon_button('folder_open', 'Load', lambda: ui.notify('Load clicked'))
            icon_button('save', 'Save', lambda: ui.notify('Save clicked'))
            run_button('Run', lambda: ui.notify('Run clicked'))
    
    # Layout: sidebar + main content
    with ui.row().classes('w-full'):
        
        # Sidebar (left), titled OPERATOR LIBRARY
        with ui.column().classes('w-80 p-4 bg-gray-50 rounded-xl gap-4'):
            ui.label('OPERATOR LIBRARY').classes('text-sm font-bold text-gray-600 mb-2')

            operator_card(
                'filter_alt',
                'Metadata Filter',
                'Filter artworks by metadata attributes',
                lambda: ui.notify('Metadata Filter added')
            )
       
            operator_card(
                'search',
                'Semantic Search',
                'Text-based semantic search using AI',
                lambda: ui.notify('Semantic Search added')
            )

            operator_card(
                'library_books',
                'Similarity Search',
                'Find visually similar artworks',
                lambda: ui.notify('Similarity Search added')
            )

            operator_card(
                'palette',
                'Color Filter',
                'Filter artworks by color attributes',
                lambda: ui.notify('Color Filter added')
            )

            operator_card(
                'accessibility_new',
                'Pose Search',
                'Find artworks with similar human poses',
                lambda: ui.notify('Pose Search added')
            )

            operator_card(
                'brush',
                'Sketch Search',
                'Search by drawing or uploading a sketch',
                lambda: ui.notify('Sketch Search added')
            )

        
        # Main content (right)
        with ui.column().classes('flex-grow p-4'):
            ui.label('OPERATOR CHAIN').classes('text-xl font-bold mb-2')
            render_pipeline()  # <-- direct call, no pipeline_bar
            ui.label('Results will appear here...')
            

def icon_button(icon_name, label, on_click, bg='bg-white', text='text-gray-700', border='border-gray-300'):
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes(f'h-9 px-3 flex items-center gap-x-8 rounded-md '
                f'border {border} {bg} {text} hover:bg-gray-50 py-1')
    with btn:
        ui.icon(icon_name).classes(f'{text} text-lg')
        ui.label(label).classes(f'{text} text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn

def run_button(label, on_click):
    btn = ui.button(on_click=on_click)
    btn.props('color=none text-color=none')
    btn.classes('h-9 px-3 flex items-center gap-x-8 rounded-md '
                'border border-gray-900 bg-black text-white hover:bg-gray-800 py-1')
    with btn:
        ui.icon('play_arrow').classes('text-white text-lg')
        ui.label(label).classes('text-white text-base font-bold').style('text-transform: none; margin-left: 10px;')
    return btn
 
def operator_card(icon, title, description, on_add):
    """
    Operator card component (for example 'Semantic Search'is (icon, title, description, and operator on_add)
    """
    with ui.row().classes('w-full items-center gap-3 p-3 rounded-lg bg-white shadow hover:bg-gray-100 transition'):
        # operator icon 
        ui.icon(icon).classes(f'text-3xl text-[{BROWN}]')
        
        # operator title + description
        with ui.column().classes('flex-1 items-start gap-0'):
            ui.label(title).classes('text-base font-bold text-gray-800 mb-0')
            ui.label(description).classes('text-xs text-gray-500 mt-0')
        
        # plus button to add operator
        (
            ui.button(icon='add', on_click=on_add)
                .props('round color=none text-color=none')
                .classes(f'bg-[{BROWN}] text-white ml-auto text-xs p-0')
        ).props('draggable=true')
        
def render_pipeline():
    active_operator = 0  # or whatever logic you want

    # Pure div as container, no parent NiceGUI row/column
    with ui.element('div').props('id=pipeline-container').classes('flex items-start gap-4 bg-white p-4 rounded'):
        for idx, op in enumerate(pipeline):
            icon = {
                'Metadata Filter': 'filter_alt',
                'Semantic Search': 'search',
                'Similarity Search': 'library_books'
            }.get(op, 'tune')

            if idx == active_operator:
                tile_classes = f'flex flex-col gap-0 px-2 py-2 rounded-xl border bg-white shadow-sm border-[{BROWN}] min-w-[180px]'
            else:
                tile_classes = 'flex flex-col gap-0 px-2 py-2 rounded-xl bg-white shadow-sm min-w-[180px]'

            with ui.element('div').classes(tile_classes):
                with ui.row().classes('items-center w-full'):
                    ui.icon('drag_indicator').classes('text-xl text-gray-400 cursor-move')
                    ui.icon(icon).classes('text-xl text-gray-700')
                    ui.label(op).classes('text-gray-800 font-medium ml-2')
                ui.label("param1: value").classes('text-sm text-gray-400 italic w-full mt-2')
                ui.label("param2: value").classes('text-sm text-gray-400 italic w-full')
                ui.label("89 results").classes(
                    f'inline-block mt-3 px-2 py-1 text-xs font-medium '
                    f'rounded-md bg-[{BROWN}] text-white'
                )

    ui.run_javascript("""
    new Sortable(document.getElementById('pipeline-container'), {
        animation: 150,
        ghostClass: 'opacity-50'
    });
    """)





