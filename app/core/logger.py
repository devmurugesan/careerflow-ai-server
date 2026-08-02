import logging
import sys
from typing import Any, Dict
import structlog

SENSITIVE_KEYS = {
    "password", "hashed_password", "token", "access_token", "refresh_token",
    "secret", "secret_key", "api_key", "authorization", "raw_body"
}


def sanitize_sensitive_data(logger_instance: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Processor that redacts sensitive values from structured log outputs."""
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
    return event_dict


def setup_logging():
    """Configures structured JSON console logging with security sanitization."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        sanitize_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger()
