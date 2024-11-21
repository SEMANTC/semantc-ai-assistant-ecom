# ecommerce-ai-assistant/utils/logger.py
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger
from app.config.settings import Settings

settings = Settings()

def setup_logging() -> None:
    """CONFIGURE STRUCTURED LOGGING FOR THE APPLICATION"""
    
    # configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # create json formatter
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
            super().add_fields(log_record, record, message_dict)
            log_record['timestamp'] = datetime.utcnow().isoformat()
            log_record['level'] = record.levelname
            log_record['environment'] = settings.ENVIRONMENT

    # configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    ))
    root_logger.addHandler(console_handler)

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    GET A LOGGER INSTANCE WITH THE GIVEN NAME
    
    args:
        name (optional[str]): logger name, typically __name__
        
    returns:
        structlog.boundlogger: configured logger instance
    """
    return structlog.get_logger(name)

class LogContext:
    """CONTEXT MANAGER FOR ADDING TEMPORARY CONTEXT TO LOGS"""
    
    def __init__(self, **kwargs):
        self.temp_context = kwargs
        self.token = None
    
    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.temp_context)
        return self
    
    def __exit__(self, *args):
        structlog.contextvars.unbind_contextvars(self.token)

def log_execution_time(logger: structlog.BoundLogger):
    """
    DECORATOR TO LOG EXECUTION TIME OF FUNCTIONS
    
    args:
        logger (structlog.boundlogger): logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(
                    "function execution completed",
                    function=func.__name__,
                    execution_time=execution_time
                )
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(
                    "function execution failed",
                    function=func.__name__,
                    execution_time=execution_time,
                    error=str(e),
                    exc_info=True
                )
                raise
        return wrapper
    return decorator
