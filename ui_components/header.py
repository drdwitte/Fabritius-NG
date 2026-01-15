from nicegui import ui
from typing import Callable
from config import settings
from loguru import logger

def report_click(label):
    ui.notify(f'Report: {label} was clicked!', position='bottom')


def navigate_to(label: str) -> Callable:
    """
    Create a navigation callback for the given label.
    
    Returns a closure (=callable function) that navigates to the route when called.
    This allows configuring the route NOW, but executing navigation LATER (on button click).
    
    Example: navigate_to('Search') returns a function that navigates to '/search'
    
    Args:
        label: Page label ('Search', 'Detail', etc.)
        
    Returns:
        Function that navigates to /{label.lower()} when called
    """
    def _navigate() -> None:
        route = '/' if label.lower() == 'search' else f'/{label.lower()}'
        logger.info(f"Navigating to {label} page (route: {route})")
        ui.navigate.to(route)
    return _navigate


def build_header() -> None:
    """Build the application header with navigation buttons."""
    header = (
        HeaderBuilder()
        .with_title(settings.title)
        .with_subtitle(settings.subtitle)
        .with_button('Search', navigate_to('Search'))
        .with_button('Detail', navigate_to('Detail'))
        .with_button('Label', navigate_to('Label'))
        .with_button('Chat', navigate_to('Chat'))
        .with_button('Insights', navigate_to('Insights'))
        .with_login_button(settings.login_label, navigate_to(settings.login_label))
    )
    header.build()


class HeaderBuilder:
    def __init__(self):
        self.logo = 'static/logo-kmskb.svg'
        self.logo_link = 'https://fine-arts-museum.be/nl/onderzoek/digitaal-museum'
        self.title = ''
        self.subtitle = ''
        self.buttons = []
        self.login_button = None

    def with_title(self, title):
        self.title = title
        return self

    def with_subtitle(self, subtitle):
        self.subtitle = subtitle
        return self

    def with_button(self, label, on_click):
        self.buttons.append((label, on_click))
        return self

    def with_login_button(self, label, on_click):
        self.login_button = (label, on_click)
        return self

    def build(self): 
        with ui.header().classes('flex items-center bg-white  px-8 py-4 shadow-md'):
            
            # Logo
            with ui.element('div').classes('aspect-[4/1] w-32'):
                with ui.link(target=self.logo_link):
                    ui.image(self.logo).classes('h-full w-full object-contain')
            
            # Title and subtitle
            with ui.column().classes('gap-0'):
                if self.title:
                    ui.label(self.title).classes('text-black text-2xl font-bold')
                if self.subtitle:
                    ui.label(self.subtitle).classes('text-gray-500')
            
            # Navigation buttons
            with ui.row().classes('gap-2 ml-auto'):
                for label, on_click_callback in self.buttons:
                    ui.button(
                        label,
                        on_click=on_click_callback
                    ).props('color=none text-color=none').classes(f'bg-white text-[{settings.primary_color}] font-bold px-4 py-2 rounded')
                    #.props call removes quasar default styles; then these are overwritten with classes from tailwind

                # Login button with distinct style
                if self.login_button:
                    label, on_click_callback = self.login_button
                    ui.button(
                        label,
                        on_click=on_click_callback if on_click_callback else None
                    ).props('color=none text-color=none').classes(f'bg-[{settings.primary_color}] text-white font-bold px-4 py-2 rounded')
                    #.props call removes quasar default styles; then these are overwritten with classes from tailwind