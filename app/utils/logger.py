"""
Logging configuration for Viamigo application
"""

import logging
import sys
from typing import Optional

def setup_logging(level: Optional[str] = None) -> None:
    """Setup logging configuration"""
    
    # Get log level from config or parameter
    from app.config import settings
    log_level = level or settings.LOG_LEVEL
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    loggers = [
        "viamigo",
        "app",
        "uvicorn",
        "fastapi"
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Reduce noise from some libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
