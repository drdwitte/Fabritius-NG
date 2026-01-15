from nicegui import ui
from ui_components.header import build_header
from loguru import logger


def render_insights(ui_module) -> None:
    ui_module.label('Insights').classes('text-2xl font-bold')


@ui.page('/insights')
def page() -> None:
    """Analytics and insights page."""
    logger.info("Loading Insights page")
    build_header()
    render_insights(ui)