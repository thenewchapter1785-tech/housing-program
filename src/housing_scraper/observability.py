import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Structured JSON logger for observability."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s %(extra_fields)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(
            logging.getLevelName(os.getenv("LOG_LEVEL", "INFO"))
        )

    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, extra={"extra_fields": json.dumps(kwargs)})

    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message, extra={"extra_fields": json.dumps(kwargs)})

    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(message, extra={"extra_fields": json.dumps(kwargs)})

    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, extra={"extra_fields": json.dumps(kwargs)})
