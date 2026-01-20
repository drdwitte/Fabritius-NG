"""
Application route constants.

Centralized route definitions to avoid magic strings and ensure consistency.
Used in both @ui.page() decorators and ui.navigate.to() calls.
"""

from config import settings

# Apply base path from settings (e.g., "/fabritius" for reverse proxy)
def _with_base(path: str) -> str:
    """Prepend base_path to route if configured."""
    base = settings.base_path.rstrip('/')
    return f"{base}{path}" if base else path

# Main application routes
ROUTE_HOME = _with_base('/')
ROUTE_SEARCH = _with_base('/search')
ROUTE_DETAIL = _with_base('/detail')
ROUTE_LABEL = _with_base('/label')
ROUTE_CHAT = _with_base('/chat')
ROUTE_INSIGHTS = _with_base('/insights')
ROUTE_LOGIN = _with_base('/login')
