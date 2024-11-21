# ecommerce-ai-assistant/api/routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Optional
import time
import uuid
from datetime import datetime

from .models import (
    QueryRequest, QueryResponse, ErrorResponse, ErrorDetail,
    Platform, QueryType, QueryMetrics, SchemaContext
)
from core.assistant import AssistantManager
from core.metadata import SchemaRegistry
from core.bigquery import BigQueryClient
from utils.logger import get_logger, LogContext
from app.config import settings

# Initialize router and logger
router = APIRouter()
logger = get_logger(__name__)

@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def process_query(
    request: QueryRequest,
    req: Request,
    assistant: AssistantManager = Depends(AssistantManager),
    schema_registry: SchemaRegistry = Depends(SchemaRegistry),
    bq_client: BigQueryClient = Depends(BigQueryClient),
) -> QueryResponse:
    """
    Process a natural language query using schema knowledge and return results.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    with LogContext(
        request_id=request_id,
        platforms=list(request.platforms),
        query_type=request.query_type
    ):
        try:
            logger.info(
                "Processing query request",
                query=request.query,
                query_type=request.query_type
            )
            
            # Validate platforms against schema
            valid_platforms, invalid = await schema_registry.validate_platforms(
                request.platforms
            )
            if invalid:
                raise ValueError(f"Invalid platforms: {', '.join(invalid)}")
            
            # Get schema context
            schema_context = await schema_registry.get_query_context(
                request.query,
                request.query_type,
                valid_platforms
            )
            
            # Process query
            response = await assistant.process_message(
                message=request.query,
                conversation_id=request_id,
                active_platforms=valid_platforms,
                context={
                    "schema_context": schema_context,
                    "query_context": request.context,
                    "request_id": request_id
                }
            )
            
            # Execute query if generated
            if response.get("sql_query"):
                results = await bq_client.execute_query(
                    query=response["sql_query"].sql,
                    params=response["sql_query"].params
                )
                
                # Get query metrics
                metrics = QueryMetrics(
                    execution_time=time.time() - start_time,
                    rows_processed=len(results),
                    bytes_processed=response.get("bytes_processed", 0),
                    cache_hit=response.get("cache_hit", False)
                )
                
                return QueryResponse(
                    message=response["message"],
                    sql_query=response["sql_query"],
                    data=results,
                    metrics=metrics,
                    schema_context=schema_context,
                    conversation_id=request_id
                )
            
            # Handle non-query responses
            return QueryResponse(
                message=response["message"],
                conversation_id=request_id,
                schema_context=schema_context
            )
            
        except ValueError as e:
            logger.warning(
                "Invalid query request",
                error=str(e),
                query=request.query
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorDetail(
                    code="INVALID_REQUEST",
                    message=str(e),
                    query_context={
                        "query": request.query,
                        "platforms": list(request.platforms)
                    }
                ).dict()
            )
            
        except Exception as e:
            logger.error(
                "Error processing query",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=ErrorDetail(
                    code="PROCESSING_ERROR",
                    message="Failed to process query",
                    details={"error": str(e)},
                    query_context={
                        "request_id": request_id,
                        "query": request.query
                    }
                ).dict()
            )

@router.get("/health")
async def health_check() -> Dict:
    """
    Check the health of the API and its dependencies.
    """
    try:
        schema_registry: SchemaRegistry = router.dependency_overrides.get(
            SchemaRegistry, SchemaRegistry
        )()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "components": {
                "schema_registry": {
                    "status": "healthy",
                    "schemas_loaded": len(schema_registry.schemas)
                }
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorDetail(
                code="HEALTH_CHECK_FAILED",
                message="Service health check failed",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/metadata/platforms")
async def list_platforms(
    schema_registry: SchemaRegistry = Depends(SchemaRegistry)
) -> Dict:
    """
    List all supported e-commerce platforms and their capabilities.
    """
    try:
        platforms = {}
        for platform in Platform:
            capabilities = await schema_registry.get_platform_capabilities(
                platform.value
            )
            platforms[platform.value] = capabilities
        
        return {
            "platforms": platforms,
            "query_types": [qt.value for qt in QueryType]
        }
    except Exception as e:
        logger.error("Failed to list platforms", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorDetail(
                code="PLATFORM_LIST_FAILED",
                message="Failed to retrieve platform information",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/metadata/schema/{platform}")
async def get_platform_schema(
    platform: Platform,
    schema_registry: SchemaRegistry = Depends(SchemaRegistry)
) -> Dict:
    """
    Get schema information for a specific platform.
    """
    try:
        schema = await schema_registry.get_platform_schema(platform.value)
        return schema
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=ErrorDetail(
                code="PLATFORM_NOT_FOUND",
                message=f"Schema not found for platform: {platform}"
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorDetail(
                code="SCHEMA_RETRIEVAL_FAILED",
                message="Failed to retrieve schema information",
                details={"error": str(e)}
            ).dict()
        )