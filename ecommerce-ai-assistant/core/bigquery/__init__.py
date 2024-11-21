"""
bigquery integration module

this module handles all bigquery interactions for the e-commerce ai assistant,
providing a clean interface for query execution and schema management
"""

from .client import BigQueryClient
from .utils import (
    format_schema_field,
    clean_column_name,
    format_value_for_bigquery,
    get_table_ref,
    parse_table_ref,
    estimate_query_cost,
    format_query_plan
)

__all__ = [
    "BigQueryClient",
    "format_schema_field",
    "clean_column_name",
    "format_value_for_bigquery",
    "get_table_ref",
    "parse_table_ref",
    "estimate_query_cost",
    "format_query_plan"
]