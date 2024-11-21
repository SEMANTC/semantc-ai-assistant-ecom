# ecommerce-ai-assistant/app/config/settings.py
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Set
from enum import Enum
from pathlib import Path

class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with typing and validation.
    """
    
    # Basic Configuration
    PROJECT_NAME: str = "E-commerce AI Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WORKERS: int = 4
    RELOAD: bool = False
    
    # GCP Configuration
    PROJECT_ID: str
    REGION: str = "us-central1"
    DATASET_ID: str
    BIGQUERY_DATASET: str
    SERVICE_ACCOUNT_PATH: Optional[str] = None
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: Path = Path("knowledge_base")
    SCHEMA_REFRESH_INTERVAL: int = 3600  # seconds
    SCHEMA_CACHE_ENABLED: bool = True
    SCHEMA_CACHE_TTL: int = 3600  # seconds
    
    # Query Template Configuration
    TEMPLATE_PATH: Path = Path("knowledge_base/templates")
    DEFAULT_TEMPLATE_SET: str = "default"
    
    # Platform Configuration
    AVAILABLE_PLATFORMS: Set[str] = {"shopify", "amazon", "ebay"}
    PLATFORM_SCHEMAS: Dict[str, str] = {
        "shopify": "shopify_schema",
        "amazon": "amazon_schema",
        "ebay": "ebay_schema"
    }
    REQUIRED_SCHEMA_FILES: List[str] = [
        "orders.yaml",
        "products.yaml",
        "customers.yaml"
    ]
    
    # Schema Validation
    SCHEMA_VALIDATION_ENABLED: bool = True
    STRICT_SCHEMA_VALIDATION: bool = True
    ALLOW_UNKNOWN_FIELDS: bool = False
    
    # Query Processing
    ENABLE_QUERY_CACHE: bool = True
    QUERY_CACHE_TTL: int = 300  # seconds
    MAX_QUERY_TEMPLATES: int = 100
    ENABLE_SAVED_QUERIES: bool = True
    SAVED_QUERIES_PATH: Path = Path("knowledge_base/saved_queries")
    MAX_QUERY_LENGTH: int = 500
    QUERY_TIMEOUT: int = 30  # seconds
    MAX_ROWS_RETURN: int = 10000
    
    # LLM Configuration
    ANTHROPIC_API_KEY: str
    MODEL_NAME: str = "claude-3-sonnet-20240229"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # Security Configuration
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_KEY_HEADER: str = "X-API-Key"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # seconds
    MAX_CACHE_SIZE: int = 1000
    
    # Performance Configuration
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    BATCH_SIZE: int = 100
    
    # BigQuery Configuration
    BQ_LOCATION: str = "US"
    BQ_JOB_TIMEOUT: int = 300
    BQ_MAXIMUM_BYTES_BILLED: int = 1_000_000_000
    
    # Memory Configuration
    MAX_CONVERSATION_HISTORY: int = 10
    MEMORY_PERSIST_ENABLED: bool = True
    MEMORY_STORAGE_PATH: Optional[Path] = None
    
    # Error Handling
    MAX_ERROR_RETRIES: int = 3
    ERROR_RETRY_DELAY: int = 1  # seconds
    DETAILED_ERRORS: bool = False  # Only enable in non-production
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.ENVIRONMENT == EnvironmentType.PRODUCTION
    
    @property
    def bigquery_dataset_path(self) -> str:
        """Get fully qualified BigQuery dataset path."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}"
    
    @property
    def schema_paths(self) -> Dict[str, Path]:
        """Get schema paths for each platform."""
        return {
            platform: self.KNOWLEDGE_BASE_PATH / platform
            for platform in self.AVAILABLE_PLATFORMS
        }
    
    @property
    def consolidated_schema_path(self) -> Path:
        """Get path for consolidated schemas."""
        return self.KNOWLEDGE_BASE_PATH / "consolidated"
    
    @property
    def available_schemas(self) -> Dict[str, Dict]:
        """Load and return available database schemas."""
        return {
            platform: self.PLATFORM_SCHEMAS[platform]
            for platform in self.AVAILABLE_PLATFORMS
            if platform in self.PLATFORM_SCHEMAS
        }
    
    def get_platform_schema_path(self, platform: str) -> Path:
        """Get schema path for specific platform."""
        if platform not in self.AVAILABLE_PLATFORMS:
            raise ValueError(f"Invalid platform: {platform}")
        return self.schema_paths[platform]
    
    def validate_schema_structure(self) -> bool:
        """Validate knowledge base structure exists."""
        try:
            if not self.KNOWLEDGE_BASE_PATH.exists():
                return False
                
            for platform in self.AVAILABLE_PLATFORMS:
                platform_path = self.schema_paths[platform]
                if not platform_path.exists():
                    return False
                    
                for schema_file in self.REQUIRED_SCHEMA_FILES:
                    if not (platform_path / schema_file).exists():
                        return False
            
            if not self.consolidated_schema_path.exists():
                return False
                
            return True
            
        except Exception:
            return False
    
    def get_memory_path(self) -> Optional[Path]:
        """Get path for memory persistence."""
        if self.MEMORY_PERSIST_ENABLED and self.MEMORY_STORAGE_PATH:
            path = self.MEMORY_STORAGE_PATH
            path.mkdir(parents=True, exist_ok=True)
            return path
        return None
    
    def get_cache_config(self) -> Dict:
        """Get cache configuration."""
        return {
            "enabled": self.CACHE_ENABLED,
            "ttl": self.CACHE_TTL,
            "max_size": self.MAX_CACHE_SIZE,
            "schema_ttl": self.SCHEMA_CACHE_TTL
        }
    
    def get_error_config(self) -> Dict:
        """Get error handling configuration."""
        return {
            "max_retries": self.MAX_ERROR_RETRIES,
            "retry_delay": self.ERROR_RETRY_DELAY,
            "detailed_errors": self.DETAILED_ERRORS and not self.is_production
        }
    
    def get_query_config(self) -> Dict:
        """Get query processing configuration."""
        return {
            "timeout": self.QUERY_TIMEOUT,
            "max_length": self.MAX_QUERY_LENGTH,
            "max_rows": self.MAX_ROWS_RETURN,
            "cache_enabled": self.ENABLE_QUERY_CACHE,
            "cache_ttl": self.QUERY_CACHE_TTL,
            "saved_queries_enabled": self.ENABLE_SAVED_QUERIES
        }