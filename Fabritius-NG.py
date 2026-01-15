"""
Hensor Workbench - Main Entry Point.
AI-powered CMS for the Royal Museums of Fine Arts of Belgium.

This is the application entry point. It imports all page modules
(which register their own routes via @ui.page decorators) and starts the server.
"""

from nicegui import ui
from config import settings

# Import all pages to register their routes
# Each page module uses @ui.page('/route') to register itself
import pages.search
import pages.detail
import pages.label
import pages.chat
import pages.insights
import pages.login

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title=settings.title,
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
