import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional
from fastapi import Request
from pythonjsonlogger import jsonlogger
from ..config.settings import settings

class RequestContextFilter(logging.Filter):
    """Add FastAPI request context to logs"""
    def filter(self, record: logging.LogRecord) -> bool:
        from fastapi import Request
        request: Optional[Request] = getattr(record, 'request', None)
        if request:
            record.request_id = request.state.request_id if hasattr(request.state, 'request_id') else None
            record.path = request.url.path
            record.method = request.method
        return True

def get_logger(name: str = "bbyor") -> logging.Logger:
    """Get a configured logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)  # Set from config (e.g., "INFO", "DEBUG")

    # Prevent duplicate handlers in reload scenarios
    if logger.handlers:
        return logger

    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s %(path)s %(method)s %(request_id)s',
        rename_fields={
            'asctime': 'timestamp',
            'levelname': 'level',
            'name': 'service'
        },
        timestamp=True
    )

    # Console handler (structured JSON)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())

    # File handler (rotating logs)
    if settings.LOG_FILE:
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        logger.addHandler(file_handler)

    logger.addHandler(console_handler)
    logger.propagate = False  # Prevent double-logging
    return logger

# FastAPI middleware to capture request context
async def log_request_middleware(request: Request, call_next):
    logger = get_logger("api.request")
    request.state.request_id = request.headers.get('X-Request-ID', 'none')
    
    logger.info(
        "Request started",
        extra={
            "path": request.url.path,
            "method": request.method,
            "ip": request.client.host if request.client else None
        }
    )
    
    response = await call_next(request)
    
    logger.info(
        "Request completed",
        extra={
            "status_code": response.status_code,
            "duration": response.headers.get('X-Response-Time')
        }
    )
    return response