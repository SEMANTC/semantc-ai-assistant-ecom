# ecommerce-ai-assistant/app/config/constants.py
"""
application constants

this module contains static configuration values and constants used throughout the application
"""

from typing import Dict, Set

# sql query templates
SQL_TEMPLATES = {
    "sales_total": """
        SELECT 
            platform,
            SUM(total_amount) as total_sales
        FROM `{dataset}.{table}`
        WHERE {date_condition}
        GROUP BY platform
    """,
    "inventory_count": """
        SELECT
            platform,
            COUNT(DISTINCT product_id) as product_count,
            SUM(quantity) as total_quantity
        FROM `{dataset}.{table}`
        WHERE {condition}
        GROUP BY platform
    """
}

# schema mappings
SCHEMA_MAPPINGS = {
    "shopify": {
        "orders": "shopify_orders",
        "products": "shopify_products",
        "customers": "shopify_customers"
    },
    "amazon": {
        "orders": "amazon_orders",
        "products": "amazon_products",
        "customers": "amazon_customers"
    },
    "ebay": {
        "orders": "ebay_orders",
        "products": "ebay_products",
        "customers": "ebay_customers"
    }
}

# query types and required tables
QUERY_TYPE_MAPPINGS: Dict[str, Set[str]] = {
    "sales": {"orders"},
    "inventory": {"products", "inventory"},
    "customers": {"customers", "orders"},
    "products": {"products"},
    "performance": {"orders", "products"}
}

# error messages
ERROR_MESSAGES = {
    "INVALID_QUERY": "The provided query is invalid or cannot be processed.",
    "MISSING_PLATFORM": "One or more required platforms are not available.",
    "EXECUTION_ERROR": "An error occurred while executing the query.",
    "TIMEOUT_ERROR": "The query execution timed out.",
    "PERMISSION_ERROR": "Insufficient permissions to access the requested data."
}

# date format templates
DATE_FORMATS = {
    "bigquery": "%Y-%m-%d",
    "iso": "%Y-%m-%dT%H:%M:%SZ",
    "display": "%B %d, %Y"
}

# metric definitions
METRICS = {
    "sales": {
        "total_sales": "SUM(total_amount)",
        "average_order_value": "AVG(total_amount)",
        "order_count": "COUNT(DISTINCT order_id)"
    },
    "inventory": {
        "stock_count": "SUM(quantity)",
        "unique_products": "COUNT(DISTINCT product_id)",
        "low_stock": "COUNT(CASE WHEN quantity <= reorder_point THEN 1 END)"
    }
}

# response templates
RESPONSE_TEMPLATES = {
    "sales": "Total sales for {period} were {amount} across {platforms}.",
    "inventory": "Current inventory shows {count} products with total quantity of {quantity}.",
    "error": "An error occurred: {error_message}"
}

# platform specific configurations
PLATFORM_CONFIGS = {
    "shopify": {
        "date_field": "created_at",
        "amount_field": "total_amount",
    },
    "amazon": {
        "date_field": "purchase_date",
        "amount_field": "item_price",
    },
    "ebay": {
        "date_field": "order_date",
        "amount_field": "total_price",
    }
}