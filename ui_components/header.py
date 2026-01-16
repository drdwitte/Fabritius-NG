from nicegui import ui
from typing import Callable
from config import settings, RESET_QUASAR_COLORS
from loguru import logger
import routes

def navigate_to(route: str) -> Callable:
    """
    Create a navigation callback for the given route.
    Returns a closure (=callable function) that navigates to the route when called.
    This allows configuring the route NOW, but executing navigation LATER (on button click).
    Example: navigate_to(routes.ROUTE_HOME) returns a function that navigates to '/'
    
    Args:
        route: Route constant from routes.py
        
    Returns:
        Function that navigates to the specified route when called
    """
    def _navigate():
        logger.info(f"Navigating to route: {route}")
        ui.navigate.to(route)
    return _navigate

def render_header():
    """
    Render the application header with navigation buttons.
    Uses the Builder pattern: configure header via method chaining,
    then call .build() to actually render it to the DOM.
    """
    header = (
        HeaderBuilder()
        .with_title(settings.title)
        .with_subtitle(settings.subtitle)
        .with_button('Search', navigate_to(routes.ROUTE_SEARCH))
        .with_button('Detail', navigate_to(routes.ROUTE_DETAIL))
        .with_button('Label', navigate_to(routes.ROUTE_LABEL))
        .with_button('Chat', navigate_to(routes.ROUTE_CHAT))
        .with_button('Insights', navigate_to(routes.ROUTE_INSIGHTS))
        .with_login_button(settings.login_label, navigate_to(routes.ROUTE_LOGIN))
    )
    header.build()


class HeaderBuilder:
    """
    Builder for the application header.
    Uses the Builder pattern to construct complex UI components step-by-step.
    All with_* methods return self to enable fluent method chaining.
    """
    def __init__(self):
        self.logo = settings.logo
        self.logo_link = settings.logo_link
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
    
    def _create_nav_button(self, label: str, on_click_callback: Callable):
        """Helper to create a navigation button with consistent styling."""
        button = ui.button(label, on_click=on_click_callback)
        # Reset Quasar's default color props to allow full Tailwind control
        button.props(RESET_QUASAR_COLORS)
        button.classes(
            'bg-white text-[{}] font-bold px-4 py-2 rounded'.format(settings.primary_color) # Use primary color for text
        )
    
    def _create_login_button(self, label: str, on_click_callback: Callable):
        """Helper to create a login button with primary styling."""
        button = ui.button(label, on_click=on_click_callback if on_click_callback else None)
        # Reset Quasar's default color props to allow full Tailwind control
        button.props(RESET_QUASAR_COLORS)
        button.classes(
            'bg-[{}] text-white font-bold px-4 py-2 rounded'.format(settings.primary_color) # Use primary color for background
        )

    def build(self): 
        with ui.header().classes('flex items-center bg-white  px-8 py-4 shadow-md'):
            
            # Logo container: using plain div instead of ui.row(), because those add flexbox layout which interferes with aspect-ratio.
            # A simple fixed-size container is all we need here. (otherwise dimensions of logo get distorted)
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
                    self._create_nav_button(label, on_click_callback)

                # Login button with distinct style
                if self.login_button:
                    label, on_click_callback = self.login_button
                    self._create_login_button(label, on_click_callback)