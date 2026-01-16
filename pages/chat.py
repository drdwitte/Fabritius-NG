from nicegui import ui
from ui_components.header import render_header
from loguru import logger
import routes


def render_chat(ui_module) -> None:
    ui_module.label('Chat').classes('text-2xl font-bold')


@ui.page(routes.ROUTE_CHAT)
def page() -> None:
    """Chat interface page."""
    logger.info("Loading Chat page")
    render_header()
    render_chat(ui)