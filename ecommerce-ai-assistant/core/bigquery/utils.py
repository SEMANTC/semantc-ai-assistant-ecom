# ecommerce-ai-assistant/core/bigquery/utils.py
from typing import Dict, List, Optional
from google.cloud import bigquery
import re

def format_schema_field(field: bigquery.SchemaField) -> Dict:
    """FORMAT A BIGQUERY SCHEMA FIELD INTO A DICTIONARY"""
    return {
        "name": field.name,
        "type": field.field_type,
        "mode": field.mode,
        "description": field.description,
        "fields": [
            format_schema_field(f) for f in field.fields
        ] if field.fields else None
    }

def clean_column_name(name: str) -> str:
    """CLEAN AND NORMALIZE COLUMN NAMES"""
    # remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    # replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # convert to lowercase
    return name.lower()

def format_value_for_bigquery(value: any) -> str:
    """FORMAT A PYTHON VALUE FOR BIGQUERY SQL"""
    if value is None:
        return 'NULL'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, bool):
        return str(value).upper()
    elif isinstance(value, (list, tuple)):
        return f"[{','.join(format_value_for_bigquery(v) for v in value)}]"
    else:
        return f"'{str(value)}'"

def get_table_ref(project_id: str, dataset_id: str, table_id: str) -> str:
    """CREATE A FULLY QUALIFIED TABLE REFERENCE"""
    return f"{project_id}.{dataset_id}.{table_id}"

def parse_table_ref(table_ref: str) -> Dict[str, str]:
    """PARSE A FULLY QUALIFIED TABLE REFERENCE"""
    parts = table_ref.split('.')
    if len(parts) != 3:
        raise ValueError("invalid table reference format")
    
    return {
        "project_id": parts[0],
        "dataset_id": parts[1],
        "table_id": parts[2]
    }

def estimate_query_cost(bytes_processed: int, rate_per_tb: float = 5.0) -> float:
    """
    ESTIMATE QUERY COST BASED ON BYTES PROCESSED
    DEFAULT RATE IS $5 PER TB
    """
    tb_processed = bytes_processed / (1024 ** 4)  # Convert bytes to TB
    return tb_processed * rate_per_tb

def format_query_plan(plan_entries: List[Dict]) -> str:
    """FORMAT QUERY PLAN ENTRIES FOR LOGGING"""
    formatted_plan = []
    for entry in plan_entries:
        formatted_plan.append(
            f"Step {entry.get('index', '?')}: "
            f"{entry.get('name', 'Unknown')} - "
            f"Records: {entry.get('records_read', '?')}, "
            f"Bytes: {entry.get('bytes_processed', '?')}"
        )
    return "\n".join(formatted_plan)