"""
Search pipeline package.

This package provides the search pipeline functionality for the Fabritius-NG application.
It includes state management, operator execution, and UI rendering components.

Main entry point: render_search()
"""

# Initialize operator registry on module import
from .operator_registration import register_all_operators
register_all_operators()

