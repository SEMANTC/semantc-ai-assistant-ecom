# ecommerce-ai-assistant/app/config/settings.py
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional, Set
from enum import Enum

class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    """
    APPLICATION SETTINGS LOADED FROM ENVIRONMENT VARIABLES WITH TYPING AND VALIDATION
    """
    
    # basic configuration
    PROJECT_NAME: str = "e-commerce AI Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False
    
    # server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WORKERS: int = 4
    RELOAD: bool = False  # auto-reload in development
    
    # gcp configuration
    PROJECT_ID: str
    REGION: str = "us-central1"
    DATASET_ID: str
    BIGQUERY_DATASET: str
    SERVICE_ACCOUNT_PATH: Optional[str] = None
    
    # llm configuration
    ANTHROPIC_API_KEY: str
    MODEL_NAME: str = "claude-3-sonnet-20240229"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # platform configuration
    AVAILABLE_PLATFORMS: Set[str] = {"shopify", "amazon", "ebay"}
    PLATFORM_SCHEMAS: Dict[str, str] = {
        "shopify": "shopify_schema",
        "amazon": "amazon_schema",
        "ebay": "ebay_schema"
    }
    
    # security configuration
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_KEY_HEADER: str = "X-API-Key"
    
    # logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # cache configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # seconds
    MAX_CACHE_SIZE: int = 1000
    
    # query configuration
    MAX_QUERY_LENGTH: int = 500
    QUERY_TIMEOUT: int = 30  # seconds
    MAX_ROWS_RETURN: int = 10000
    
    # performance configuration
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    BATCH_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def is_production(self) -> bool:
        """CHECK IF ENVIRONMENT IS PRODUCTION"""
        return self.ENVIRONMENT == EnvironmentType.PRODUCTION
    
    @property
    def bigquery_dataset_path(self) -> str:
        """GET FULLY QUALIFIED BIGQUERY DATASET PATH"""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}"
    
    @property
    def available_schemas(self) -> Dict[str, Dict]:
        """LOAD AND RETURN AVAILABLE DATABASE SCHEMAS"""
        # this could be extended to dynamically load schemas
        return {
            platform: self.PLATFORM_SCHEMAS[platform]
            for platform in self.AVAILABLE_PLATFORMS
            if platform in self.PLATFORM_SCHEMAS
        }