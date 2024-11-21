# ecommerce-ai-assistant/core/metadata/schema_registry.py
from typing import Dict, List, Optional, Set, Union
import yaml
from pathlib import Path
import networkx as nx
from datetime import datetime
import json
from functools import lru_cache
import re

from utils.logger import get_logger
from app.config import settings

class SchemaRegistry:
    """
    Manages database schema metadata, relationships, and business rules.
    Provides a central registry for all data model information.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.schemas: Dict = {}
        self.relationships = nx.DiGraph()
        self.business_glossary: Dict = {}
        self.query_templates: Dict = {}
        self.metric_definitions: Dict = {}
        self.time_patterns: Dict = {}
        self._last_reload: Optional[datetime] = None
        
    async def initialize(self) -> None:
        """
        Initialize the schema registry by loading all metadata.
        """
        try:
            self.logger.info("Initializing schema registry")
            
            # Load all schema files
            await self._load_schemas()
            
            # Build relationship graph
            self._build_relationship_graph()
            
            # Build business glossary
            self._build_business_glossary()
            
            # Load query templates
            self._load_query_templates()
            
            # Load metric definitions
            self._load_metric_definitions()
            
            # Load time patterns
            self._load_time_patterns()
            
            self._last_reload = datetime.utcnow()
            
            self.logger.info(
                "Schema registry initialized",
                schemas=len(self.schemas),
                relationships=self.relationships.number_of_edges(),
                templates=len(self.query_templates),
                metrics=len(self.metric_definitions)
            )
            
        except Exception as e:
            self.logger.error("Failed to initialize schema registry", error=str(e))
            raise
    
    async def _load_schemas(self) -> None:
        """Load all schema files from the knowledge base directory."""
        schema_dir = Path("knowledge_base/schemas")
        
        # Load platform-specific schemas
        for platform in settings.AVAILABLE_PLATFORMS:
            platform_dir = schema_dir / platform
            if platform_dir.exists():
                for schema_file in platform_dir.glob("*.yaml"):
                    await self._load_schema_file(schema_file, platform)
        
        # Load consolidated schemas
        consolidated_dir = schema_dir / "consolidated"
        if consolidated_dir.exists():
            for schema_file in consolidated_dir.glob("*.yaml"):
                await self._load_schema_file(schema_file, "consolidated")
    
    async def _load_schema_file(self, file_path: Path, platform: str) -> None:
        """Load and validate a single schema file."""
        try:
            with open(file_path) as f:
                schema = yaml.safe_load(f)
            
            # Validate schema structure
            if not self._validate_schema_structure(schema):
                self.logger.error(f"Invalid schema structure in {file_path}")
                return
            
            # Add platform information
            schema["platform"] = platform
            
            # Add to schemas dictionary
            self.schemas[schema["table_name"]] = schema
            
            self.logger.info(
                f"Loaded schema",
                table=schema["table_name"],
                platform=platform
            )
            
        except Exception as e:
            self.logger.error(f"Error loading schema file {file_path}", error=str(e))
    
    def _validate_schema_structure(self, schema: Dict) -> bool:
        """Validate the structure of a schema definition."""
        required_fields = {"table_name", "columns"}
        if not all(field in schema for field in required_fields):
            return False
            
        # Validate columns
        for column in schema.get("columns", []):
            if not {"name", "type"}.issubset(set(column.keys())):
                return False
        
        return True
    
    def _build_relationship_graph(self) -> None:
        """Build directed graph of table relationships."""
        self.relationships = nx.DiGraph()
        
        # Add nodes for all tables
        for table_name in self.schemas:
            self.relationships.add_node(table_name)
        
        # Add edges for relationships
        for table_name, schema in self.schemas.items():
            for relationship in schema.get("relationships", []):
                if "table" in relationship and "type" in relationship:
                    self.relationships.add_edge(
                        table_name,
                        relationship["table"],
                        relationship_type=relationship["type"],
                        keys=relationship.get("keys", {}),
                        description=relationship.get("description", "")
                    )
    
    def _build_business_glossary(self) -> None:
        """Build mapping of technical terms to business terms."""
        self.business_glossary = {}
        
        for schema in self.schemas.values():
            # Add column business terms
            for column in schema.get("columns", []):
                if "business_term" in column:
                    self.business_glossary[column["name"]] = {
                        "business_term": column["business_term"],
                        "description": column.get("description", ""),
                        "table": schema["table_name"]
                    }
            
            # Add metric business terms
            for metric in schema.get("common_metrics", []):
                if "name" in metric:
                    self.business_glossary[metric["name"]] = {
                        "business_term": metric.get("description", metric["name"]),
                        "type": "metric",
                        "table": schema["table_name"]
                    }
    
    def _load_query_templates(self) -> None:
        """Load query templates from schemas."""
        self.query_templates = {}
        
        for schema in self.schemas.values():
            for template in schema.get("query_templates", []):
                if "name" in template and "template" in template:
                    self.query_templates[template["name"]] = {
                        "template": template["template"],
                        "description": template.get("description", ""),
                        "table": schema["table_name"],
                        "type": template.get("type", "general")
                    }
    
    def _load_metric_definitions(self) -> None:
        """Load metric definitions from schemas."""
        self.metric_definitions = {}
        
        for schema in self.schemas.values():
            for metric in schema.get("common_metrics", []):
                if "name" in metric and "sql_template" in metric:
                    self.metric_definitions[metric["name"]] = {
                        "sql_template": metric["sql_template"],
                        "description": metric.get("description", ""),
                        "table": schema["table_name"]
                    }
    
    def _load_time_patterns(self) -> None:
        """Load time-related patterns and their handling."""
        self.time_patterns = {
            "last_month": lambda now: (
                now.replace(day=1).replace(month=now.month-1 if now.month > 1 else 12),
                now.replace(day=1) - timedelta(days=1)
            ),
            "this_month": lambda now: (
                now.replace(day=1),
                now
            ),
            "last_year": lambda now: (
                now.replace(year=now.year-1, month=1, day=1),
                now.replace(year=now.year-1, month=12, day=31)
            ),
            # Add more time patterns as needed
        }
    
    # Public access methods
    
    @lru_cache(maxsize=100)
    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """Get schema for a specific table."""
        return self.schemas.get(table_name)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the registry."""
        return table_name in self.schemas
    
    def get_relationships(self) -> nx.DiGraph:
        """Get the relationship graph."""
        return self.relationships
    
    def has_relationship(self, source_table: str, target_table: str) -> bool:
        """Check if two tables have a relationship."""
        return self.relationships.has_edge(source_table, target_table)
    
    def get_relationship_path(self, source_table: str, target_table: str) -> Optional[List[str]]:
        """Get the shortest path between two tables."""
        try:
            return nx.shortest_path(self.relationships, source_table, target_table)
        except nx.NetworkXNoPath:
            return None
    
    def get_business_term(self, technical_term: str) -> Optional[Dict]:
        """Get business term information for a technical term."""
        return self.business_glossary.get(technical_term)
    
    def get_query_template(self, template_name: str) -> Optional[Dict]:
        """Get a query template by name."""
        return self.query_templates.get(template_name)
    
    def get_metric_definition(self, metric_name: str) -> Optional[Dict]:
        """Get a metric definition by name."""
        return self.metric_definitions.get(metric_name)
    
    def get_time_pattern(self, pattern_name: str) -> Optional[callable]:
        """Get a time pattern handler by name."""
        return self.time_patterns.get(pattern_name)
    
    def get_tables_for_query_type(self, query_type: str) -> Set[str]:
        """Get tables relevant for a specific query type."""
        relevant_tables = set()
        
        for table_name, schema in self.schemas.items():
            if query_type in schema.get("query_types", []):
                relevant_tables.add(table_name)
        
        return relevant_tables
    
    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """Get the data type of a column."""
        schema = self.get_table_schema(table_name)
        if not schema:
            return None
            
        for column in schema.get("columns", []):
            if column["name"] == column_name:
                return column["type"]
        
        return None
    
    def get_platform_tables(self, platform: str) -> Set[str]:
        """Get all tables for a specific platform."""
        return {
            table_name for table_name, schema in self.schemas.items()
            if schema.get("platform") == platform
        }
    
    def get_all_platforms(self) -> Set[str]:
        """Get all platforms in the registry."""
        return {
            schema.get("platform") for schema in self.schemas.values()
            if schema.get("platform")
        }
    
    async def reload(self) -> None:
        """Reload all metadata."""
        await self.initialize()
    
    def needs_reload(self) -> bool:
        """Check if registry needs reloading based on time threshold."""
        if not self._last_reload:
            return True
            
        threshold = settings.SCHEMA_REFRESH_INTERVAL
        return (datetime.utcnow() - self._last_reload).total_seconds() > threshold