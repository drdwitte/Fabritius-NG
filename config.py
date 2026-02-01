"""
Application configuration using Pydantic Settings.
* Pydantic is a data validation library (specifically typing and settings management)
* Pydantic Settings is used for environment variable support

This module provides environment-aware configuration management.
Values can be overridden via environment variables or .env file.
"""

from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Quasar component property string to reset default colors and enable full Tailwind control, use as .setProps(RESET_QUASAR_COLORS) argument
RESET_QUASAR_COLORS = 'color=none text-color=none'

class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Environment variables are loaded from .env file if present.
    Prefix with 'FABRITIUS_' to override any setting.
    
    Example .env:
        FABRITIUS_BROWN="#8b4513"
        FABRITIUS_IMAGE_BASE_URL="https://www.opac-fabritius.be"
        FABRITIUS_PREVIEW_RESULTS_COUNT=10
    """
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='FABRITIUS_', #prefix the environment variables
        case_sensitive=False
    )
    
    # Application metadata
    #Pydantic syntax: type hints for validation, default values, descriptions for documentation
    title: str = Field(default='Hensor Workbench', description='Application title')
    subtitle: str = Field(default='an AI-powered CMS', description='Application subtitle')
    base_path: str = Field(default='', description='Base path for reverse proxy deployment (e.g., "/fabritius" for nginx)')
    
    # UI Configuration
    primary_color: str = Field(
        default='#8b4513', 
        description='Primary theme color for UI (default: brown)'
    )
    logo: str = Field(
        default='static/logo-kmskb.svg',
        description='Path to application logo'
    )
    logo_link: str = Field(
        default='https://fine-arts-museum.be/nl/onderzoek/digitaal-museum',
        description='External link for logo click'
    )
    max_visible_params: int = Field(
        default=3,
        ge=1,
        le=10,
        description='Maximum number of operator parameters to show in pipeline view'
    )
    button_labels: List[str] = Field(
        default=['SEARCH', 'DETAIL', 'LABEL', 'CHAT', 'INSIGHTS'],
        description='Navigation button labels'
    )
    login_label: str = Field(default='LOGIN', description='Login button label')
    
    # Image serving
    image_base_url: str = Field(
        default='https://www.opac-fabritius.be',
        description='Base URL for artwork images'
    )
    
    # Preview settings
    preview_results_count: int = Field(
        default=10,
        ge=1, # min value
        le=100, # max value
        description='Number of results to show in preview (2 rows x 5 columns)'
    )
    
    # Server settings
    host: str = Field(default='127.0.0.1', description='Server host')
    port: int = Field(default=1234, ge=1, le=65535, description='Server port')
    reload: bool = Field(default=True, description='Enable auto-reload on code changes')
    session_secret: str = Field(
        default='replace-this-with-a-real-secret-key-in-production',
        description='Secret key for encrypting user sessions (MUST be set in production!)'
    )
    
    # Backend settings
    supabase_url: str = Field(default='', description='Supabase project URL')
    supabase_key: str = Field(default='', description='Supabase anon key')
    
    # LLM settings
    openai_api_key: str = Field(default='', description='OpenAI API key')


# Global settings instance (singleton pattern)
# This is initialized once at module import and provides type-safe access
# to configuration throughout the application
settings = Settings()


def get_settings():
    """
    Get the global settings instance.
    
    This function is optional but provides:
    - Explicit function call pattern (some teams prefer this)
    - Easy to mock in tests
    - Clear dependency in function signatures
    
    Returns:
        Global Settings instance
    """
    return settings
