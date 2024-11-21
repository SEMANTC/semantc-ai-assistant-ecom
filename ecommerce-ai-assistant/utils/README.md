# Utils Package

## Overview
The utils package contains shared utilities and helper functions used throughout the E-commerce AI Assistant application. These utilities are designed to provide consistent logging, monitoring, and helper functions.

## Components

### Logger (`logger.py`)
Advanced structured logging implementation with context management and performance monitoring.

#### Key Features:
- JSON-formatted logs
- Contextual logging with metadata
- Performance monitoring
- Environment-aware logging
- Log level configuration

#### Basic Usage:
```python
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Basic logging
logger.info("Processing request", user_id="123")

# Error logging
logger.error("Query failed", query_id="abc", error="Invalid syntax")
```

#### Context Management:
```python
from utils.logger import LogContext

# Add temporary context to logs
with LogContext(request_id="abc-123", user_id="user_456"):
    logger.info("Processing query")  # Will include context automatically
```

#### Performance Monitoring:
```python
from utils.logger import log_execution_time

logger = get_logger(__name__)

@log_execution_time(logger)
def process_complex_query(query: str):
    # Function implementation
    pass
```

### Log Levels
```python
# Available log levels
logger.debug("Debug message")    # Detailed debugging information
logger.info("Info message")      # General information
logger.warning("Warning")        # Warning messages
logger.error("Error")           # Error messages
logger.critical("Critical")     # Critical errors
```

### Configuration
Configure logging through environment variables:
```env
LOG_LEVEL=INFO                # Set logging level
LOG_FORMAT=json              # Set log format (json/text)
ENVIRONMENT=development      # Set environment
```

## Best Practices

### 1. Structured Logging
Always include relevant context in log messages:
```python
# Good
logger.info("Query processed", query_id="123", duration_ms=45)

# Avoid
logger.info("Query 123 processed in 45ms")  # Hard to parse
```

### 2. Error Logging
Include full context when logging errors:
```python
try:
    process_query(query)
except Exception as e:
    logger.error(
        "Query processing failed",
        query_id=query.id,
        error=str(e),
        exc_info=True
    )
```

### 3. Performance Monitoring
Use the execution time decorator for important functions:
```python
@log_execution_time(logger)
def generate_sql(text: str):
    # Implementation
    pass
```

## Example Log Output
```json
{
    "timestamp": "2024-03-21T15:30:45.123Z",
    "level": "INFO",
    "environment": "production",
    "event": "SQL query generated",
    "query_id": "abc-123",
    "duration_ms": 150,
    "user_id": "user_456",
    "platform": "shopify"
}
```

## Integration with Other Components

### SQL Generation Logging
```python
from utils.logger import get_logger, LogContext

logger = get_logger(__name__)

def generate_sql(text: str, context: dict):
    with LogContext(**context):
        logger.info("Starting SQL generation", input_text=text)
        # Implementation
```

### BigQuery Integration
```python
@log_execution_time(logger)
async def execute_query(query: str):
    logger.info("Executing BigQuery query", query_length=len(query))
    # Query execution
```

### Error Tracking
```python
def process_request(request_data: dict):
    try:
        with LogContext(request_id=request_data.get("id")):
            # Processing
            logger.info("Request processed successfully")
    except Exception as e:
        logger.error(
            "Request processing failed",
            error=str(e),
            exc_info=True
        )
```

## Future Enhancements
- [ ] Add metrics collection
- [ ] Implement log aggregation
- [ ] Add request tracing
- [ ] Enhance performance monitoring
- [ ] Add log rotation

## Contributing
When adding new utility functions:
1. Add appropriate logging
2. Include type hints
3. Add documentation
4. Follow existing patterns
5. Add tests

## Testing
```bash
# Run utils tests
pytest tests/utils/
```