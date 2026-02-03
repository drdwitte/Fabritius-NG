"""
Level column view component.

Renders a single column with results (AI algorithm or validated data).
"""

from nicegui import ui
from typing import List, Dict, Any, Optional

from label_tool.level_config import ValidationLevel
from label_tool.state import ValidationResults


def render_level_column(
    level: Optional[ValidationLevel],
    results: ValidationResults,
    column_label: str = None
) -> None:
    """
    Render a result column.
    
    Args:
        level: Validation level configuration (None for AI/custom columns)
        results: Results for this column
        column_label: Override label (used for AI columns)
    """
    # Determine label and color
    if column_label:
        label = column_label
        color = "purple-600"  # Default color for AI columns
    elif level:
        label = level.display_name
        color = level.color
    else:
        label = results.column_label
        color = "gray-600"
    
    with ui.column().classes('flex-1 bg-white rounded-lg shadow-md p-4'):
        # Column header
        with ui.row().classes('w-full items-center justify-between mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('label').classes(f'text-{color}')
                ui.label(label).classes('text-lg font-bold')
            
            # Result count badge
            if results.total_count > 0:
                with ui.badge(results.total_count).props(f'color={color}'):
                    pass
        
        # Loading state
        if results.is_loading:
            with ui.column().classes('w-full items-center justify-center py-8'):
                ui.spinner(size='lg', color=color)
                ui.label('Loading results...').classes('text-sm text-gray-500 mt-2')
            return
        
        # Error state
        if results.error:
            with ui.column().classes('w-full items-center justify-center py-8'):
                ui.icon('error').classes('text-red-500 text-3xl')
                ui.label(f'Error: {results.error}').classes('text-sm text-red-500 mt-2')
            return
        
        # Empty state
        if results.total_count == 0:
            with ui.column().classes('w-full items-center justify-center py-8'):
                ui.icon('inbox').classes('text-gray-300 text-3xl')
                ui.label('No results yet').classes('text-sm text-gray-400 mt-2')
            return
        
        # Results list
        with ui.column().classes('w-full gap-2'):
            for artwork in results.results:
                render_result_card(artwork, color)


def render_result_card(artwork: Dict[str, Any], color: str) -> None:
    """
    Render a single artwork result card.
    
    Args:
        artwork: Artwork data
        color: Tailwind color for accent
    """
    with ui.card().classes('w-full p-3 cursor-pointer hover:shadow-lg transition-shadow'):
        with ui.row().classes('w-full items-start gap-3'):
            # Artwork image or placeholder
            if artwork.get('image_url'):
                with ui.element('div').classes('w-24 h-24 rounded overflow-hidden flex-shrink-0'):
                    ui.image(artwork['image_url']).classes('w-full h-full object-cover')
            else:
                with ui.element('div').classes(
                    f'w-24 h-24 bg-{color} bg-opacity-10 rounded flex items-center justify-center flex-shrink-0'
                ):
                    ui.icon('image').classes(f'text-{color} text-3xl')
            
            # Artwork info
            with ui.column().classes('flex-1 gap-1 min-w-0'):
                ui.label(artwork.get('title', 'Untitled')).classes('font-semibold text-sm truncate')
                
                if artwork.get('artist'):
                    ui.label(artwork['artist']).classes('text-xs text-gray-600 truncate')
                
                if artwork.get('date'):
                    ui.label(artwork['date']).classes('text-xs text-gray-500')
                
                # Confidence score (for AI results)
                if artwork.get('confidence'):
                    confidence_pct = int(artwork['confidence'] * 100)
                    with ui.row().classes('items-center gap-1 mt-1'):
                        ui.icon('check_circle').classes(f'text-{color} text-xs')
                        ui.label(f'{confidence_pct}%').classes('text-xs text-gray-600')
                
                # Algorithm name (for AI results)
                if artwork.get('algorithm'):
                    with ui.badge(artwork['algorithm']).props(f'color={color}').classes('text-xs mt-1'):
                        pass
                
                # Validation level (for validated results)
                if artwork.get('validation_level'):
                    ui.label(f"✓ {artwork['validation_level']}").classes(f'text-xs text-{color} mt-1')
