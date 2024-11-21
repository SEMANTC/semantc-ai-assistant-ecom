# ecommerce-ai-assistant/api/models.py
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Set
from datetime import datetime

class QueryType(str, Enum):
    """TYPES OF QUERIES THAT CAN BE PROCESSED"""
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    GENERAL = "general"

class Platform(str, Enum):
    """SUPPORTED E-COMMERCE PLATFORMS"""
    SHOPIFY = "shopify"
    AMAZON = "amazon"
    EBAY = "ebay"

class ChatMessage(BaseModel):
    """INDIVIDUAL CHAT MESSAGE FORMAT"""
    content: str = Field(..., description="the content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = Field(default=None, description="additional message metadata")

class QueryRequest(BaseModel):
    """REQUEST FORMAT FOR QUERY PROCESSING"""
    query: str = Field(..., description="the natural language query to process")
    platforms: Set[Platform] = Field(..., description="platforms to query against")
    query_type: Optional[QueryType] = Field(None, description="type of query being made")
    context: Optional[Dict] = Field(None, description="additional context for query processing")
    
    @validator('query')
    def validate_query_length(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("query must be at least 3 characters long")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "query": "What were my total sales last month?",
                "platforms": ["shopify", "amazon"],
                "query_type": "sales",
                "context": {"timezone": "UTC"}
            }
        }

class SQLQuery(BaseModel):
    """GENERATED SQL QUERY DETAILS"""
    sql: str = Field(..., description="the generated SQL query")
    params: Optional[Dict] = Field(default=None, description="query parameters")
    tables: List[str] = Field(default_factory=list, description="tables referenced in query")
    platforms: Set[Platform] = Field(..., description="platforms involved in query")

class QueryResponse(BaseModel):
    """RESPONSE FORMAT FOR QUERY PROCESSING"""
    message: str = Field(..., description="natural language response to the query")
    sql_query: Optional[SQLQuery] = Field(None, description="generated SQL query details")
    data: Optional[Dict] = Field(None, description="query results")
    error: Optional[str] = Field(None, description="error message if query failed")
    processing_time: float = Field(..., description="query processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "your total sales last month were $50,000",
                "sql_query": {
                    "sql": "SELECT SUM(total_amount) ...",
                    "platforms": ["shopify", "amazon"],
                    "tables": ["orders"]
                },
                "processing_time": 0.45
            }
        }

class ErrorDetail(BaseModel):
    """DETAILED ERROR INFORMATION"""
    code: str = Field(..., description="error code")
    message: str = Field(..., description="error message")
    details: Optional[Dict] = Field(None, description="additional error details")

class ErrorResponse(BaseModel):
    """STANDARD ERROR RESPONSE"""
    error: ErrorDetail
    request_id: str = Field(..., description="request identifier for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)