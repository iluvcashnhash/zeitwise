import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
import os

def setup_logging() -> None:
    """Setup logging configuration.
    
    Configures logging with a JSON formatter and both console and file handlers.
    Logs are written to `logs/zeitwise.log`.
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "simple",
                "level": "DEBUG",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "zeitwise.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": "INFO",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file"],
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "httpcore": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }
    
    # Apply the configuration
    logging.config.dictConfig(log_config)
    
    # Capture warnings from the warnings module
    logging.captureWarnings(True)
