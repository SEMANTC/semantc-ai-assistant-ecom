# SQL Processing Module

## Overview
This module handles SQL query generation from natural language and query validation for the E-commerce AI Assistant.

## Components

### SQL Generator (`generator.py`)
Converts natural language queries into SQL, handling:
- Time period parsing
- Platform-specific fields
- Query templates
- Parameter generation

```python
from core.sql import SQLGenerator

generator = SQLGenerator()
query, params = await generator.generate_query(
    text="What were my total sales last month?",
    platforms={"shopify", "amazon"},
    query_type="sales"
)
```

### SQL Validator (`validator.py`)
Validates SQL queries for:
- SQL injection risks
- Table existence
- Query structure
- Query execution

```python
from core.sql import SQLValidator

validator = SQLValidator()
is_valid = await validator.validate_query(query)
```

## Usage Examples

### 1. Basic Query Generation
```python
generator = SQLGenerator()

# Generate sales query
query, params = await generator.generate_query(
    text="Show me sales from last month",
    platforms={"shopify"},
    query_type="sales"
)

# The generated query might look like:
"""
SELECT 
    platform,
    SUM(total_amount) as total_sales
FROM `project.dataset.consolidated_orders`
WHERE created_at BETWEEN @start_date AND @end_date
AND platform = 'shopify'
GROUP BY platform
"""
```

### 2. Query Validation
```python
validator = SQLValidator()

# Validate query
if await validator.validate_query(query):
    # Execute query
    ...
else:
    # Handle invalid query
    ...
```

## Query Templates
Templates are defined in `app.config.constants`:

```python
SQL_TEMPLATES = {
    "sales_total": """
        SELECT 
            platform,
            SUM(total_amount) as total_sales
        FROM `{dataset}.{table}`
        WHERE {date_condition}
        GROUP BY platform
    """
}
```

## Security Features

### 1. SQL Injection Prevention
- Parameter binding
- Pattern detection
- Query structure validation

### 2. Access Control
- Table reference validation
- Project/dataset validation
- Permission checking

## Best Practices

### 1. Query Generation
- Use parameterized queries
- Validate all inputs
- Handle platform differences
- Include proper error handling

### 2. Query Validation
- Check table existence
- Validate query structure
- Use dry runs
- Log validation failures

## Testing
```bash
# Run SQL module tests
pytest tests/core/sql/

# Test specific components
pytest tests/core/sql/test_generator.py
pytest tests/core/sql/test_validator.py
```

## Contributing
When adding new features:
1. Add appropriate tests
2. Update documentation
3. Follow security best practices
4. Add logging statements
5. Update query templates if needed

## Future Enhancements
- [ ] Add query optimization logic
- [ ] Implement query cost estimation
- [ ] Add support for more complex analytical queries
- [ ] Implement query caching
- [ ] Add query performance metrics collection
- [ ] Enhance time period parsing
- [ ] Add support for custom templates
- [ ] Implement query plan analysis

## Error Handling

### Query Generation Errors
```python
try:
    query, params = await generator.generate_query(text, platforms)
except ValueError as e:
    # Handle invalid input
    logger.error("Invalid query input", error=str(e))
except Exception as e:
    # Handle unexpected errors
    logger.error("Query generation failed", error=str(e))
```

### Validation Errors
```python
class ValidationError(Exception):
    def __init__(self, message: str, query: str):
        self.message = message
        self.query = query
        super().__init__(self.message)

# Usage
if not await validator.validate_query(query):
    raise ValidationError("Invalid query structure", query)
```

## Performance Considerations

### Query Optimization
- Use appropriate indexes
- Limit result sets
- Optimize JOIN operations
- Use column pruning
- Consider partitioning

```python
# Example of optimized query template
OPTIMIZED_TEMPLATE = """
SELECT {selected_columns}
FROM `{dataset}.{table}`
WHERE {date_condition}
    AND platform IN UNNEST(@platforms)
{group_by}
{having}
LIMIT @limit
"""
```

### Resource Management
- Set query timeout
- Implement retry logic
- Handle connection pooling
- Monitor query costs

```python
# Example configuration
QUERY_TIMEOUT = 30  # seconds
MAX_ROWS = 10000
RETRY_ATTEMPTS = 3
```

## Monitoring and Logging

### Query Metrics
- Generation time
- Validation time
- Query execution time
- Error rates
- Resource usage

```python
# Example logging
logger.info(
    "Query metrics",
    generation_time=gen_time,
    validation_time=val_time,
    query_size=len(query),
    tables_referenced=len(tables)
)
```

### Performance Tracking
```python
from utils.logger import log_execution_time

@log_execution_time(logger)
async def generate_and_validate(text: str, platforms: Set[str]):
    query, params = await generator.generate_query(text, platforms)
    is_valid = await validator.validate_query(query)
    return query, params, is_valid
```

## Integration Examples

### With BigQuery
```python
from google.cloud import bigquery

async def execute_query(query: str, params: Dict):
    client = bigquery.Client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", params["start_date"]),
            bigquery.ScalarQueryParameter("end_date", "DATE", params["end_date"]),
        ]
    )
    
    query_job = client.query(query, job_config=job_config)
    return query_job.result()
```

### With Response Formatting
```python
async def process_query_results(results, query_type: str):
    if query_type == "sales":
        return {
            "total_sales": sum(row.total_sales for row in results),
            "by_platform": {row.platform: row.total_sales for row in results}
        }
    # Add more result processing logic
```

## Common Patterns

### Time Period Handling
```python
# Example time patterns
TIME_PATTERNS = {
    "last_month": lambda: (start_of_last_month(), end_of_last_month()),
    "this_year": lambda: (start_of_year(), today()),
    "last_7_days": lambda: (days_ago(7), today())
}
```

### Platform-Specific Logic
```python
# Example platform configurations
PLATFORM_CONFIGS = {
    "shopify": {
        "date_field": "created_at",
        "amount_field": "total_amount"
    },
    "amazon": {
        "date_field": "order_date",
        "amount_field": "item_total"
    }
}
```

## Troubleshooting Guide

### Common Issues

1. **Invalid Query Structure**
   ```python
   # Check query structure
   if not re.search(r'^\s*SELECT', query, re.IGNORECASE):
       logger.error("Query must start with SELECT")
   ```

2. **Missing Tables**
   ```python
   # Validate table existence
   if not await validator._validate_table_references(query):
       logger.error("One or more tables do not exist")
   ```

3. **Performance Issues**
   ```python
   # Monitor query performance
   if execution_time > QUERY_TIMEOUT:
       logger.warning("Query execution exceeded timeout")
   ```

## API Reference

### SQLGenerator
```python
class SQLGenerator:
    async def generate_query(
        text: str,
        platforms: Set[str],
        query_type: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Generate SQL query from natural language.
        
        Args:
            text: Natural language query
            platforms: Set of platforms to query
            query_type: Optional query type hint
            
        Returns:
            Tuple of (SQL query, query parameters)
        """
```

### SQLValidator
```python
class SQLValidator:
    async def validate_query(query: str) -> bool:
        """
        Validate SQL query for security and correctness.
        
        Args:
            query: SQL query to validate
            
        Returns:
            bool: True if query is valid
        """
```

## Dependencies
- google-cloud-bigquery
- sqlparse
- structlog
- pydantic

## License
Proprietary - All rights reserved.