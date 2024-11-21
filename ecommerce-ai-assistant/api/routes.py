# ecommerce-ai-assistant/api/routes.py
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, Dict
import time
import uuid
from datetime import datetime

from .models import (
    QueryRequest, QueryResponse, ErrorResponse, ErrorDetail,
    Platform, QueryType
)
from core.assistant.base import AssistantManager
from core.sql.generator import SQLGenerator
from core.bigquery.client import BigQueryClient
from utils.logger import get_logger, LogContext

# initialize router and logger
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
    bq_client: BigQueryClient = Depends(BigQueryClient),
) -> QueryResponse:
    """
    PROCESS A NATURAL LANGUAGE QUERY AND RETURN RESULTS FROM BIGQUERY
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    with LogContext(request_id=request_id, platforms=list(request.platforms)):
        try:
            logger.info(
                "processing query request",
                query=request.query,
                query_type=request.query_type
            )
            
            # generate sql query
            sql_query = await assistant.generate_sql(
                query=request.query,
                platforms=request.platforms,
                query_type=request.query_type,
                context=request.context
            )
            
            # execute query
            results = await bq_client.execute_query(
                query=sql_query.sql,
                params=sql_query.params
            )
            
            # generate natural language response
            response_message = await assistant.generate_response(
                query=request.query,
                results=results,
                sql_query=sql_query
            )
            
            processing_time = time.time() - start_time
            
            return QueryResponse(
                message=response_message,
                sql_query=sql_query,
                data=results,
                processing_time=processing_time
            )
            
        except ValueError as e:
            logger.warning(
                "invalid query request",
                error=str(e),
                query=request.query
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorDetail(
                    code="INVALID_REQUEST",
                    message=str(e)
                ).dict()
            )
            
        except Exception as e:
            logger.error(
                "error processing query",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=ErrorDetail(
                    code="PROCESSING_ERROR",
                    message="Failed to process query",
                    details={"error": str(e)}
                ).dict()
            )

@router.get("/health")
async def health_check() -> Dict:
    """
    CHECK THE HEALTH OF THE API AND ITS DEPENDENCIES
    """
    try:
        # Basic health check
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error("health check failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=ErrorDetail(
                code="HEALTH_CHECK_FAILED",
                message="service health check failed"
            ).dict()
        )

@router.get("/platforms")
async def list_platforms() -> Dict:
    """
    LIST ALL SUPPORTED E-COMMERCE PLATFORMS
    """
    return {
        "platforms": [platform.value for platform in Platform],
        "query_types": [query_type.value for query_type in QueryType]
    }