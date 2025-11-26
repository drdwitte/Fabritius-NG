"""
Hensor Workbench - Main Entry Point.
AI-powered CMS for the Royal Museums of Fine Arts of Belgium.
"""

from nicegui import ui
from ui_components.header import HeaderBuilder, report_click
from ui_components.config import *

from pages.home import render_home
from pages.search import render_search
from pages.detail import render_detail
from pages.label import render_label
from pages.chat import render_chat
from pages.insights import render_insights
from pages.login import render_login

def open_page(title):
    # Convert button title to lowercase and open the corresponding route
    route = '/' if title.lower() == 'home' else f'/{title.lower()}'
    ui.notify(f'Navigating to: {route}', position='bottom')
    ui.navigate.to(route)

def build_header():
    header = (
        HeaderBuilder()
        .with_title(TITLE)
        .with_subtitle(SUBTITLE)
        .with_login_button(LOGIN_LABEL, lambda l=LOGIN_LABEL: open_page(l))
    )
    for label in BUTTON_LABELS:
        header.with_button(label, lambda l=label: open_page(l))
    header.build()

# Dictionary: route -> render function
ROUTES = {
    '/': render_home,
    '/search': render_search,
    '/detail': render_detail,
    '/label': render_label,
    '/chat': render_chat,
    '/insights': render_insights,
    '/login': render_login,
}

# Dynamisch routes aanmaken
for route, render_func in ROUTES.items():
    @ui.page(route)
    def _page(render_func=render_func):
        build_header()
        # Sidebar placeholder
        render_func(ui)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Hensor Workbench', port=8080)

