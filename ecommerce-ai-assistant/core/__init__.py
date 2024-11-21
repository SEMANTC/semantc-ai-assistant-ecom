# ecommerce-ai-assistant/core/__init__.py
"""
core module for e-commerce ai assistant

this is the main core package that provides the fundamental components
for the e-commerce ai assistant, including natural language processing,
sql generation, bigquery integration, and metadata management
"""

from .assistant import (
    AssistantManager,
    ConversationMemory,
    QueryRouter,
    AssistantError,
    QueryProcessingError
)

from .sql import (
    SQLGenerator,
    SQLValidator
)

from .bigquery import (
    BigQueryClient,
    format_schema_field,
    clean_column_name,
    format_value_for_bigquery
)

from .metadata import (
    SchemaRegistry
)

__version__ = "1.0.0"

# Component version information
COMPONENT_VERSIONS = {
    "assistant": "1.0.0",
    "sql": "1.0.0",
    "bigquery": "1.0.0",
    "metadata": "1.0.0"
}

class CoreError(Exception):
    """Base exception for core-related errors."""
    pass

async def create_engine(
    project_id: str = None,
    dataset_id: str = None,
    **kwargs
) -> AssistantManager:
    """
    Factory function to create and initialize all core components.
    
    Args:
        project_id: Optional Google Cloud project ID
        dataset_id: Optional BigQuery dataset ID
        **kwargs: Additional configuration options
        
    Returns:
        AssistantManager: Fully initialized assistant manager
        
    Example:
        >>> engine = await create_engine(
        ...     project_id="my-project",
        ...     dataset_id="my_dataset"
        ... )
        >>> response = await engine.process_message(
        ...     message="Show me sales from last month",
        ...     conversation_id="conv_123",
        ...     active_platforms={"shopify"}
        ... )
    """
    try:
        # Initialize components in the correct order
        schema_registry = SchemaRegistry()
        await schema_registry.initialize()
        
        bq_client = BigQueryClient()
        await bq_client.initialize()
        
        query_router = QueryRouter()
        await query_router.initialize(schema_registry)
        
        assistant = AssistantManager()
        await assistant.initialize()
        
        return assistant
        
    except Exception as e:
        raise CoreError(f"Failed to initialize core components: {str(e)}")

# Export public interface
__all__ = [
    # Main components
    "AssistantManager",
    "ConversationMemory",
    "QueryRouter",
    "SQLGenerator",
    "SQLValidator",
    "BigQueryClient",
    "SchemaRegistry",
    
    # Factory function
    "create_engine",
    
    # Exceptions
    "CoreError",
    "AssistantError",
    "QueryProcessingError",
    
    # Utility functions
    "format_schema_field",
    "clean_column_name",
    "format_value_for_bigquery",
    
    # Version information
    "COMPONENT_VERSIONS"
]

def get_version() -> str:
    """Get the current version of the core package."""
    return __version__

def get_component_versions() -> dict:
    """Get version information for all components."""
    return COMPONENT_VERSIONS.copy()

# Debug information
if __debug__:
    def get_debug_info() -> dict:
        """Get debug information about the core package."""
        return {
            "version": __version__,
            "components": COMPONENT_VERSIONS,
            "assistant_settings": {
                "memory_enabled": True,
                "router_enabled": True
            },
            "sql_settings": {
                "validator_enabled": True,
                "generator_enabled": True
            },
            "bigquery_settings": {
                "location": "US",
                "timeout": 300
            },
            "metadata_settings": {
                "schema_refresh_enabled": True,
                "cache_enabled": True
            }
        }
    
    __all__.append("get_debug_info")

# Optional: System checks
def _perform_system_checks():
    """Perform system checks during import."""
    import pkg_resources
    
    required_packages = [
        'google-cloud-bigquery',
        'pydantic',
        'structlog'
    ]
    
    for package in required_packages:
        try:
            pkg_resources.require(package)
        except pkg_resources.DistributionNotFound:
            print(f"Warning: Required package '{package}' not found")
        except Exception as e:
            print(f"Warning: Error checking package '{package}': {str(e)}")

if __debug__:
    _perform_system_checks()