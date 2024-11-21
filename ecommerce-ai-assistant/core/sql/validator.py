# ecommerce-ai-assistant/core/sql/validator.py
from typing import Dict, List, Optional, Set, Tuple
import re
from google.cloud import bigquery
from app.config import settings
from utils.logger import get_logger
from core.metadata import SchemaRegistry

class SQLValidator:
    """
    Validates SQL queries using schema metadata and security rules.
    """
    
    def __init__(self, schema_registry: SchemaRegistry):
        self.schema_registry = schema_registry
        self.logger = get_logger(__name__)
        self.project_id = settings.PROJECT_ID
        self.dataset = settings.BIGQUERY_DATASET
        self.client = bigquery.Client()
        
    async def validate_query(
        self,
        query: str,
        parameters: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query for security and correctness.
        
        Args:
            query: SQL query to validate
            parameters: Query parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # 1. Basic security checks
            if await self._has_security_risks(query):
                return False, "Query contains security risks"
            
            # 2. Extract and validate table references
            tables = await self._extract_table_references(query)
            if not tables:
                return False, "No valid table references found"
                
            if not await self._validate_tables(tables):
                return False, "Invalid or inaccessible table references"
            
            # 3. Validate column references
            if not await self._validate_columns(query, tables):
                return False, "Invalid column references"
            
            # 4. Validate joins and relationships
            if not await self._validate_joins(query, tables):
                return False, "Invalid join conditions or table relationships"
            
            # 5. Validate aggregations and grouping
            if not await self._validate_aggregations(query):
                return False, "Invalid aggregation or grouping"
            
            # 6. Validate platform conditions
            if not await self._validate_platform_conditions(query):
                return False, "Invalid platform conditions"
            
            # 7. Validate parameters
            if parameters and not await self._validate_parameters(query, parameters):
                return False, "Invalid query parameters"
            
            # 8. Perform dry run
            dry_run_error = await self._perform_dry_run(query, parameters)
            if dry_run_error:
                return False, f"Dry run failed: {dry_run_error}"
            
            return True, None
            
        except Exception as e:
            self.logger.error(
                "Query validation failed",
                error=str(e),
                query=query,
                exc_info=True
            )
            return False, f"Validation error: {str(e)}"
    
    async def _has_security_risks(self, query: str) -> bool:
        """Check for SQL injection and other security risks."""
        # Get security patterns from schema registry
        security_patterns = [
            r';\s*DROP\s+',
            r';\s*DELETE\s+',
            r';\s*INSERT\s+',
            r';\s*UPDATE\s+',
            r';\s*MERGE\s+',
            r'--',
            r'/\*.*\*/',
            r'UNION\s+ALL\s+SELECT',
            r'UNION\s+SELECT'
        ]
        
        # Check each pattern
        query_upper = query.upper()
        for pattern in security_patterns:
            if re.search(pattern, query_upper):
                self.logger.warning(
                    "Security risk detected",
                    pattern=pattern,
                    query=query
                )
                return True
        
        return False
    
    async def _extract_table_references(self, query: str) -> Set[str]:
        """Extract all table references from the query."""
        tables = set()
        
        # Match both FROM and JOIN clauses
        table_pattern = r'(?:FROM|JOIN)\s+`?([^`\s]+)`?(?:\s+AS\s+\w+)?'
        
        for match in re.finditer(table_pattern, query, re.IGNORECASE):
            table_ref = match.group(1)
            
            # Handle fully qualified names
            parts = table_ref.split('.')
            if len(parts) == 3:  # project.dataset.table
                tables.add(parts[2])
            elif len(parts) == 2:  # dataset.table
                tables.add(parts[1])
            else:  # just table
                tables.add(parts[0])
        
        return tables
    
    async def _validate_tables(self, tables: Set[str]) -> bool:
        """Validate table existence and permissions."""
        for table in tables:
            # Check schema registry
            if not self.schema_registry.table_exists(table):
                self.logger.error(f"Table {table} not found in schema registry")
                return False
            
            # Check BigQuery
            try:
                table_ref = f"{self.project_id}.{self.dataset}.{table}"
                self.client.get_table(table_ref)
            except Exception as e:
                self.logger.error(f"Table {table} access error", error=str(e))
                return False
        
        return True
    
    async def _validate_columns(self, query: str, tables: Set[str]) -> bool:
        """Validate column references against schema."""
        # Extract column references
        columns = set()
        
        # Handle SELECT columns
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, query, re.IGNORECASE | re.DOTALL)
        if select_match:
            cols = select_match.group(1).split(',')
            columns.update(self._clean_column_references(cols))
        
        # Handle WHERE, GROUP BY, and HAVING columns
        condition_pattern = r'(?:WHERE|GROUP BY|HAVING)\s+(.*?)(?:(?:GROUP BY|HAVING|ORDER BY|LIMIT)\s+|$)'
        for match in re.finditer(condition_pattern, query, re.IGNORECASE | re.DOTALL):
            cols = match.group(1).split(',')
            columns.update(self._clean_column_references(cols))
        
        # Validate each column
        for column in columns:
            if not await self._is_valid_column(column, tables):
                self.logger.error(f"Invalid column reference: {column}")
                return False
        
        return True
    
    def _clean_column_references(self, columns: List[str]) -> Set[str]:
        """Clean and extract actual column names from SQL expressions."""
        cleaned = set()
        for col in columns:
            col = col.strip()
            if col == '*':
                continue
                
            # Remove aliases
            if ' AS ' in col.upper():
                col = col.split(' AS ')[0].strip()
            
            # Remove functions
            col = re.sub(r'\w+\((.*?)\)', r'\1', col)
            
            # Remove table qualifiers
            if '.' in col:
                col = col.split('.')[-1]
            
            # Remove quotes
            col = col.strip('`"\'')
            
            if col:
                cleaned.add(col)
        
        return cleaned
    
    async def _validate_joins(self, query: str, tables: Set[str]) -> bool:
        """Validate join conditions against defined relationships."""
        if len(tables) <= 1:
            return True
            
        # Extract join conditions
        join_pattern = r'JOIN\s+`?(\w+)`?\s+(?:AS\s+\w+\s+)?ON\s+(.*?)(?:(?:JOIN|WHERE|GROUP)\s+|$)'
        
        for match in re.finditer(join_pattern, query, re.IGNORECASE | re.DOTALL):
            joined_table = match.group(1)
            join_condition = match.group(2)
            
            # Validate relationship exists
            if not self.schema_registry.has_relationship(tables, joined_table):
                self.logger.error(f"No valid relationship found for join with {joined_table}")
                return False
            
            # Validate join keys
            if not await self._validate_join_keys(join_condition, joined_table):
                return False
        
        return True
    
    async def _validate_aggregations(self, query: str) -> bool:
        """Validate aggregation functions and GROUP BY clauses."""
        # Check for aggregation functions
        agg_pattern = r'(COUNT|SUM|AVG|MIN|MAX)\s*\('
        has_aggregation = bool(re.search(agg_pattern, query, re.IGNORECASE))
        
        # Check for GROUP BY
        has_group_by = 'GROUP BY' in query.upper()
        
        # If using aggregation, must have GROUP BY for non-aggregated columns
        if has_aggregation and not has_group_by:
            select_pattern = r'SELECT\s+(.*?)\s+FROM'
            select_match = re.search(select_pattern, query, re.IGNORECASE)
            if select_match:
                select_columns = select_match.group(1)
                non_agg_cols = [
                    col.strip() for col in select_columns.split(',')
                    if not re.search(agg_pattern, col, re.IGNORECASE)
                    and col.strip() != '*'
                ]
                
                if non_agg_cols:
                    self.logger.error("Non-aggregated columns without GROUP BY")
                    return False
        
        return True
    
    async def _validate_platform_conditions(self, query: str) -> bool:
        """Validate platform-related conditions."""
        if 'platform' in query.lower():
            # Ensure platform column exists in referenced tables
            tables = await self._extract_table_references(query)
            platform_exists = False
            
            for table in tables:
                schema = self.schema_registry.get_table_schema(table)
                if schema and 'platform' in schema.get('columns', {}):
                    platform_exists = True
                    break
            
            if not platform_exists:
                self.logger.error("Platform condition used but no platform column exists")
                return False
        
        return True
    
    async def _validate_parameters(self, query: str, parameters: Dict) -> bool:
        """Validate query parameters."""
        # Extract parameter references from query
        param_pattern = r'@(\w+)'
        referenced_params = set(re.findall(param_pattern, query))
        
        # Check all referenced parameters are provided
        for param in referenced_params:
            if param not in parameters:
                self.logger.error(f"Missing parameter: {param}")
                return False
        
        return True
    
    async def _perform_dry_run(
        self,
        query: str,
        parameters: Optional[Dict] = None
    ) -> Optional[str]:
        """Perform BigQuery dry run."""
        try:
            job_config = bigquery.QueryJobConfig(dry_run=True)
            
            # Add query parameters if provided
            if parameters:
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(
                        name,
                        self._get_parameter_type(value),
                        value
                    )
                    for name, value in parameters.items()
                ]
            
            # Perform dry run
            query_job = self.client.query(
                query,
                job_config=job_config
            )
            
            # Check estimated bytes processed
            bytes_processed = query_job.total_bytes_processed
            if bytes_processed > settings.MAX_BYTES_PROCESSED:
                return f"Query would process {bytes_processed} bytes (limit: {settings.MAX_BYTES_PROCESSED})"
            
            return None
            
        except Exception as e:
            return str(e)
    
    def _get_parameter_type(self, value: any) -> str:
        """Determine BigQuery parameter type from Python value."""
        if isinstance(value, bool):
            return 'BOOL'
        elif isinstance(value, int):
            return 'INT64'
        elif isinstance(value, float):
            return 'FLOAT64'
        elif isinstance(value, str):
            return 'STRING'
        elif isinstance(value, (list, tuple, set)):
            return 'ARRAY'
        else:
            return 'STRING'