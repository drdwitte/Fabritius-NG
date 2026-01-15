from nicegui import ui
from ui_components.header import build_header


def render_login(ui_module) -> None:
    ui_module.label('Login').classes('text-2xl font-bold')


@ui.page('/login')
def page() -> None:
    """Login page."""
    build_header()
    render_login(ui)