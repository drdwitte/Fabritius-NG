from nicegui import ui
from ui_components.header import render_header
from loguru import logger
import routes


def render_login(ui_module) -> None:
    ui_module.label('Login').classes('text-2xl font-bold')


@ui.page(routes.ROUTE_LOGIN)
def page() -> None:
    """Login page."""
    logger.info("Loading Login page")
    render_header()
    render_login(ui)