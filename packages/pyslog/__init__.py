"""
Pyslog - A structlog-based logging package.

This package provides a configured structlog setup that can be easily used
from other projects. It supports configuration via environment variables.

Environment Variables:
    LOGGING_LEVEL: Log level (CRITICAL, ERROR, WARNING, INFO, DEBUG). Default: DEBUG
    LOGGING_FORMAT: Output format ("console" or "json"). Default: console
    LOGGING_OUTPUT: Output destination ("stdout" or "file"). Default: stdout
    LOGGING_FILE_PATH: Path to log file when LOGGING_OUTPUT=file. Default: app.log
    LOGGING_INCLUDE_LOCATION: Include filename, line number, and module (true/false). Default: false
    LOGGING_LOGGER_NAME: Name of the underlying Python logger. Default: logs

Usage Examples:

1. Basic usage with default logger:
    ```python
    from pyslog import get_logger

    logger = get_logger()
    logger.info("Application started", version="1.0.0")
    ```

2. Using named loggers for different modules:
    ```python
    from pyslog import get_logger

    db_logger = get_logger("database")
    api_logger = get_logger("api")

    db_logger.info("Connection established", host="localhost")
    api_logger.info("Request received", endpoint="/users")
    ```

3. Replacing standard library loggers:
    ```python
    # Old way (standard library):
    import logging
    logger = logging.getLogger("my_module")
    logger.info("Old logging")

    # New way (structlog):
    from pyslog import replace_stdlib_logger
    logger = replace_stdlib_logger("my_module")
    logger.info("Using structlog", extra="data")
    ```

4. Using handler loggers to distinguish components:
    ```python
    from pyslog import get_handler_logger

    api_handler = get_handler_logger("api")
    db_handler = get_handler_logger("database")
    cache_handler = get_handler_logger("cache")

    api_handler.info("Request", endpoint="/users")
    db_handler.info("Query", table="users")
    cache_handler.info("Cache miss", key="user:123")
    ```

5. Using context variables for request-scoped logging:
    ```python
    from pyslog import get_logger
    import structlog

    logger = get_logger()
    structlog.contextvars.bind_contextvars(request_id="req-123", user_id=456)
    logger.info("Processing started")  # Will include request_id and user_id
    logger.info("Step completed")      # Will also include request_id and user_id
    structlog.contextvars.clear_contextvars()
    logger.info("Finished")           # No longer includes request_id or user_id
    ```

6. Migrating existing code:
    ```python
    # Before (standard logging):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Message: %s", "value")

    # After (structlog):
    from pyslog import replace_stdlib_logger
    logger = replace_stdlib_logger(__name__)
    logger.info("Message", value="value")  # Structured data instead of string formatting
    ```
See example_usage.py for more comprehensive examples.
"""

from .logs import (
    LogFormat,
    LoggerFactory,
    LoggingConfig,
    LogLevel,
    LogOutput,
    get_handler_logger,
    get_logger,
    replace_stdlib_logger,
)

__version__ = "0.0.1"
__all__ = [
    "get_logger",
    "get_handler_logger",
    "replace_stdlib_logger",
    "LoggingConfig",
    "LogLevel",
    "LogFormat",
    "LogOutput",
    "LoggerFactory",
]
