# ecommerce-ai-assistant/app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Callable
from contextlib import asynccontextmanager
import structlog
from google.cloud import bigquery

from app.config import settings
from api import api_router
from utils.logger import setup_logging, get_logger
from core.bigquery.client import BigQueryClient

# setup logging
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    LIFECYCLE MANAGER FOR THE FASTAPI APPLICATION
    HANDLES STARTUP AND SHUTDOWN EVENTS
    """
    # startup
    try:
        logger.info(
            "Starting application",
            environment=settings.ENVIRONMENT,
            project_id=settings.PROJECT_ID
        )
        
        # initialize bigquery client
        bq_client = BigQueryClient()
        await bq_client.initialize()
        
        # validate dataset access
        dataset_ref = f"{settings.PROJECT_ID}.{settings.BIGQUERY_DATASET}"
        logger.info("validating BigQuery dataset access", dataset=dataset_ref)
        
        # store clients in app state
        app.state.bq_client = bq_client
        
        yield
    except Exception as e:
        logger.error("startup failed", error=str(e), exc_info=True)
        raise
    
    # shutdown
    try:
        logger.info("shutting down application")
        if hasattr(app.state, 'bq_client'):
            await app.state.bq_client.close()
    except Exception as e:
        logger.error("shutdown error", error=str(e))

# initialize fastapi application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="E-commerce AI Assistant API for natural language querying of e-commerce data",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# add cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# request id middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable):
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=f"{duration:.3f}s"
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            error=str(e),
            duration=f"{duration:.3f}s",
            exc_info=True
        )
        raise

# error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal server error",
            "detail": str(exc) if settings.DEBUG else "an unexpected error occurred"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    HEALTH CHECK ENDPOINT FOR THE APPLICATION
    VERIFIES DATABASE CONNECTIVITY AND CORE SERVICES
    """
    try:
        # Check BigQuery connectivity
        bq_client: BigQueryClient = app.state.bq_client
        dataset_ref = f"{settings.PROJECT_ID}.{settings.BIGQUERY_DATASET}"
        await bq_client.validate_dataset(dataset_ref)
        
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "bigquery_status": "connected"
        }
    except Exception as e:
        logger.error("health check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# include api routes
app.include_router(api_router, prefix="/api")

# debug routes (non-production only)
if not settings.is_production:
    @app.get("/debug/config")
    async def debug_config():
        """RETURN NON-SENSITIVE CONFIGURATION FOR DEBUGGING"""
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "available_platforms": list(settings.AVAILABLE_PLATFORMS),
            "project_id": settings.PROJECT_ID,
            "dataset": settings.BIGQUERY_DATASET
        }