"""
core assistant module

this module provides the core functionality for the e-commerce ai assistant,
including query processing, conversation management, and query routing
this is the central orchestration layer that coordinates between different
components of the system
"""

from .base import AssistantManager
from .memory import ConversationMemory
from .router import QueryRouter

__version__ = "1.0.0"

class AssistantError(Exception):
    """Base exception for assistant-related errors."""
    pass

class QueryProcessingError(AssistantError):
    """Raised when there's an error processing a query."""
    def __init__(self, message: str, query: str, *args):
        self.query = query
        super().__init__(f"Error processing query '{query}': {message}", *args)

class MemoryError(AssistantError):
    """Raised when there's an error with conversation memory."""
    def __init__(self, message: str, conversation_id: str, *args):
        self.conversation_id = conversation_id
        super().__init__(f"Memory error for conversation '{conversation_id}': {message}", *args)

class RouterError(AssistantError):
    """Raised when there's an error with query routing."""
    def __init__(self, message: str, query_type: str = None, *args):
        self.query_type = query_type
        super().__init__(f"Router error{f' for query type {query_type}' if query_type else ''}: {message}", *args)

# Version information
VERSION_INFO = {
    "version": __version__,
    "components": {
        "AssistantManager": "1.0.0",
        "ConversationMemory": "1.0.0",
        "QueryRouter": "1.0.0"
    }
}

__all__ = [
    "AssistantManager",
    "ConversationMemory",
    "QueryRouter",
    "AssistantError",
    "QueryProcessingError",
    "MemoryError",
    "RouterError",
    "VERSION_INFO"
]

def get_version() -> str:
    """Get the current version of the assistant module."""
    return __version__

def get_component_versions() -> dict:
    """Get version information for all components."""
    return VERSION_INFO["components"]

async def create_assistant() -> AssistantManager:
    """
    Factory function to create and initialize an AssistantManager instance.
    
    Returns:
        AssistantManager: Initialized assistant manager
        
    Example:
        >>> assistant = await create_assistant()
        >>> response = await assistant.process_message(
        ...     message="What were my total sales?",
        ...     conversation_id="conv_123",
        ...     active_platforms={"shopify", "amazon"}
        ... )
    """
    assistant = AssistantManager()
    await assistant.initialize()
    return assistant

# Optional: Add debug information when in development
if __debug__:
    def get_debug_info() -> dict:
        """Get debug information about the assistant module."""
        return {
            "version": __version__,
            "components": VERSION_INFO["components"],
            "memory_settings": {
                "max_history": ConversationMemory.max_history,
                "save_format": "json"
            },
            "router_settings": {
                "supported_query_types": list(QueryRouter.query_patterns.keys())
            }
        }
    
    __all__.append("get_debug_info")