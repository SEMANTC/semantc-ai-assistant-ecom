# ecommerce-ai-assistant/app/config/__init__.py
"""
configuration package

this package handles all configuration management for the application,
including environment variables, settings, and constants
"""

from .settings import Settings, EnvironmentType

# create a global settings instance
settings = Settings()

__all__ = ["settings", "Settings", "EnvironmentType"]