"""
Hensor Workbench - Main Entry Point.
AI-powered CMS for the Royal Museums of Fine Arts of Belgium.
"""

from nicegui import ui
from ui_components.header import HeaderBuilder, report_click
from ui_components.config import *

from pages.search import render_search
from pages.detail import render_detail
from pages.label import render_label
from pages.chat import render_chat
from pages.insights import render_insights
from pages.login import render_login

def navigate_to(label):
    def _navigate(_=None):
        route = '/' if label.lower() == 'search' else f'/{label.lower()}'
        print(f'Navigating to: {route}')  # Debug print
        ui.navigate.to(route)
    return _navigate

def build_header():
    header = (
        HeaderBuilder()
        .with_title(TITLE)
        .with_subtitle(SUBTITLE)
        .with_button('Search', navigate_to('Search'))
        .with_button('Detail', navigate_to('Detail'))
        .with_button('Label', navigate_to('Label'))
        .with_button('Chat', navigate_to('Chat'))
        .with_button('Insights', navigate_to('Insights'))
        .with_login_button(LOGIN_LABEL, navigate_to(LOGIN_LABEL))
    )
    header.build()

# Dictionary: route -> render function

ROUTES = {
    '/': render_search,  # Standaard route is now search
    '/search': render_search,
    '/detail': render_detail,
    '/label': render_label,
    '/chat': render_chat,
    '/insights': render_insights,
    '/login': render_login,
}

# Dynamically create routes
for route, render_func in ROUTES.items():
    @ui.page(route)
    def _page(render_func=render_func):
        build_header()
        # Sidebar placeholder
        render_func(ui)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Hensor Workbench', port=1234, reload=True)
