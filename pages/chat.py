from nicegui import ui
from ui_components.header import build_header


def render_chat(ui_module) -> None:
    ui_module.label('Chat').classes('text-2xl font-bold')


@ui.page('/chat')
def page() -> None:
    """Chat interface page."""
    build_header()
    render_chat(ui)