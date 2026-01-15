from nicegui import ui
from ui_components.header import build_header


def render_label(ui_module) -> None:
    ui_module.label('Label').classes('text-2xl font-bold')


@ui.page('/label')
def page() -> None:
    """Label tool page."""  
    build_header()
    render_label(ui)