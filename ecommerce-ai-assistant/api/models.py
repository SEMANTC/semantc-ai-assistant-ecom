# ecommerce-ai-assistant/api/models.py
from enum import Enum
from pydantic import BaseModel, Field, validator, conlist
from typing import Dict, List, Optional, Set, Union
from datetime import datetime

class QueryType(str, Enum):
    """Types of queries that can be processed"""
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    PERFORMANCE = "performance"
    GENERAL = "general"

class Platform(str, Enum):
    """Supported e-commerce platforms"""
    SHOPIFY = "shopify"
    AMAZON = "amazon"
    EBAY = "ebay"

class TimeRange(BaseModel):
    """Time range specification"""
    start_date: Optional[datetime] = Field(None, description="Start date for the query")
    end_date: Optional[datetime] = Field(None, description="End date for the query")
    period: Optional[str] = Field(None, description="Predefined time period (e.g., 'last_month')")

class MetricDefinition(BaseModel):
    """Metric definition for queries"""
    name: str = Field(..., description="Name of the metric")
    aggregation: str = Field(..., description="Aggregation type (sum, avg, etc.)")
    field: str = Field(..., description="Field to aggregate")
    filter: Optional[str] = Field(None, description="Optional filter condition")

class SchemaContext(BaseModel):
    """Schema context for query generation"""
    tables: List[str] = Field(default_factory=list, description="Required tables")
    relationships: List[Dict] = Field(default_factory=list, description="Table relationships")
    metrics: List[MetricDefinition] = Field(default_factory=list, description="Required metrics")

class QueryContext(BaseModel):
    """Extended query context"""
    time_range: Optional[TimeRange] = Field(None, description="Time range for the query")
    metrics: Optional[List[str]] = Field(None, description="Required metrics")
    dimensions: Optional[List[str]] = Field(None, description="Required dimensions")
    filters: Optional[Dict] = Field(None, description="Additional filters")
    schema: Optional[SchemaContext] = Field(None, description="Schema context")

class QueryRequest(BaseModel):
    """Request format for query processing"""
    query: str = Field(..., description="Natural language query to process")
    platforms: Set[Platform] = Field(..., description="Platforms to query against")
    query_type: Optional[QueryType] = Field(None, description="Type of query being made")
    context: Optional[QueryContext] = Field(None, description="Query context")
    
    @validator('query')
    def validate_query_length(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query must be at least 3 characters long")
        if len(v) > 500:
            raise ValueError("Query must not exceed 500 characters")
        return v

    @validator('platforms')
    def validate_platforms(cls, v):
        if not v:
            raise ValueError("At least one platform must be specified")
        return v

    class Config:
        schema_extra = {
            "example": {
                "query": "What were my total sales last month?",
                "platforms": ["shopify", "amazon"],
                "query_type": "sales",
                "context": {
                    "time_range": {
                        "period": "last_month"
                    },
                    "metrics": ["total_sales", "order_count"]
                }
            }
        }

class SQLQuery(BaseModel):
    """Generated SQL query details"""
    sql: str = Field(..., description="Generated SQL query")
    params: Optional[Dict] = Field(default=None, description="Query parameters")
    tables: List[str] = Field(default_factory=list, description="Tables referenced in query")
    platforms: Set[Platform] = Field(..., description="Platforms involved in query")
    metadata: Optional[Dict] = Field(None, description="Additional query metadata")
    estimated_cost: Optional[float] = Field(None, description="Estimated query cost")

class QueryMetrics(BaseModel):
    """Query execution metrics"""
    execution_time: float = Field(..., description="Query execution time in seconds")
    rows_processed: int = Field(..., description="Number of rows processed")
    bytes_processed: int = Field(..., description="Number of bytes processed")
    cache_hit: bool = Field(..., description="Whether query hit cache")

class QueryResponse(BaseModel):
    """Response format for query processing"""
    message: str = Field(..., description="Natural language response")
    sql_query: Optional[SQLQuery] = Field(None, description="Generated SQL query details")
    data: Optional[Dict] = Field(None, description="Query results")
    metrics: Optional[QueryMetrics] = Field(None, description="Query execution metrics")
    schema_context: Optional[SchemaContext] = Field(None, description="Schema context used")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    error: Optional[str] = Field(None, description="Error message if query failed")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Your total sales last month were $50,000",
                "sql_query": {
                    "sql": "SELECT SUM(total_amount) as total_sales...",
                    "platforms": ["shopify", "amazon"],
                    "tables": ["orders"]
                },
                "metrics": {
                    "execution_time": 0.45,
                    "rows_processed": 1000,
                    "bytes_processed": 50000,
                    "cache_hit": False
                }
            }
        }

class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(None, description="Additional error details")
    query_context: Optional[Dict] = Field(None, description="Context when error occurred")

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail
    request_id: str = Field(..., description="Request identifier for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")