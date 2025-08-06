"""
Logging configuration for DocuVerse Worker
"""

import logging
import sys
from typing import Any, Optional

from celery.signals import setup_logging


@setup_logging.connect  # type: ignore[misc]
def configure_logging(sender: Optional[Any] = None, **kwargs: Any) -> logging.Logger:
    """
    Configure Celery logging with proper format and handlers
    """
    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler only (no file logging to prevent container size issues)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific logger levels
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("celery.task").setLevel(logging.INFO)
    logging.getLogger("celery.worker").setLevel(logging.INFO)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    return root_logger
