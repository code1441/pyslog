"""Integration tests for pyslog in realistic usage scenarios."""

import io
import logging
import os
import sys
import tempfile
from pathlib import Path

import pytest
import structlog

from pyslog import LoggerFactory, LoggingConfig, LogFormat, LogLevel, LogOutput
from pyslog import get_handler_logger, get_logger, replace_stdlib_logger


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset logger configuration before and after each test."""
    LoggerFactory.reset()
    yield
    LoggerFactory.reset()


def test_real_world_api_logging_scenario():
    """Test realistic API logging scenario with multiple components."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.JSON,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)
    
    stdlib_logger = logging.getLogger(config.logger_name)
    stdlib_logger.handlers.clear()
    handler = logging.StreamHandler(stream=output)
    handler.setLevel(logging.DEBUG)
    stdlib_logger.addHandler(handler)
    stdlib_logger.setLevel(logging.DEBUG)

    api_logger = get_handler_logger("api")
    db_logger = get_handler_logger("database")
    cache_logger = get_handler_logger("cache")

    structlog.contextvars.bind_contextvars(request_id="req-12345", user_id=789)
    api_logger.info("Request received", method="GET", path="/api/users", ip="192.168.1.1")
    db_logger.info("Query executed", query="SELECT * FROM users", duration_ms=45)
    cache_logger.info("Cache miss", key="user:789", action="fetch_from_db")
    api_logger.info("Response sent", status_code=200, duration_ms=67)
    structlog.contextvars.clear_contextvars()

    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert '"request_id": "req-12345"' in content
    assert '"handler": "api"' in content
    assert '"handler": "database"' in content
    assert '"handler": "cache"' in content


def test_migration_from_stdlib_logging():
    """Test migration scenario from standard library logging."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)

    old_logger = replace_stdlib_logger("legacy_module")
    old_logger.info("Migrated message", module="legacy", version="2.0")

    new_logger = get_logger("new_module")
    new_logger.info("New module message", module="new", version="2.0")

    assert old_logger is not None
    assert new_logger is not None


def test_production_configuration_with_file_logging():
    """Test production-like configuration with file logging."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as tmp_file:
        log_file = tmp_file.name

    try:
        config = LoggingConfig(
            level=LogLevel.WARNING,
            format=LogFormat.JSON,
            output=LogOutput.FILE,
            file_path=log_file,
            include_location=True,
            logger_name="production_app",
        )
        LoggerFactory.configure(config)

        logger = get_logger()
        logger.warning("High memory usage", memory_mb=2048, threshold_mb=1024)
        logger.error("Database connection failed", host="db.example.com", port=5432)
        logger.critical("System shutdown initiated", reason="maintenance")

        import logging
        stdlib_logger = logging.getLogger("production_app")
        for handler in stdlib_logger.handlers:
            handler.flush()
            handler.close()

        assert os.path.exists(log_file)
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
            assert '"level": "warning"' in content
            assert '"level": "error"' in content
            assert '"level": "critical"' in content
            assert "High memory usage" in content
            assert "Database connection failed" in content
    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_development_configuration():
    """Test development configuration with verbose console output."""
    config = LoggingConfig(
        level=LogLevel.DEBUG,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
        include_location=True,
    )
    LoggerFactory.configure(config)

    logger = get_logger("dev")
    logger.debug("Debug information", variable="value", step=1)
    logger.info("Info message", action="processing")
    logger.warning("Warning message", issue="minor")

    assert logger is not None


def test_multiple_loggers_same_configuration():
    """Test multiple loggers using the same configuration."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)

    loggers = {
        "auth": get_logger("auth"),
        "api": get_logger("api"),
        "database": get_logger("database"),
        "cache": get_logger("cache"),
    }

    for name, logger in loggers.items():
        assert logger is not None
        logger.info(f"Initialized {name} module", module=name)


def test_configuration_reload_scenario():
    """Test reloading configuration (e.g., for hot-reload scenarios)."""
    config1 = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config1)
    logger1 = get_logger()
    logger1.info("Before reload")

    config2 = LoggingConfig(
        level=LogLevel.DEBUG,
        format=LogFormat.JSON,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config2)
    logger2 = get_logger()
    logger2.debug("After reload")

    assert LoggerFactory.get_config() == config2


def test_error_logging_with_exception():
    """Test logging exceptions in realistic error scenarios."""
    config = LoggingConfig(
        level=LogLevel.ERROR,
        format=LogFormat.JSON,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)

    logger = get_logger("error_handler")

    try:
        result = 1 / 0
    except ZeroDivisionError:
        logger.exception("Division error", dividend=1, divisor=0, operation="divide")

    try:
        data = {"key": "value"}
        value = data["missing"]
    except KeyError:
        logger.exception("Missing key", key="missing", available_keys=list(data.keys()))

    assert logger is not None


def test_context_variables_in_request_flow():
    """Test context variables in a realistic request flow."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.JSON,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)
    
    stdlib_logger = logging.getLogger(config.logger_name)
    stdlib_logger.handlers.clear()
    handler = logging.StreamHandler(stream=output)
    handler.setLevel(logging.DEBUG)
    stdlib_logger.addHandler(handler)
    stdlib_logger.setLevel(logging.DEBUG)

    logger = get_logger()

    def process_request(request_id: str, user_id: int):
        structlog.contextvars.bind_contextvars(request_id=request_id, user_id=user_id)
        logger.info("Request started")
        logger.info("Processing step 1")
        logger.info("Processing step 2")
        logger.info("Request completed")
        structlog.contextvars.clear_contextvars()

    process_request("req-001", 123)
    process_request("req-002", 456)

    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert '"request_id": "req-001"' in content
    assert '"user_id": 123' in content
    assert '"request_id": "req-002"' in content
    assert '"user_id": 456' in content

