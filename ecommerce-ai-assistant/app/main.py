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
from core.metadata import SchemaRegistry
from core.assistant import AssistantManager, create_assistant

# Setup logging
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    try:
        logger.info(
            "Starting application",
            environment=settings.ENVIRONMENT,
            project_id=settings.PROJECT_ID
        )
        
        # Initialize components
        try:
            # Validate knowledge base structure
            if not settings.validate_schema_structure():
                raise ValueError("Invalid knowledge base structure")
            
            # Initialize schema registry
            schema_registry = SchemaRegistry()
            await schema_registry.initialize()
            logger.info(
                "Schema registry initialized",
                schema_count=len(schema_registry.schemas),
                platforms=list(settings.AVAILABLE_PLATFORMS)
            )
            
            # Initialize BigQuery client
            bq_client = BigQueryClient()
            await bq_client.initialize()
            logger.info(
                "BigQuery client initialized",
                project=settings.PROJECT_ID,
                dataset=settings.BIGQUERY_DATASET
            )
            
            # Create and initialize assistant
            assistant = await create_assistant()
            logger.info("Assistant initialized successfully")
            
            # Store components in app state
            app.state.schema_registry = schema_registry
            app.state.bq_client = bq_client
            app.state.assistant = assistant
            
            # Validate all components
            dataset_ref = f"{settings.PROJECT_ID}.{settings.BIGQUERY_DATASET}"
            await bq_client.validate_dataset(dataset_ref)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(
                "Component initialization failed",
                error=str(e),
                exc_info=True
            )
            raise
        
        yield
        
    except Exception as e:
        logger.error(
            "Startup failed",
            error=str(e),
            exc_info=True
        )
        raise
    
    # Shutdown
    try:
        logger.info("Shutting down application")
        
        if hasattr(app.state, 'bq_client'):
            await app.state.bq_client.close()
            logger.info("BigQuery client closed")
            
        if hasattr(app.state, 'assistant'):
            await app.state.assistant.close()
            logger.info("Assistant closed")
            
        if hasattr(app.state, 'schema_registry'):
            # Save any cached schemas if needed
            if settings.SCHEMA_CACHE_ENABLED:
                try:
                    app.state.schema_registry.save_state()
                    logger.info("Schema registry state saved")
                except Exception as e:
                    logger.error(
                        "Failed to save schema registry state",
                        error=str(e)
                    )
                    
    except Exception as e:
        logger.error("Shutdown error", error=str(e))

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="E-commerce AI Assistant API for natural language querying of e-commerce data",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable):
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Request logging middleware
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

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for the application.
    Verifies database connectivity and core services.
    """
    try:
        health_status = {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
            "components": {}
        }
        
        # Check BigQuery connectivity
        try:
            bq_client: BigQueryClient = app.state.bq_client
            dataset_ref = f"{settings.PROJECT_ID}.{settings.BIGQUERY_DATASET}"
            await bq_client.validate_dataset(dataset_ref)
            health_status["components"]["bigquery"] = {
                "status": "healthy",
                "dataset": dataset_ref
            }
        except Exception as e:
            health_status["components"]["bigquery"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check schema registry
        try:
            schema_registry: SchemaRegistry = app.state.schema_registry
            schemas_valid = len(schema_registry.schemas) > 0
            health_status["components"]["schema_registry"] = {
                "status": "healthy" if schemas_valid else "warning",
                "schemas_loaded": len(schema_registry.schemas),
                "platforms": list(settings.AVAILABLE_PLATFORMS)
            }
        except Exception as e:
            health_status["components"]["schema_registry"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check assistant
        try:
            assistant: AssistantManager = app.state.assistant
            health_status["components"]["assistant"] = {
                "status": "healthy",
                "model": settings.MODEL_NAME
            }
        except Exception as e:
            health_status["components"]["assistant"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Determine overall health
        component_statuses = [
            comp["status"] for comp in health_status["components"].values()
        ]
        if any(status == "unhealthy" for status in component_statuses):
            health_status["status"] = "unhealthy"
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_status
            )
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# Include API routes
app.include_router(api_router, prefix="/api")

# Debug routes (non-production only)
if not settings.is_production:
    @app.get("/debug/config")
    async def debug_config():
        """Return non-sensitive configuration for debugging"""
        try:
            schema_registry: SchemaRegistry = app.state.schema_registry
            return {
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "available_platforms": list(settings.AVAILABLE_PLATFORMS),
                "project_id": settings.PROJECT_ID,
                "dataset": settings.BIGQUERY_DATASET,
                "schema_info": {
                    "loaded_schemas": list(schema_registry.schemas.keys()),
                    "relationship_count": len(schema_registry.relationships.edges()),
                    "query_templates": len(schema_registry.query_templates),
                    "business_terms": len(schema_registry.business_glossary)
                },
                "cache_config": settings.get_cache_config(),
                "query_config": settings.get_query_config()
            }
        except Exception as e:
            logger.error("Debug config error", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Failed to retrieve debug configuration",
                    "detail": str(e)
                }
            )
            
    @app.get("/debug/schema-info")
    async def debug_schema_info():
        """Return schema information for debugging"""
        try:
            schema_registry: SchemaRegistry = app.state.schema_registry
            return {
                "tables": list(schema_registry.schemas.keys()),
                "relationships": [
                    {
                        "from": edge[0],
                        "to": edge[1],
                        "type": schema_registry.relationships.edges[edge]["relationship_type"]
                    }
                    for edge in schema_registry.relationships.edges()
                ],
                "business_terms": list(schema_registry.business_glossary.keys()),
                "query_templates": list(schema_registry.query_templates.keys())
            }
        except Exception as e:
            logger.error("Schema info error", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Failed to retrieve schema information",
                    "detail": str(e)
                }
            )