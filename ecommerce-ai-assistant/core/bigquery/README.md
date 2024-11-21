# BigQuery Integration Module

## Overview
This module handles all interactions with Google BigQuery, providing a robust interface for query execution and schema management.

## Components

### BigQuery Client (`client.py`)
Manages BigQuery operations with error handling and retries:
```python
from core.bigquery import BigQueryClient

# Initialize client
client = BigQueryClient()
await client.initialize()

# Execute query
results = await client.execute_query(
    query="SELECT * FROM `table` WHERE date = @date",
    params={"date": "2024-03-21"}
)
```

### Utilities (`utils.py`)
Helper functions for BigQuery operations:
```python
from core.bigquery import (
    format_schema_field,
    clean_column_name,
    estimate_query_cost
)

# Format schema
schema = format_schema_field(field)

# Clean column names
clean_name = clean_column_name("Raw Column Name")

# Estimate costs
cost = estimate_query_cost(bytes_processed=1000000)
```

## Usage Examples

### 1. Query Execution
```python
# Execute with parameters
results = await client.execute_query(
    query="""
        SELECT *
        FROM `project.dataset.table`
        WHERE date BETWEEN @start_date AND @end_date
          AND platform IN UNNEST(@platforms)
    """,
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "platforms": ["shopify", "amazon"]
    }
)
```

### 2. Schema Management
```python
# Get table schema
schema = await client.get_table_schema("project.dataset.table")

# Validate table
exists = await client.validate_table_exists("project.dataset.table")
```

### 3. Cost Estimation
```python
# Estimate query cost
bytes_processed = query_job.total_bytes_processed
estimated_cost = estimate_query_cost(bytes_processed)
```

## Error Handling

### 1. Client Errors
```python
try:
    results = await client.execute_query(query)
except Exception as e:
    logger.error("Query failed", error=str(e))
```

### 2. Validation Errors
```python
if not await client.validate_dataset(dataset_ref):
    raise ValueError(f"Invalid dataset: {dataset_ref}")
```

## Performance Considerations

### 1. Query Optimization
- Use query parameters
- Set appropriate timeouts
- Monitor bytes processed
- Use column pruning

### 2. Resource Management
- Close clients properly
- Handle connection pooling
- Set maximum bytes billed
- Monitor query quotas

## Best Practices

### 1. Query Parameters
```python
# Do: Use parameters
query = "SELECT * FROM table WHERE date = @date"
params = {"date": "2024-03-21"}

# Don't: String concatenation
# query = f"SELECT * FROM table WHERE date = '{date}'"
```

### 2. Error Handling
```python
try:
    results = await client.execute_query(query)
except Exception as e:
    logger.error("Query failed", error=str(e))
    # Handle specific error types
```

### 3. Resource Cleanup
```python
try:
    results = await client.execute_query(query)
finally:
    await client.close()
```

## Configuration

### Environment Variables
```env
PROJECT_ID=your-project-id
BIGQUERY_DATASET=your-dataset
BQ_LOCATION=US
BQ_JOB_TIMEOUT=300
BQ_MAXIMUM_BYTES_BILLED=1000000000
```

## Testing

### 1. Client Tests
```python
async def test_query_execution():
    client = BigQueryClient()
    results = await client.execute_query("SELECT 1")
    assert results is not None
```

### 2. Utility Tests
```python
def test_clean_column_name():
    assert clean_column_name("Raw Name!") == "raw_name"
```

## Future Enhancements
- [ ] Query caching
- [ ] Connection pooling
- [ ] Advanced monitoring
- [ ] Cost optimization
- [ ] Query plan analysis
- [ ] Batch operations
- [ ] Schema synchronization

## Contributing
When adding features:
1. Add appropriate error handling
2. Include logging
3. Add tests
4. Update documentation
5. Follow Google Cloud best practices

## Dependencies
- google-cloud-bigquery
- pydantic
- structlog