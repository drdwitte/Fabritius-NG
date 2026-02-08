from nicegui import ui, app
from ui_components.header import render_header
from loguru import logger
import routes
import uuid
from backend.llms import LLMClient
from typing import List, Dict, Optional


# Module-level storage for chat controllers (same pattern as label/search pages)
# Safe for concurrent users - each browser tab gets unique UUID
_chat_controllers = {}

# System context about KMSKB from Wikipedia
KMSKB_CONTEXT = """
You are an AI assistant for the Royal Museums of Fine Arts of Belgium (KMSKB).

ABOUT THE ROYAL MUSEUMS OF FINE ARTS OF BELGIUM:
The Royal Museums of Fine Arts of Belgium (French: Musées royaux des Beaux-Arts de Belgique, Dutch: Koninklijke Musea voor Schone Kunsten van België) are a group of art museums in Brussels, Belgium.

HISTORY:
- Founded on September 1, 1801 by Napoleon
- Opened in 1803 as the Museum of Fine Arts of Brussels
- Initially occupied the former Palace of Charles of Lorraine (the "Old Court")
- In 1841, the museum was ceded to the Belgian State
- In 1919, renamed to Royal Museum of Fine Arts of Belgium
- In 1927, renamed again to its current name: Royal Museums of Fine Arts of Belgium
- The museum moved to its current location at Rue de la Régence/Regentschapsstraat in 1887 (Alphonse Balat's Palace of Fine Arts)

COLLECTIONS:
The Royal Museums contain over 20,000 drawings, sculptures, and paintings, covering a period from the early 15th century to the present. They are the most popular art institution and most visited museum complex in Belgium.

KEY MUSEUMS IN THE COMPLEX:
1. Oldmasters Museum - Extensive collection of European paintings, sculptures and drawings from 15th to 18th centuries, featuring Flemish Primitives and Old Masters
2. Magritte Museum (opened 2009) - World's largest collection of René Magritte works (approx. 200 paintings, drawings, sculptures)
3. Fin-de-Siècle Museum (opened 2013) - Art from late 19th and early 20th century when Brussels was capital of Art Nouveau
4. Wiertz Museum - Dedicated to Antoine Wiertz, Belgian romantic artist
5. Meunier Museum - Dedicated to Constantin Meunier, realist painter and sculptor

NOTABLE ARTISTS IN THE COLLECTION:
- Flemish Primitives: Pieter Bruegel the Elder, Rogier van der Weyden, Robert Campin, Hieronymus Bosch
- Old Masters: Peter Paul Rubens (dedicated "Rubens Room" with 20+ paintings), Anthony van Dyck, Jacob Jordaens
- Modern: René Magritte (surrealist), James Ensor, Constantin Meunier, Henri Evenepoel, Fernand Khnopff
- International: Rembrandt, Hendrick Goltzius, Jacob de Gheyn II, and many others

FAMOUS WORKS:
- "Landscape with the Fall of Icarus" by Pieter Bruegel the Elder (c. 1558)
- "The Empire of Light" by René Magritte
- Over 20 paintings by Rubens in the dedicated Rubens Room

VISITOR STATISTICS:
- Most popular art institution in Belgium
- Approximately 715,000 visitors in 2010
- Peak attendance of 767,355 visitors in 2015
- Top 100 most visited museums in the world
- Magritte Museum alone received about 425,000 visitors in 2010

CURRENT DIRECTOR:
Kim Oosterlinck (2024-ongoing)

Your role is to assist users with questions about the collection, help them explore artworks, provide information about artists and art movements, and support their research. Be knowledgeable, helpful, and enthusiastic about art and the museum's collections.
"""


class ChatPageController:
    """Controller for chat page state and LLM interactions."""
    
    def __init__(self):
        self.messages: List[Dict[str, str]] = []  # [{'role': 'user'/'assistant', 'content': '...'}]
        self.llm_client: Optional[LLMClient] = None
        self.chat_container = None
        self.input_field = None
        self.send_button = None
        # Add system context as first message (not rendered, only sent to API)
        self.system_message = {'role': 'system', 'content': KMSKB_CONTEXT}
        
    def initialize_llm(self):
        """Initialize LLM client."""
        if not self.llm_client:
            self.llm_client = LLMClient()
            logger.info("LLM client initialized for chat")
    
    def add_message(self, role: str, content: str):
        """Add message to history."""
        self.messages.append({'role': role, 'content': content})
    
    def send_message(self, message: str):
        """Send user message and get AI response."""
        if not message.strip():
            return
        
        # Add user message
        self.add_message('user', message)
        self._render_message('user', message)
        
        # Clear input
        self.input_field.value = ''
        
        # Disable input during processing
        self.input_field.set_enabled(False)
        self.send_button.set_enabled(False)
        
        # Show typing indicator
        with self.chat_container:
            typing_indicator = ui.row().classes('w-full justify-start mb-4')
            with typing_indicator:
                ui.spinner(size='sm', color='primary')
                ui.label('AI is thinking...').classes('text-sm text-gray-500 ml-2')
        
        # Get AI response (async simulation)
        try:
            self.initialize_llm()
            
            # Format messages for OpenAI API - include system message first
            formatted_messages = [self.system_message] + [
                {"role": msg['role'], "content": msg['content']} 
                for msg in self.messages
            ]
            
            response = self.llm_client.prompt_llm(formatted_messages)
            
            # The responses API returns output_text directly (not choices)
            if response and hasattr(response, 'output_text'):
                ai_message = response.output_text
                self.add_message('assistant', ai_message)
                
                # Remove typing indicator
                typing_indicator.delete()
                
                # Render AI response
                self._render_message('assistant', ai_message)
            elif response and hasattr(response, 'choices'):
                # Fallback for standard chat.completions API
                ai_message = response.choices[0].message.content
                self.add_message('assistant', ai_message)
                
                # Remove typing indicator
                typing_indicator.delete()
                
                # Render AI response
                self._render_message('assistant', ai_message)
            else:
                # Remove typing indicator
                typing_indicator.delete()
                
                # Show error
                error_msg = "Sorry, an error occurred while fetching the response."
                self.add_message('assistant', error_msg)
                self._render_message('assistant', error_msg, is_error=True)
                
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            
            # Remove typing indicator
            typing_indicator.delete()
            
            # Show error
            error_msg = f"An error occurred: {str(e)}"
            self.add_message('assistant', error_msg)
            self._render_message('assistant', error_msg, is_error=True)
        
        finally:
            # Re-enable input
            self.input_field.set_enabled(True)
            self.send_button.set_enabled(True)
            self.input_field.run_method('focus')
    
    def _render_message(self, role: str, content: str, is_error: bool = False):
        """Render a single message in the chat."""
        with self.chat_container:
            # Determine alignment and styling
            if role == 'user':
                row_classes = 'w-full justify-end mb-4'
                bubble_classes = 'bg-blue-500 text-white rounded-lg px-4 py-2 max-w-[70%]'
            else:
                row_classes = 'w-full justify-start mb-4'
                if is_error:
                    bubble_classes = 'bg-red-100 text-red-800 rounded-lg px-4 py-2 max-w-[70%]'
                else:
                    bubble_classes = 'bg-gray-100 text-gray-800 rounded-lg px-4 py-2 max-w-[70%]'
            
            with ui.row().classes(row_classes):
                with ui.card().classes(bubble_classes).style('box-shadow: 0 1px 2px rgba(0,0,0,0.1)'):
                    ui.markdown(content).classes('text-sm')
    
    def render_chat_ui(self):
        """Render the chat interface."""
        with ui.column().classes('w-full max-w-4xl mx-auto h-full'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('Chat with AI Assistant').classes('text-2xl font-bold')
                ui.button(
                    'Clear conversation', 
                    icon='delete_outline',
                    on_click=self._clear_chat
                ).props('flat').classes('text-gray-600')
            
            # Chat messages container (scrollable)
            with ui.card().classes('w-full flex-grow overflow-y-auto p-4').style('min-height: 400px; max-height: 600px'):
                self.chat_container = ui.column().classes('w-full gap-0')
                
                # Welcome message
                if not self.messages:
                    with self.chat_container:
                        with ui.row().classes('w-full justify-center mb-4'):
                            with ui.card().classes('bg-blue-50 text-blue-800 rounded-lg px-6 py-4 max-w-[80%] text-center'):
                                ui.label('👋 Hello! I\'m your AI assistant for the Royal Museums of Fine Arts of Belgium.').classes('text-lg font-semibold mb-2')
                                ui.label('Ask me about artworks, artists, museum collections, or get help with your research.').classes('text-sm')
                else:
                    # Render existing messages
                    for msg in self.messages:
                        self._render_message(msg['role'], msg['content'])
            
            # Input area
            with ui.row().classes('w-full gap-2 mt-4'):
                self.input_field = ui.input(
                    placeholder='Type your message here...',
                ).classes('flex-grow').props('outlined dense')
                
                # Send on Enter key - define handler that accesses current value
                def handle_enter():
                    if self.input_field.value:  # Only send if not empty
                        self.send_message(self.input_field.value)
                
                self.input_field.on('keydown.enter', handle_enter)
                
                self.send_button = ui.button(
                    icon='send',
                    on_click=lambda: self.send_message(self.input_field.value)
                ).props('flat').classes('text-blue-600')
            
            # Tips
            with ui.row().classes('w-full justify-center mt-2'):
                ui.label('💡 Tip: Ask about Flemish Masters, Magritte, Bruegel, museum collections, or use chat as research assistant').classes('text-xs text-gray-500')
    
    def _clear_chat(self):
        """Clear chat history."""
        self.messages.clear()
        if self.llm_client:
            self.llm_client.last_response_id = None  # Reset conversation context
        self.chat_container.clear()
        
        # Show welcome message again
        with self.chat_container:
            with ui.row().classes('w-full justify-center mb-4'):
                with ui.card().classes('bg-blue-50 text-blue-800 rounded-lg px-6 py-4 max-w-[80%] text-center'):
                    ui.label('👋 Hello! I\'m your AI assistant for the Royal Museums of Fine Arts of Belgium.').classes('text-lg font-semibold mb-2')
                    ui.label('Ask me about artworks, artists, museum collections, or get help with your research.').classes('text-sm')
        
        ui.notify('Conversation cleared', type='info')


@ui.page(routes.ROUTE_CHAT)
def page() -> None:
    """Chat interface page."""
    logger.info("Loading Chat page")
    
    # Get or create unique tab ID from browser storage (persists across navigations)
    if 'tab_id' not in app.storage.browser:
        app.storage.browser['tab_id'] = str(uuid.uuid4())
    
    tab_id = app.storage.browser['tab_id']
    
    # Get or create controller for this tab
    if tab_id not in _chat_controllers:
        logger.info(f"Creating new ChatPageController for tab {tab_id[:8]}")
        _chat_controllers[tab_id] = ChatPageController()
    else:
        logger.info(f"Reusing ChatPageController for tab {tab_id[:8]}")
    
    controller = _chat_controllers[tab_id]
    
    render_header()
    controller.render_chat_ui()