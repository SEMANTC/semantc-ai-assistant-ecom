# Configuration Package

## Overview
This package manages all configuration aspects of the E-commerce AI Assistant, including environment variables, settings management, and constants.

## Components

### Settings (`settings.py`)
Manages application settings using Pydantic BaseSettings for automatic environment variable loading and validation.

```python
from app.config import settings

# Usage
print(settings.PROJECT_NAME)
print(settings.is_production)
```

### Constants (`constants.py`)
Contains static configuration values, templates, and mappings used throughout the application.

```python
from app.config.constants import SQL_TEMPLATES, METRICS

# Usage
query_template = SQL_TEMPLATES["sales_total"]
sales_metrics = METRICS["sales"]
```

## Environment Variables
Required environment variables for the application:

```env
# Basic Configuration
ENVIRONMENT=development
DEBUG=True

# GCP Configuration
PROJECT_ID=your-project-id
DATASET_ID=your-dataset-id
BIGQUERY_DATASET=your-bigquery-dataset

# API Configuration
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## Usage Examples

### Loading Settings
```python
from app.config import settings

# Access settings
if settings.is_production:
    # Production configuration
    max_retries = settings.MAX_RETRIES
else:
    # Development configuration
    max_retries = 1
```

### Using Constants
```python
from app.config.constants import SCHEMA_MAPPINGS, ERROR_MESSAGES

# Get table name for platform
table_name = SCHEMA_MAPPINGS["shopify"]["orders"]

# Get error message
error_msg = ERROR_MESSAGES["INVALID_QUERY"]
```

### Query Templates
```python
from app.config.constants import SQL_TEMPLATES

query = SQL_TEMPLATES["sales_total"].format(
    dataset="my_dataset",
    table="orders",
    date_condition="date >= '2024-01-01'"
)
```

## Configuration Hierarchy
1. Environment Variables
2. .env File
3. Default Values

## Best Practices
1. Always use type hints
2. Keep sensitive information in environment variables
3. Use constants for repeated values
4. Document all configuration options
5. Validate settings on startup

## Adding New Configuration
When adding new configuration options:

1. Add to Settings class:
```python
class Settings(BaseSettings):
    NEW_OPTION: str = "default_value"
```

2. Add to .env.example:
```env
NEW_OPTION=example_value
```

3. Update documentation

## Security Notes
- Never commit sensitive values
- Use secret management in production
- Validate all configuration values
- Log configuration changes