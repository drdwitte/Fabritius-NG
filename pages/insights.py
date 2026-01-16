from nicegui import ui
from ui_components.header import render_header
from loguru import logger
import routes


def render_insights(ui_module) -> None:
    ui_module.label('Insights').classes('text-2xl font-bold')


@ui.page(routes.ROUTE_INSIGHTS)
def page() -> None:
    """Analytics and insights page."""
    logger.info("Loading Insights page")
    render_header()
    render_insights(ui)