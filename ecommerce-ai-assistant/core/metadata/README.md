# Metadata Management Module

## Overview
This module manages the schema metadata, table relationships, and business rules for the E-commerce AI Assistant. It provides a central registry for all data model information used in query generation and validation.

## Components

### Schema Registry (`schema_registry.py`)
Core component that manages:
- Table schemas and relationships
- Business glossary
- Query templates
- Metric definitions
- Time patterns

```python
from core.metadata import SchemaRegistry

# Initialize registry
registry = SchemaRegistry()
await registry.initialize()

# Access metadata
schema = registry.get_table_schema("orders")
relationships = registry.get_relationships()
```

## Schema Structure

### Directory Layout
```
knowledge_base/
└── schemas/
    ├── shopify/
    │   ├── orders.yaml
    │   ├── products.yaml
    │   └── customers.yaml
    ├── amazon/
    │   ├── orders.yaml
    │   ├── products.yaml
    │   └── customers.yaml
    ├── ebay/
    │   ├── orders.yaml
    │   ├── products.yaml
    │   └── customers.yaml
    └── consolidated/
        ├── all_orders.yaml
        ├── all_products.yaml
        └── all_customers.yaml
```

### Example Schema Definition
```yaml
# Example: consolidated/all_orders.yaml

table_name: consolidated_orders
description: "Consolidated order information across all platforms"
update_frequency: "hourly"
platforms: ["shopify", "amazon", "ebay"]

# Primary keys and relationships
keys:
  primary_key: "order_id"
  platform_keys:
    shopify: "shopify_order_id"
    amazon: "amazon_order_id"
    ebay: "ebay_order_id"

# Column definitions
columns:
  - name: order_id
    type: STRING
    description: "Unique identifier for the order"
    is_required: true
    business_term: "Order ID"
    
  - name: platform
    type: STRING
    description: "Source platform for the order"
    is_required: true
    enums:
      - shopify
      - amazon
      - ebay
    business_term: "Sales Channel"
    
  - name: order_date
    type: TIMESTAMP
    description: "Date and time when the order was placed"
    is_required: true
    business_term: "Order Date"
    platform_fields:
      shopify: "created_at"
      amazon: "purchase_date"
      ebay: "creation_date"
      
  - name: total_amount
    type: DECIMAL
    description: "Total order amount including tax and shipping"
    is_required: true
    business_term: "Order Total"
    aggregation_rules:
      - SUM
      - AVG
    platform_fields:
      shopify: "total_price"
      amazon: "order_total"
      ebay: "total_amount"

# Relationships
relationships:
  - table: "order_items"
    type: "one_to_many"
    keys:
      local: "order_id"
      foreign: "order_id"
    description: "Items included in this order"
    
  - table: "customers"
    type: "many_to_one"
    keys:
      local: "customer_id"
      foreign: "customer_id"
    description: "Customer who placed the order"

# Common queries and aggregations
common_metrics:
  - name: "total_sales"
    description: "Total sales amount"
    sql_template: "SUM(total_amount)"
    
  - name: "order_count"
    description: "Number of orders"
    sql_template: "COUNT(DISTINCT order_id)"
    
  - name: "average_order_value"
    description: "Average order value"
    sql_template: "AVG(total_amount)"

# Business rules
business_rules:
  - name: "valid_order"
    description: "Conditions for a valid order"
    conditions:
      - "total_amount > 0"
      - "order_date is not null"
      
  - name: "completed_order"
    description: "Conditions for a completed order"
    conditions:
      - "status = 'completed'"
      - "payment_status = 'paid'"

# Query templates
query_templates:
  - name: "sales_by_platform"
    type: "sales"
    description: "Get sales grouped by platform"
    template: >
      SELECT 
        platform,
        COUNT(DISTINCT order_id) as order_count,
        SUM(total_amount) as total_sales
      FROM {table}
      WHERE {date_condition}
      GROUP BY platform

  - name: "daily_sales"
    type: "sales"
    description: "Get daily sales metrics"
    template: >
      SELECT 
        DATE(order_date) as date,
        platform,
        COUNT(DISTINCT order_id) as orders,
        SUM(total_amount) as sales
      FROM {table}
      WHERE {date_condition}
      GROUP BY date, platform
      ORDER BY date DESC
```

## Usage

### Loading Schemas
```python
# Initialize registry
registry = SchemaRegistry()
await registry.initialize()
```

### Accessing Metadata
```python
# Get table schema
schema = registry.get_table_schema("consolidated_orders")

# Check relationships
has_relation = registry.has_relationship("orders", "customers")

# Get business terms
term = registry.get_business_term("total_amount")

# Get query templates
template = registry.get_query_template("sales_by_platform")
```

### Validation
```python
# Validate table existence
if registry.table_exists("orders"):
    # Process table
    pass

# Get column type
col_type = registry.get_column_type("orders", "total_amount")
```

### Platform-Specific
```python
# Get platform tables
shopify_tables = registry.get_platform_tables("shopify")

# Get all platforms
platforms = registry.get_all_platforms()
```

## Schema Requirements

1. **Required Fields**
   - table_name
   - columns
   - platform (if platform-specific)

2. **Column Properties**
   - name
   - type
   - description
   - business_term (optional)
   - is_required (optional)
   - enums (optional)
   - platform_fields (optional)

3. **Relationships**
   - table
   - type
   - keys
   - description

## Best Practices

1. **Schema Organization**
   - Use platform-specific directories
   - Keep consolidated schemas separate
   - Use clear, descriptive names

2. **Metadata Management**
   - Document all business terms
   - Include clear descriptions
   - Define relationships explicitly
   - Include common query patterns

3. **Updates and Maintenance**
   - Keep schemas in version control
   - Document changes
   - Update relationships when schema changes
   - Validate schemas before deployment

## Future Enhancements
- [ ] Schema versioning
- [ ] Change tracking
- [ ] Automated validation
- [ ] Schema visualization
- [ ] Impact analysis
- [ ] Query optimization hints
- [ ] Caching improvements

## Contributing
When adding or modifying schemas:
1. Follow the schema template
2. Include all required fields
3. Document relationships
4. Add business terms
5. Include common queries
6. Update tests

## Testing
```bash
# Run metadata tests
pytest tests/core/metadata/

# Test schema loading
pytest tests/core/metadata/test_schema_registry.py
```