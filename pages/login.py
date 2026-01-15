from nicegui import ui
from ui_components.header import build_header
from loguru import logger


def render_login(ui_module) -> None:
    ui_module.label('Login').classes('text-2xl font-bold')


@ui.page('/login')
def page() -> None:
    """Login page."""
    logger.info("Loading Login page")
    build_header()
    render_login(ui)