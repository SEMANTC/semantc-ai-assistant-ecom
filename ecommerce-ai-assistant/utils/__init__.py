"""
utility modules for the e-commerce ai assistant

this package contains various utility functions and classes used throughout
the application, including logging, timing, and other helper functions
"""

from .logger import (
    setup_logging,
    get_logger,
    LogContext,
    log_execution_time
)

__all__ = [
    'setup_logging',
    'get_logger',
    'LogContext',
    'log_execution_time'
]