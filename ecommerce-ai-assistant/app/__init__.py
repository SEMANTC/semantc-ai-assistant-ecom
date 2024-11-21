"""
e-commerce ai assistant application

this package contains the main fastapi application and its configurations
the application provides a natural language interface for querying
e-commerce data stored in bigquery, supporting multiple platforms
like shopify, amazon, and ebay

features:
- natural language to sql conversion
- multi-platform data querying
- structured logging
- health monitoring
- error handling
"""

__version__ = "1.0.0"
__author__ = "SEMANTC AI"
__license__ = "Proprietary"

import os
import logging
from pathlib import Path

# ensure all required directories exist
def ensure_directories():
    """ENSURE ALL REQUIRED APPLICATION DIRECTORIES EXIST"""
    base_dir = Path(__file__).parent.parent
    
    directories = [
        base_dir / "logs",
        base_dir / "cache",
        base_dir / "tmp"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)

# initialize directories
ensure_directories()

# initialize logging
logging.getLogger("uvicorn.access").handlers = []

# export the fastapi application
from .main import app

__all__ = ["app"]

def get_app_path() -> Path:
    """GET THE APPLICATION BASE DIRECTORY PATH"""
    return Path(__file__).parent.parent

def get_version() -> str:
    """GET THE CURRENT APPLICATION VERSION"""
    return __version__