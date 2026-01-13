"""Core logging configuration and utilities for pyslog."""

from __future__ import annotations

import logging
import os
import sys
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import structlog
from dotenv import load_dotenv


class LogLevel(str, Enum):
    """Supported log levels for structured logging."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogFormat(str, Enum):
    """Supported log output formats."""

    CONSOLE = "console"
    JSON = "json"


class LogOutput(str, Enum):
    """Supported log output destinations."""

    STDOUT = "stdout"
    FILE = "file"


@dataclass
class LoggingConfig:
    """Configuration for pyslog logging."""

    level: LogLevel = LogLevel.DEBUG
    format: LogFormat = LogFormat.CONSOLE
    output: LogOutput = LogOutput.STDOUT
    file_path: str = "app.log"
    include_location: bool = False
    logger_name: str = "logs"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> LoggingConfig:
        """
        Create configuration from environment variables.

        Args:
            env: Optional environment dictionary. If None, uses os.environ.

        Returns:
            LoggingConfig instance with values from environment.

        Raises:
            ValueError: If environment variables contain invalid values.
        """
        if env is None:
            env = dict(os.environ)

        level_str = env.get("LOGGING_LEVEL", "DEBUG").upper()
        try:
            level = LogLevel(level_str)
        except ValueError:
            valid_levels = ", ".join(e.value for e in LogLevel)
            raise ValueError(f"Invalid LOGGING_LEVEL '{level_str}'. Must be one of: {valid_levels}") from None

        format_str = env.get("LOGGING_FORMAT", "console").lower()
        try:
            log_format = LogFormat(format_str)
        except ValueError:
            valid_formats = ", ".join(e.value for e in LogFormat)
            raise ValueError(f"Invalid LOGGING_FORMAT '{format_str}'. Must be one of: {valid_formats}") from None

        output_str = env.get("LOGGING_OUTPUT", "stdout").lower()
        try:
            output = LogOutput(output_str)
        except ValueError:
            valid_outputs = ", ".join(e.value for e in LogOutput)
            raise ValueError(f"Invalid LOGGING_OUTPUT '{output_str}'. Must be one of: {valid_outputs}") from None

        file_path = env.get("LOGGING_FILE_PATH", "app.log")
        if not file_path or not isinstance(file_path, str):
            raise ValueError("LOGGING_FILE_PATH must be a non-empty string")
        if len(file_path) > 4096:
            raise ValueError(f"LOGGING_FILE_PATH is too long (max 4096 characters, got {len(file_path)})")

        include_location_str = env.get("LOGGING_INCLUDE_LOCATION", "false").lower()
        include_location = include_location_str in ("true", "1", "yes")

        logger_name = env.get("LOGGING_LOGGER_NAME", "logs")
        if not logger_name or not isinstance(logger_name, str):
            raise ValueError("LOGGING_LOGGER_NAME must be a non-empty string")

        return cls(
            level=level,
            format=log_format,
            output=output,
            file_path=file_path,
            include_location=include_location,
            logger_name=logger_name,
        )


class LoggerFactory:
    """Thread-safe factory for creating and managing loggers."""

    _lock = threading.Lock()
    _configured = False
    _config: LoggingConfig | None = None
    _default_logger: structlog.BoundLogger | None = None

    @classmethod
    def load_environment_variables(cls, env: dict[str, str] | None = None) -> None:
        """
        Load environment variables from .env files in priority order.

        Args:
            env: Optional environment dictionary to update. If None, updates os.environ.
        """
        if env is None:
            if os.path.exists(".env.shared"):
                load_dotenv(".env.shared", override=False)
            if os.path.exists(".env"):
                load_dotenv(".env", override=False)
            profile = os.getenv("PROFILE", "NONE")
            if profile != "NONE":
                envpath = f".env.{profile}"
                if os.path.exists(envpath):
                    load_dotenv(envpath, override=False)
        else:
            original_env = os.environ.copy()
            if os.path.exists(".env.shared"):
                load_dotenv(".env.shared", override=False)
                for key, value in os.environ.items():
                    if key not in env:
                        env[key] = value
            if os.path.exists(".env"):
                load_dotenv(".env", override=False)
                for key, value in os.environ.items():
                    if key not in env:
                        env[key] = value
            profile = env.get("PROFILE", original_env.get("PROFILE", "NONE"))
            if profile != "NONE":
                envpath = f".env.{profile}"
                if os.path.exists(envpath):
                    load_dotenv(envpath, override=False)
                    for key, value in os.environ.items():
                        if key not in env:
                            env[key] = value
            # We clear and restore os.environ so that loading of .env files by load_dotenv
            # does NOT leave any changes in the process-global environment.
            # This way, evaluation of .env files only affects the temporary env dict
            # passed in by the caller, not the Python process as a whole.
            # Lasting effect: Only the passed-in `env` dict is mutated, not os.environ.
            # The config is saved in the LoggerFactory instance's config field, so it is not affected by this.
            os.environ.clear()
            os.environ.update(original_env)

    @classmethod
    def configure(cls, config: LoggingConfig | None = None, env: dict[str, str] | None = None) -> None:
        """
        Configure structlog with the given configuration.

        Args:
            config: Optional LoggingConfig. If None, loads from environment.
            env: Optional environment dictionary. Used if config is None.

        Raises:
            ValueError: If configuration is invalid.
            RuntimeError: If file handler cannot be created.
        """
        with cls._lock:
            if config is None:
                if env is None:
                    cls.load_environment_variables()
                else:
                    cls.load_environment_variables(env)
                config = LoggingConfig.from_env(env)

            cls._config = config
            cls._configure_structlog(config)
            cls._configured = True

    @classmethod
    def _configure_structlog(cls, config: LoggingConfig) -> None:
        """Configure structlog processors and handlers."""
        log_level_map = {
            LogLevel.CRITICAL: logging.CRITICAL,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.INFO: logging.INFO,
            LogLevel.DEBUG: logging.DEBUG,
        }
        log_level = log_level_map[config.level]

        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        if config.include_location:
            shared_processors.insert(
                3,
                structlog.processors.CallsiteParameterAdder(
                    parameters=[
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.LINENO,
                        structlog.processors.CallsiteParameter.MODULE,
                    ]
                ),
            )

        if config.format == LogFormat.JSON:
            renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer()  # type: ignore[assignment]

        processors = shared_processors + [renderer]

        structlog.configure(
            processors=processors,  # type: ignore[arg-type]
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        stdlib_logger = logging.getLogger(config.logger_name)
        stdlib_logger.setLevel(log_level)

        if config.output == LogOutput.FILE:
            log_path = Path(config.file_path)
            if log_path.exists() and log_path.is_dir():
                raise ValueError(f"Log file path '{config.file_path}' is a directory, not a file")
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                if log_path.exists() and not log_path.is_file():
                    raise ValueError(f"Log file path '{config.file_path}' exists but is not a regular file")
                handler: logging.Handler = logging.FileHandler(config.file_path, encoding="utf-8")
            except (OSError, PermissionError) as e:
                raise RuntimeError(f"Failed to create log file handler for path '{config.file_path}': {e}") from e
        else:
            handler = logging.StreamHandler(stream=sys.stdout)

        stdlib_logger.handlers.clear()
        stdlib_logger.addHandler(handler)
        stdlib_logger.propagate = False

        cls._default_logger = structlog.get_logger(config.logger_name)  # type: ignore[assignment]

    @classmethod
    def get_default_logger(cls) -> structlog.BoundLogger:
        """
        Get the default configured logger.

        Returns:
            The default structlog logger instance.

        Raises:
            RuntimeError: If logger has not been configured.
        """
        if not cls._configured:
            cls.configure()
        if cls._default_logger is None:
            raise RuntimeError("Logger not properly configured")
        return cls._default_logger

    @classmethod
    def reset(cls) -> None:
        """Reset configuration. Useful for testing."""
        with cls._lock:
            if cls._config:
                stdlib_logger = logging.getLogger(cls._config.logger_name)
                stdlib_logger.handlers.clear()
            cls._configured = False
            cls._config = None
            cls._default_logger = None
            structlog.reset_defaults()

    @classmethod
    def get_config(cls) -> LoggingConfig | None:
        """Get current configuration."""
        return cls._config


LoggerFactory.load_environment_variables()
LoggerFactory.configure()


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Optional logger name. If None, returns the default logger.

    Returns:
        A configured structlog logger instance.

    Example:
        ```python
        from pyslog import get_logger

        logger = get_logger("my_module")
        logger.info("Application started", user_id=123, action="start")
        ```
    """
    if name:
        return structlog.get_logger(name)  # type: ignore[no-any-return]
    return LoggerFactory.get_default_logger()


def replace_stdlib_logger(logger_name: str) -> structlog.BoundLogger:
    """
    Replace a standard library logger with a structlog logger.

    This is useful for migrating existing code that uses standard logging
    to use structlog while maintaining the same logger name.

    Args:
        logger_name: Name of the logger to replace.

    Returns:
        A structlog logger bound to the specified name.

    Example:
        ```python
        # Old way:
        import logging
        logger = logging.getLogger("my_module")

        # New way:
        from pyslog import replace_stdlib_logger
        logger = replace_stdlib_logger("my_module")
        logger.info("Using structlog now", extra_data="value")
        ```
    """
    return structlog.get_logger(logger_name)  # type: ignore[no-any-return]


def get_handler_logger(handler_name: str) -> structlog.BoundLogger:
    """
    Get a logger with a specific handler name for distinguishing different log sources.

    Args:
        handler_name: Name to identify this handler/component.

    Returns:
        A structlog logger with the handler name in context.

    Example:
        ```python
        from pyslog import get_handler_logger

        api_logger = get_handler_logger("api")
        db_logger = get_handler_logger("database")

        api_logger.info("Request received", endpoint="/users")
        db_logger.info("Query executed", table="users", duration_ms=45)
        ```
    """
    config = LoggerFactory.get_config()
    logger_name = config.logger_name if config else "logs"
    return structlog.get_logger(logger_name).bind(handler=handler_name)  # type: ignore[no-any-return]
