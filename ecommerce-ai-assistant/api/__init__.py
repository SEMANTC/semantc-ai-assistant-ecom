# ecommerce-ai-assistant/api/__init__.py
"""
api package for e-commerce ai assistant

this package handles the rest api interface for the ai assistant,
providing endpoints for natural language query processing
and conversion to sql for e-commerce data analysis
"""

from fastapi import APIRouter
from .routes import router as query_router

# create main api router
api_router = APIRouter()

# include all routes
api_router.include_router(
    query_router,
    prefix="/v1",
    tags=["query"]
)

# export the router
__all__ = ["api_router"]