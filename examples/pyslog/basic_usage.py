"""
Example usage of pyslog structured logging package.

This script demonstrates various ways to use the pyslog logger:
1. Basic usage with default logger
2. Getting named loggers
3. Replacing standard library loggers
4. Using handler loggers to distinguish different components
5. Structured logging with context variables

Environment variables that can be set:
- LOGGING_LEVEL: CRITICAL, ERROR, WARNING, INFO, DEBUG (default: DEBUG)
- LOGGING_FORMAT: console or json (default: console)
- LOGGING_OUTPUT: stdout or file (default: stdout)
- LOGGING_FILE_PATH: path to log file when LOGGING_OUTPUT=file (default: app.log)
- LOGGING_INCLUDE_LOCATION: true/false to include filename, line number, module (default: false)
"""

import os

# Example 1: Basic usage with default logger
from pyslog import get_logger, get_handler_logger, replace_stdlib_logger

# Get the default logger
logger = get_logger()
logger.info("Application started", version="1.0.0", environment="development")

# Example 2: Using named loggers for different modules
database_logger = get_logger("database")
api_logger = get_logger("api")
auth_logger = get_logger("auth")

database_logger.info("Database connection established", host="localhost", port=5432)
api_logger.info("API request received", method="GET", path="/users", status_code=200)
auth_logger.warning("Failed login attempt", username="user123", ip="192.168.1.1")

# Example 3: Replacing standard library loggers
# Old way (standard library):
# import logging
# old_logger = logging.getLogger("legacy_module")
# old_logger.info("Old logging style")

# New way (structlog):
legacy_logger = replace_stdlib_logger("legacy_module")
legacy_logger.info("Migrated to structlog", feature="logging", status="success")

# Example 4: Using handler loggers to distinguish different components
# This is useful when you want to tag logs with a specific handler/component name
api_handler = get_handler_logger("api_handler")
db_handler = get_handler_logger("db_handler")
cache_handler = get_handler_logger("cache_handler")

api_handler.info("Processing request", request_id="req-123", endpoint="/api/v1/data")
db_handler.info("Executing query", query="SELECT * FROM users", duration_ms=45)
cache_handler.info("Cache miss", key="user:123", action="fetch_from_db")

# Example 5: Structured logging with context
logger.debug("User action", user_id=123, action="login", timestamp="2024-01-01T12:00:00")
logger.info("Order created", order_id=456, amount=99.99, currency="USD")
logger.warning("High memory usage", memory_mb=2048, threshold_mb=1024)
logger.error("Payment failed", order_id=456, error_code="INSUFFICIENT_FUNDS", retry_count=3)

# Example 6: Logging exceptions
try:
    result = 1 / 0
except ZeroDivisionError:
    logger.exception("Division by zero error", dividend=1, divisor=0)

# Example 7: Using context variables for request-scoped logging
import structlog

# Set context that will be included in all subsequent log entries
structlog.contextvars.clear_contextvars()
structlog.contextvars.bind_contextvars(request_id="req-789", user_id=456)

logger.info("Processing started")
logger.debug("Step 1 completed")
logger.debug("Step 2 completed")
logger.info("Processing finished")

# Clear context
structlog.contextvars.clear_contextvars()
logger.info("Context cleared", note="This log won't have request_id or user_id")

# Example 8: Different log levels
logger.debug("Debug message", detail="Very verbose information")
logger.info("Info message", detail="General information")
logger.warning("Warning message", detail="Something might be wrong")
logger.error("Error message", detail="Something went wrong")
logger.critical("Critical message", detail="System is in critical state")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Example usage of pyslog")
    print("=" * 80)
    print("\nCurrent configuration:")
    print(f"  LOGGING_LEVEL: {os.getenv('LOGGING_LEVEL', 'DEBUG (default)')}")
    print(f"  LOGGING_FORMAT: {os.getenv('LOGGING_FORMAT', 'console (default)')}")
    print(f"  LOGGING_OUTPUT: {os.getenv('LOGGING_OUTPUT', 'stdout (default)')}")
    print(f"  LOGGING_FILE_PATH: {os.getenv('LOGGING_FILE_PATH', 'app.log (default)')}")
    print(f"  LOGGING_INCLUDE_LOCATION: {os.getenv('LOGGING_INCLUDE_LOCATION', 'false (default)')}")
    print("\n" + "=" * 80 + "\n")

