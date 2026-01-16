from nicegui import ui
from ui_components.header import render_header
from loguru import logger
import routes


def render_label(ui_module) -> None:
    ui_module.label('Label').classes('text-2xl font-bold')


@ui.page(routes.ROUTE_LABEL)
def page() -> None:
    """Label tool page."""  
    logger.info("Loading Label page")
    render_header()
    render_label(ui)