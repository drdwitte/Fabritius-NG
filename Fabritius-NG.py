"""
Hensor Workbench - Main Entry Point.
AI-powered CMS for the Royal Museums of Fine Arts of Belgium.
"""

from nicegui import ui
from ui_components.header import HeaderBuilder, report_click
from ui_components.config import *



def setup_ui() -> None:
    
    builder = (
        HeaderBuilder()
        .with_title(TITLE)
        .with_subtitle(SUBTITLE)
    )
    
    for label in BUTTON_LABELS:
        builder.with_button(label, report_click)
    
    builder.with_login_button(LOGIN_LABEL).build()

if __name__ in {"__main__", "__mp_main__"}:
    setup_ui()
    ui.run(title='Hensor Workbench', port=8080)

