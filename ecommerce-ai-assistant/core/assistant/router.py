# ecommerce-ai-assistant/core/assistant/router.py
from typing import Dict, Optional, Set, Tuple
import re
from datetime import datetime

from utils.logger import get_logger
from core.metadata import SchemaRegistry

class QueryRouter:
    """
    Routes and classifies queries based on their intent and required data sources.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.schema_registry = None
        
        # Common query patterns
        self.query_patterns = {
            "sales": [
                r"sales",
                r"revenue",
                r"earnings",
                r"income",
                r"transactions",
                r"orders",
                r"purchases"
            ],
            "inventory": [
                r"inventory",
                r"stock",
                r"products",
                r"items",
                r"availability"
            ],
            "customers": [
                r"customers?",
                r"buyers",
                r"clients",
                r"customer base",
                r"shoppers"
            ],
            "performance": [
                r"performance",
                r"metrics",
                r"analytics",
                r"trends",
                r"growth"
            ]
        }
        
        # Temporal patterns
        self.time_patterns = [
            r"last (day|week|month|year)",
            r"this (week|month|year)",
            r"past \d+ (days|weeks|months|years)",
            r"between.*and",
            r"since",
            r"current",
            r"ytd",
            r"daily|weekly|monthly|yearly"
        ]
    
    async def initialize(self, schema_registry: SchemaRegistry) -> None:
        """Initialize with schema registry."""
        self.schema_registry = schema_registry
        self.logger.info("Query router initialized")
    
    async def classify_query(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Tuple[Optional[str], Dict]:
        """
        Classify the query type and extract relevant context.
        
        Args:
            query: User's query text
            context: Optional additional context
            
        Returns:
            Tuple of (query_type, extracted_context)
        """
        try:
            query_lower = query.lower()
            extracted_context = {}
            
            # Check for temporal context
            time_context = self._extract_time_context(query_lower)
            if time_context:
                extracted_context.update(time_context)
            
            # Try to match query patterns
            for query_type, patterns in self.query_patterns.items():
                if any(re.search(pattern, query_lower) for pattern in patterns):
                    self.logger.info(
                        "Classified query",
                        query_type=query_type,
                        context=extracted_context
                    )
                    return query_type, extracted_context
            
            # If no direct match, try schema-based classification
            if self.schema_registry:
                schema_type = await self._classify_from_schema(query_lower)
                if schema_type:
                    return schema_type, extracted_context
            
            self.logger.info("Could not classify query", query=query)
            return None, extracted_context
            
        except Exception as e:
            self.logger.error(
                "Error classifying query",
                error=str(e),
                query=query,
                exc_info=True
            )
            return None, {}
    
    async def validate_platforms(
        self,
        requested_platforms: Set[str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Validate requested platforms against available schemas.
        
        Returns:
            Tuple of (valid_platforms, invalid_platforms)
        """
        if not self.schema_registry:
            raise ValueError("Schema registry not initialized")
            
        available_platforms = self.schema_registry.get_all_platforms()
        
        valid = requested_platforms.intersection(available_platforms)
        invalid = requested_platforms - available_platforms
        
        if invalid:
            self.logger.warning(
                "Invalid platforms requested",
                invalid_platforms=list(invalid)
            )
        
        return valid, invalid
    
    async def get_required_tables(
        self,
        query_type: str,
        platforms: Set[str]
    ) -> Set[str]:
        """Get required tables for query type and platforms."""
        if not self.schema_registry:
            raise ValueError("Schema registry not initialized")
            
        tables = set()
        
        # Get tables for query type
        type_tables = self.schema_registry.get_tables_for_query_type(query_type)
        tables.update(type_tables)
        
        # Get platform-specific tables
        for platform in platforms:
            platform_tables = self.schema_registry.get_platform_tables(platform)
            tables.update(platform_tables)
        
        return tables
    
    def _extract_time_context(self, query: str) -> Dict:
        """Extract temporal context from query."""
        context = {}
        
        # Try to match time patterns
        for pattern in self.time_patterns:
            match = re.search(pattern, query)
            if match:
                time_expr = match.group(0)
                context["time_range"] = time_expr
                break
        
        # Extract specific date references
        date_matches = re.findall(
            r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}',
            query
        )
        if date_matches:
            context["specific_dates"] = date_matches
        
        return context
    
    async def _classify_from_schema(self, query: str) -> Optional[str]:
        """Attempt to classify query using schema metadata."""
        if not self.schema_registry:
            return None
            
        # Check business terms
        for term in query.split():
            business_term = self.schema_registry.get_business_term(term)
            if business_term:
                table_info = self.schema_registry.get_table_schema(
                    business_term.get("table")
                )
                if table_info:
                    return table_info.get("query_type")
        
        return None
    
    async def get_query_context(
        self,
        query_type: str,
        platforms: Set[str]
    ) -> Dict:
        """Get additional context for query execution."""
        context = {
            "query_type": query_type,
            "platforms": list(platforms),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.schema_registry:
            # Add table information
            tables = await self.get_required_tables(query_type, platforms)
            context["tables"] = list(tables)
            
            # Add metric information
            metrics = self.schema_registry.get_metric_definition(query_type)
            if metrics:
                context["metrics"] = metrics
        
        return context
    
    def supports_query_type(self, query_type: str) -> bool:
        """Check if query type is supported."""
        return query_type in self.query_patterns
    
    async def get_platform_capabilities(self, platform: str) -> Dict:
        """Get capabilities for a specific platform."""
        if not self.schema_registry:
            return {}
            
        capabilities = {
            "tables": list(self.schema_registry.get_platform_tables(platform)),
            "query_types": []
        }
        
        # Get supported query types
        for query_type in self.query_patterns.keys():
            tables = await self.get_required_tables(
                query_type,
                {platform}
            )
            if tables:
                capabilities["query_types"].append(query_type)
        
        return capabilities
    
    async def validate_query_support(
        self,
        query_type: str,
        platforms: Set[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if query type is supported for given platforms.
        
        Returns:
            Tuple of (is_supported, error_message)
        """
        try:
            # Check query type support
            if not self.supports_query_type(query_type):
                return False, f"Query type '{query_type}' not supported"
            
            # Validate platforms
            valid, invalid = await self.validate_platforms(platforms)
            if invalid:
                return False, f"Invalid platforms: {', '.join(invalid)}"
            
            # Check if required tables exist
            required_tables = await self.get_required_tables(
                query_type,
                valid
            )
            
            if not required_tables:
                return False, f"No tables available for {query_type} queries"
            
            return True, None
            
        except Exception as e:
            self.logger.error(
                "Error validating query support",
                error=str(e),
                query_type=query_type,
                platforms=list(platforms),
                exc_info=True
            )
            return False, str(e)