"""Pytest tests for pyslog structlog configuration."""

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


def test_console_format():
    """Test console format output."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
        include_location=False,
    )
    LoggerFactory.configure(config)
    
    stdlib_logger = logging.getLogger(config.logger_name)
    stdlib_logger.handlers.clear()
    handler = logging.StreamHandler(stream=output)
    handler.setLevel(logging.DEBUG)
    stdlib_logger.addHandler(handler)
    stdlib_logger.setLevel(logging.DEBUG)

    logger = get_logger()
    logger.info("Console format test", test_id=1, format_type="console")
    logger.warning("This is a warning", severity="medium")
    logger.error("This is an error", error_code="TEST_001")
    
    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert "Console format test" in content
    assert "test_id" in content and "1" in content
    assert "format_type" in content and "console" in content


def test_json_format():
    """Test JSON format output."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.DEBUG,
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
    logger.debug("JSON format test", test_id=2, format_type="json")
    logger.info("This is info", message="test message")
    logger.error("This is an error", error_code="TEST_002")
    
    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert '"event": "JSON format test"' in content
    assert '"test_id": 2' in content
    assert '"level": "info"' in content


def test_file_output():
    """Test file output configuration."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as tmp_file:
        log_file = tmp_file.name

    try:
        config = LoggingConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON,
            output=LogOutput.FILE,
            file_path=log_file,
        )
        LoggerFactory.configure(config)

        import logging
        logs_logger = logging.getLogger(config.logger_name)
        assert len(logs_logger.handlers) > 0
        assert any(isinstance(h, logging.FileHandler) for h in logs_logger.handlers)

        file_handlers = [h for h in logs_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        assert file_handlers[0].baseFilename == os.path.abspath(log_file)

        logger = get_logger()
        logger.debug("File output test", test_id=3, output_type="file")
        logger.info("This should be in the file", message="test message")
        logger.warning("Warning in file", severity="low")

        for handler in logs_logger.handlers:
            handler.flush()
            handler.close()
            if hasattr(handler, 'stream') and handler.stream:
                handler.stream.flush()

        assert os.path.exists(log_file)
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
            assert "File output test" in content
            assert '"test_id": 3' in content
            assert "This should be in the file" in content
    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_location_inclusion():
    """Test location information inclusion."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
        include_location=True,
    )
    LoggerFactory.configure(config)
    
    stdlib_logger = logging.getLogger(config.logger_name)
    stdlib_logger.handlers.clear()
    handler = logging.StreamHandler(stream=output)
    handler.setLevel(logging.DEBUG)
    stdlib_logger.addHandler(handler)
    stdlib_logger.setLevel(logging.DEBUG)

    logger = get_logger()
    logger.info("Location test", test_id=4)
    
    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert "Location test" in content


def test_different_log_levels():
    """Test different log levels."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.WARNING,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)
    
    stdlib_logger = logging.getLogger(config.logger_name)
    stdlib_logger.handlers.clear()
    handler = logging.StreamHandler(stream=output)
    handler.setLevel(logging.DEBUG)
    stdlib_logger.addHandler(handler)
    stdlib_logger.setLevel(logging.WARNING)

    logger = get_logger()
    logger.debug("This should not appear")
    logger.info("This should not appear")
    logger.warning("This should appear")
    logger.error("This should appear")

    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert "This should not appear" not in content
    assert "This should appear" in content


def test_handler_loggers():
    """Test handler loggers."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
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

    api_logger.info("API request", endpoint="/users")
    db_logger.info("Database query", table="users")

    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert "API request" in content
    assert "Database query" in content


def test_replace_stdlib_logger():
    """Test replacing standard library logger."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)

    logger = replace_stdlib_logger("test_module")
    logger.info("Using structlog", extra="data")


def test_context_variables():
    """Test context variables."""
    output = io.StringIO()
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
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
    structlog.contextvars.bind_contextvars(request_id="req-123", user_id=456)
    logger.info("Processing started")
    logger.info("Step completed")
    structlog.contextvars.clear_contextvars()
    logger.info("Request finished (context cleared)")

    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert "Processing started" in content
    assert "Step completed" in content


def test_get_logger_with_name():
    """Test getting logger with specific name."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)

    named_logger = get_logger("custom_name")
    assert named_logger is not None
    named_logger.info("Test message", test="value")


def test_get_logger_default():
    """Test getting default logger."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)

    default_logger = get_logger()
    assert default_logger is not None
    default_logger.info("Default logger test")


def test_handler_logger_binding():
    """Test that handler logger properly binds handler name."""
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

    handler_logger = get_handler_logger("test_handler")
    handler_logger.info("Handler test", data="value")

    handler.flush()
    stdlib_logger.removeHandler(handler)
    handler.close()
    content = output.getvalue()
    assert '"handler": "test_handler"' in content


def test_config_from_env_valid():
    """Test creating config from valid environment variables."""
    env = {
        "LOGGING_LEVEL": "WARNING",
        "LOGGING_FORMAT": "json",
        "LOGGING_OUTPUT": "file",
        "LOGGING_FILE_PATH": "/tmp/test.log",
        "LOGGING_INCLUDE_LOCATION": "true",
        "LOGGING_LOGGER_NAME": "custom_logger",
    }
    config = LoggingConfig.from_env(env)
    assert config.level == LogLevel.WARNING
    assert config.format == LogFormat.JSON
    assert config.output == LogOutput.FILE
    assert config.file_path == "/tmp/test.log"
    assert config.include_location is True
    assert config.logger_name == "custom_logger"


def test_config_from_env_invalid_level():
    """Test that invalid log level raises ValueError."""
    env = {"LOGGING_LEVEL": "INVALID"}
    with pytest.raises(ValueError, match="Invalid LOGGING_LEVEL"):
        LoggingConfig.from_env(env)


def test_config_from_env_invalid_format():
    """Test that invalid log format raises ValueError."""
    env = {"LOGGING_FORMAT": "invalid"}
    with pytest.raises(ValueError, match="Invalid LOGGING_FORMAT"):
        LoggingConfig.from_env(env)


def test_config_from_env_invalid_output():
    """Test that invalid log output raises ValueError."""
    env = {"LOGGING_OUTPUT": "invalid"}
    with pytest.raises(ValueError, match="Invalid LOGGING_OUTPUT"):
        LoggingConfig.from_env(env)


def test_config_from_env_empty_file_path():
    """Test that empty file path raises ValueError."""
    env = {"LOGGING_FILE_PATH": ""}
    with pytest.raises(ValueError, match="must be a non-empty string"):
        LoggingConfig.from_env(env)


def test_file_path_is_directory():
    """Test that file path being a directory raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = LoggingConfig(
            level=LogLevel.INFO,
            format=LogFormat.CONSOLE,
            output=LogOutput.FILE,
            file_path=tmpdir,
        )
        with pytest.raises(ValueError, match="is a directory"):
            LoggerFactory.configure(config)


def test_file_path_permission_error(monkeypatch):
    """Test handling of permission errors when creating log file."""
    def mock_mkdir(*args, **kwargs):
        raise PermissionError("Permission denied")

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        log_file = tmp_file.name
        os.unlink(log_file)

    try:
        config = LoggingConfig(
            level=LogLevel.INFO,
            format=LogFormat.CONSOLE,
            output=LogOutput.FILE,
            file_path=log_file,
        )
        monkeypatch.setattr(Path, "mkdir", mock_mkdir)
        with pytest.raises(RuntimeError, match="Failed to create log file handler"):
            LoggerFactory.configure(config)
    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_custom_logger_name():
    """Test using custom logger name."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
        logger_name="custom_app",
    )
    LoggerFactory.configure(config)

    import logging
    stdlib_logger = logging.getLogger("custom_app")
    assert stdlib_logger.name == "custom_app"

    logger = get_logger()
    logger.info("Test with custom name")


def test_thread_safety():
    """Test that logger factory is thread-safe."""
    import threading

    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )

    errors = []

    def configure_logger():
        try:
            LoggerFactory.configure(config)
            logger = get_logger(f"thread_{threading.current_thread().ident}")
            logger.info("Thread test")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=configure_logger) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(errors) == 0, f"Thread safety issues: {errors}"


def test_reset_functionality():
    """Test that reset properly clears configuration."""
    config = LoggingConfig(
        level=LogLevel.INFO,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)
    assert LoggerFactory.get_config() is not None
    assert LoggerFactory._configured is True

    LoggerFactory.reset()
    assert LoggerFactory.get_config() is None
    assert LoggerFactory._configured is False
    assert LoggerFactory._default_logger is None


def test_default_configuration():
    """Test that default configuration works without explicit setup."""
    LoggerFactory.reset()
    LoggerFactory.configure()

    logger = get_logger()
    assert logger is not None
    logger.info("Default config test")


def test_load_environment_variables_with_dict():
    """Test loading environment variables into provided dictionary."""
    test_env = {"EXISTING_VAR": "existing_value"}
    LoggerFactory.load_environment_variables(test_env)
    
    assert "EXISTING_VAR" in test_env
    assert test_env["EXISTING_VAR"] == "existing_value"


def test_file_path_too_long():
    """Test that very long file paths are rejected."""
    long_path = "a" * 5000
    env = {"LOGGING_FILE_PATH": long_path}
    with pytest.raises(ValueError, match="too long"):
        LoggingConfig.from_env(env)
