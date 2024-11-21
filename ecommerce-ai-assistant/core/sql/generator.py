# ecommerce-ai-assistant/core/sql/generator.py
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import re
from utils.logger import get_logger
from core.metadata import SchemaRegistry
from app.config import settings

class SQLGenerator:
    """
    Generates SQL queries using schema metadata and natural language understanding.
    """
    def __init__(self, schema_registry: SchemaRegistry):
        self.schema_registry = schema_registry
        self.logger = get_logger(__name__)
        self.project_id = settings.PROJECT_ID
        self.dataset = settings.BIGQUERY_DATASET
        
    async def generate_query(
        self,
        text: str,
        platforms: Set[str],
        query_type: Optional[str] = None
    ) -> Tuple[str, Dict[str, any], List[str]]:
        """
        Generate SQL query from natural language text.
        
        Args:
            text: Natural language query
            platforms: Set of active platforms
            query_type: Optional query type hint
            
        Returns:
            Tuple of (SQL query, parameters, list of tables used)
        """
        try:
            # Log query generation attempt
            self.logger.info(
                "Generating SQL query",
                text=text,
                platforms=platforms,
                query_type=query_type
            )
            
            # 1. Identify required tables and metrics
            tables, metrics = await self._identify_required_tables(text, query_type)
            
            # 2. Get temporal conditions
            time_range, time_params = self._parse_time_period(text)
            
            # 3. Get table relationships and join paths
            join_paths = await self._get_join_paths(tables)
            
            # 4. Find matching query template
            template = await self._get_query_template(text, query_type, metrics)
            
            # 5. Build the query using schema knowledge
            query = await self._build_query(
                template=template,
                tables=tables,
                join_paths=join_paths,
                metrics=metrics,
                time_range=time_range,
                platforms=platforms
            )
            
            # 6. Add parameters
            params = {
                **time_params,
                "platforms": list(platforms)
            }
            
            self.logger.info(
                "SQL query generated successfully",
                tables=tables,
                metrics=metrics,
                param_count=len(params)
            )
            
            return query, params, tables
            
        except Exception as e:
            self.logger.error(
                "Failed to generate SQL query",
                error=str(e),
                text=text,
                exc_info=True
            )
            raise
    
    async def _identify_required_tables(
        self,
        text: str,
        query_type: Optional[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Identify required tables and metrics based on query text.
        """
        tables = set()
        metrics = set()
        
        # Get all table schemas
        all_schemas = self.schema_registry.get_all_schemas()
        
        # Look for business terms in query
        for table_name, schema in all_schemas.items():
            # Check business terms in columns
            for column in schema.get("columns", []):
                business_term = column.get("business_term", "").lower()
                if business_term in text.lower():
                    tables.add(table_name)
                    if column.get("aggregation_rules"):
                        metrics.add(column["name"])
            
            # Check common metrics
            for metric in schema.get("common_metrics", []):
                if metric["name"].lower() in text.lower():
                    tables.add(table_name)
                    metrics.add(metric["name"])
        
        # Add tables based on query type
        if query_type:
            type_tables = self.schema_registry.get_tables_for_query_type(query_type)
            tables.update(type_tables)
        
        return list(tables), list(metrics)
    
    def _parse_time_period(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Parse time-related phrases and return SQL condition with parameters.
        """
        text = text.lower()
        current_date = datetime.utcnow()
        
        # Get time patterns from schema registry
        time_patterns = self.schema_registry.get_time_patterns()
        
        for pattern, time_func in time_patterns.items():
            if pattern in text:
                start_date, end_date = time_func(current_date)
                return (
                    "{date_field} BETWEEN @start_date AND @end_date",
                    {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    }
                )
        
        # Default to last 30 days
        start_date = current_date - timedelta(days=30)
        return (
            "{date_field} BETWEEN @start_date AND @end_date",
            {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": current_date.strftime("%Y-%m-%d")
            }
        )
    
    async def _get_join_paths(self, tables: List[str]) -> List[Dict]:
        """
        Get optimal join paths between required tables.
        """
        join_paths = []
        if len(tables) <= 1:
            return join_paths
            
        # Get relationship graph from registry
        relationships = self.schema_registry.get_relationships()
        
        # Find optimal join paths between tables
        for i in range(len(tables)-1):
            path = relationships.shortest_path(tables[i], tables[i+1])
            for j in range(len(path)-1):
                join_info = relationships.get_edge_data(path[j], path[j+1])
                join_paths.append({
                    "from_table": path[j],
                    "to_table": path[j+1],
                    "type": join_info["relationship_type"],
                    "keys": join_info["keys"]
                })
                
        return join_paths
    
    async def _get_query_template(
        self,
        text: str,
        query_type: Optional[str],
        metrics: List[str]
    ) -> str:
        """
        Get appropriate query template based on query characteristics.
        """
        # Get templates from registry
        templates = self.schema_registry.get_query_templates()
        
        # Try to find matching template
        for template in templates:
            if query_type and template["type"] == query_type:
                return template["template"]
            
            if all(metric in template["metrics"] for metric in metrics):
                return template["template"]
        
        # Return default template if no match found
        return templates["default"]["template"]
    
    async def _build_query(
        self,
        template: str,
        tables: List[str],
        join_paths: List[Dict],
        metrics: List[str],
        time_range: str,
        platforms: Set[str]
    ) -> str:
        """
        Build final SQL query using template and schema knowledge.
        """
        # Get schema information
        primary_table = tables[0]
        schema = self.schema_registry.get_table_schema(primary_table)
        
        # Replace table references
        query = template.replace(
            "{table}",
            f"`{self.project_id}.{self.dataset}.{primary_table}`"
        )
        
        # Add joins
        if join_paths:
            joins = []
            for join in join_paths:
                join_condition = self._build_join_condition(join)
                joins.append(f"JOIN `{self.project_id}.{self.dataset}.{join['to_table']}` ON {join_condition}")
            query = query.replace("{joins}", "\n".join(joins))
        
        # Add metric calculations
        metric_calculations = []
        for metric in metrics:
            metric_info = self.schema_registry.get_metric(metric)
            if metric_info:
                metric_calculations.append(
                    f"{metric_info['sql_template']} as {metric}"
                )
        
        if metric_calculations:
            query = query.replace(
                "{metrics}",
                ",\n".join(metric_calculations)
            )
        
        # Add time range
        date_field = schema["columns"]["order_date"]["name"]
        query = query.replace("{date_condition}", time_range.format(date_field=date_field))
        
        # Add platform filter
        platform_condition = "platform IN UNNEST(@platforms)" if platforms else "1=1"
        query = query.replace("{platform_condition}", platform_condition)
        
        return query.strip()
    
    def _build_join_condition(self, join_info: Dict) -> str:
        """
        Build SQL join condition from relationship information.
        """
        conditions = []
        for local_key, foreign_key in join_info["keys"].items():
            conditions.append(f"t1.{local_key} = t2.{foreign_key}")
        return " AND ".join(conditions)