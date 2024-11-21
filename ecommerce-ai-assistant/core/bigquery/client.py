# ecommerce-ai-assistant/core/bigquery/client.py
from typing import Dict, List, Optional, Union
from google.cloud import bigquery
from google.api_core import retry
from datetime import datetime
import asyncio
import json

from app.config import settings
from utils.logger import get_logger
from .utils import format_schema_field, clean_column_name

class BigQueryClient:
    """
    MANAGES BIGQUERY OPERATIONS WITH ERROR HANDLING AND RETRIES
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.project_id = settings.PROJECT_ID
        self.dataset_id = settings.BIGQUERY_DATASET
        self.client = None
        self.job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=settings.BQ_MAXIMUM_BYTES_BILLED
        )
    
    async def initialize(self) -> None:
        """INITIALIZE BIGQUERY CLIENT AND VALIDATE CONNECTION"""
        try:
            self.client = bigquery.Client()
            await self.validate_dataset(f"{self.project_id}.{self.dataset_id}")
            self.logger.info(
                "bigquery client initialized",
                project=self.project_id,
                dataset=self.dataset_id
            )
        except Exception as e:
            self.logger.error(
                "failed to initialize BigQuery client",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def validate_dataset(self, dataset_ref: str) -> bool:
        """VALIDATE DATASET EXISTS AND IS ACCESSIBLE"""
        try:
            dataset = self.client.get_dataset(dataset_ref)
            return True
        except Exception as e:
            self.logger.error(
                "dataset validation failed",
                dataset=dataset_ref,
                error=str(e)
            )
            raise
    
    @retry.Retry()
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> List[Dict]:
        """
        EXECUTE A BIGQUERY QUERY WITH RETRIES AND ERROR HANDLING
        
        args:
            query: sql query to execute
            params: query parameters
            timeout: query timeout in seconds
            
        returns:
            list of row dictionaries
        """
        try:
            # configure job
            job_config = self.job_config.copy()
            job_config.query_parameters = self._create_query_parameters(params)
            job_config.timeout_ms = (timeout or settings.BQ_JOB_TIMEOUT) * 1000
            
            # log query execution
            self.logger.info(
                "executing BigQuery query",
                query_length=len(query),
                param_count=len(params) if params else 0
            )
            
            # execute query
            query_job = self.client.query(
                query,
                job_config=job_config,
                location=settings.BQ_LOCATION
            )
            
            # wait for results
            results = query_job.result()
            
            # convert to list of dicts
            rows = [dict(row.items()) for row in results]
            
            self.logger.info(
                "query executed successfully",
                row_count=len(rows),
                bytes_processed=query_job.total_bytes_processed,
                execution_time=query_job.ended - query_job.started
            )
            
            return rows
            
        except Exception as e:
            self.logger.error(
                "query execution failed",
                error=str(e),
                query=query,
                params=params,
                exc_info=True
            )
            raise
    
    async def get_table_schema(self, table_ref: str) -> List[Dict]:
        """GET SCHEMA INFORMATION FOR A TABLE"""
        try:
            table = self.client.get_table(table_ref)
            return [format_schema_field(field) for field in table.schema]
        except Exception as e:
            self.logger.error(
                "failed to get table schema",
                table=table_ref,
                error=str(e)
            )
            raise
    
    async def validate_table_exists(self, table_ref: str) -> bool:
        """CHECK IF A TABLE EXISTS"""
        try:
            self.client.get_table(table_ref)
            return True
        except Exception:
            return False
    
    def _create_query_parameters(
        self,
        params: Optional[Dict]
    ) -> List[bigquery.ScalarQueryParameter]:
        """CONVERT PARAMETERS DICT TO BIGQUERY PARAMETERS"""
        if not params:
            return []
            
        query_params = []
        for name, value in params.items():
            param_type = self._get_parameter_type(value)
            query_params.append(
                bigquery.ScalarQueryParameter(
                    name,
                    param_type,
                    value
                )
            )
        return query_params
    
    def _get_parameter_type(self, value: any) -> str:
        """DETERMINE BIGQUERY PARAMETER TYPE FROM PYTHON VALUE"""
        if isinstance(value, bool):
            return 'BOOL'
        elif isinstance(value, int):
            return 'INT64'
        elif isinstance(value, float):
            return 'FLOAT64'
        elif isinstance(value, datetime):
            return 'TIMESTAMP'
        elif isinstance(value, (list, tuple, set)):
            return 'ARRAY'
        else:
            return 'STRING'
    
    async def close(self) -> None:
        """CLOSE THE BIGQUERY CLIENT"""
        if self.client:
            await self.client.close()
            self.logger.info("BigQuery client closed")