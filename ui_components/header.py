from nicegui import ui
from ui_components.config import BROWN

def report_click(label):
    ui.notify(f'Report: {label} was clicked!', position='bottom')

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
                    ).props('color=none text-color=none').classes(f'bg-white text-[{BROWN}] font-bold px-4 py-2 rounded')
                    #.props call removes quasar default styles; then these are overwritten with classes from tailwind

                # Login button with distinct style
                if self.login_button:
                    label, on_click_callback = self.login_button
                    ui.button(
                        label,
                        on_click=on_click_callback if on_click_callback else None
                    ).props('color=none text-color=none').classes(f'bg-[{BROWN}] text-white font-bold px-4 py-2 rounded')
                    #.props call removes quasar default styles; then these are overwritten with classes from tailwind