# Pyslog - Structured Logging Package

A structlog-based logging package that provides a pre-configured structured logging setup for easy use across projects. All configuration is done via environment variables, making it simple to adjust logging behavior without code changes.

## Overview

`pyslog` is a structured logging solution built on top of [structlog](https://www.structlog.org/), designed to make logging easier and more powerful in Python applications. It's particularly well-suited for ML pipelines and production applications where structured, searchable logs are essential.

## Features

- **Structured Logging**: Built on structlog for rich, structured log output
- **Environment-Based Configuration**: Configure via environment variables
- **Multiple Output Formats**: Console (human-readable) or JSON (machine-readable)
- **Flexible Output Destinations**: Log to stdout or file
- **Optional Location Information**: Include filename, line number, and module name
- **Easy Migration**: Simple functions to replace standard library loggers
- **Handler Support**: Distinguish logs from different components
- **Context Variables**: Add request-scoped context to all logs

## Installation

Install from GitHub:

```bash
pip install git+https://github.com/code1441/pyslog.git
```

Or using `uv`:

```bash
uv pip install git+https://github.com/code1441/pyslog.git
```

Or add to your project with `uv`:

```bash
uv add git+https://github.com/code1441/pyslog.git
```

## Configuration

All configuration is done via environment variables. Invalid values will raise `ValueError` with clear error messages.

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `LOGGING_LEVEL` | Log level | `DEBUG` | `CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG` |
| `LOGGING_FORMAT` | Output format | `console` | `console`, `json` |
| `LOGGING_OUTPUT` | Output destination | `stdout` | `stdout`, `file` |
| `LOGGING_FILE_PATH` | Log file path (when `LOGGING_OUTPUT=file`) | `app.log` | Any valid file path |
| `LOGGING_INCLUDE_LOCATION` | Include filename, line number, and module | `false` | `true`, `false`, `1`, `0`, `yes`, `no` |
| `LOGGING_LOGGER_NAME` | Name of the underlying logger | `logs` | Any valid logger name string |

### Profile-Based Configuration

The package supports profile-based configuration:
- `.env.shared` - Shared across all profiles
- `.env` - Default profile
- `.env.{PROFILE}` - Profile-specific (e.g., `.env.development`, `.env.production`)

Set the `PROFILE` environment variable to use profile-specific configuration:
```bash
export PROFILE=production
```

## Usage

### 1. Basic Usage with Default Logger

```python
from pyslog import get_logger

logger = get_logger()
logger.info("Application started", version="1.0.0")
```

### 2. Using Named Loggers for Different Modules

Create separate loggers for different parts of your application:

```python
from pyslog import get_logger

db_logger = get_logger("database")
api_logger = get_logger("api")

db_logger.info("Connection established", host="localhost")
api_logger.info("Request received", endpoint="/users")
```

### 3. Replacing Standard Library Loggers

Migrate existing code from Python's standard `logging` module:

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

### 4. Using Handler Loggers to Distinguish Components

Use handler loggers to tag logs with component names for easier filtering and analysis:

```python
from pyslog import get_handler_logger

api_handler = get_handler_logger("api")
db_handler = get_handler_logger("database")
cache_handler = get_handler_logger("cache")

api_handler.info("Request", endpoint="/users")
db_handler.info("Query", table="users")
cache_handler.info("Cache miss", key="user:123")
```

### 5. Using Context Variables for Request-Scoped Logging

Add context variables that are automatically included in all subsequent log entries:

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

### 6. Migrating Existing Code

Convert from string formatting to structured data:

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

## Examples

For comprehensive examples, see:
- [`examples/pyslog/basic_usage.py`](examples/pyslog/basic_usage.py) - Basic usage examples
- [`tests/test_logs_pytest.py`](tests/test_logs_pytest.py) - Test examples showing various configurations

## Advanced Configuration

For programmatic configuration or testing, you can use the `LoggingConfig` and `LoggerFactory` classes:

```python
from pyslog import LoggingConfig, LogLevel, LogFormat, LogOutput, LoggerFactory

# Create custom configuration
config = LoggingConfig(
    level=LogLevel.INFO,
    format=LogFormat.JSON,
    output=LogOutput.FILE,
    file_path="/var/log/app.log",
    include_location=True,
    logger_name="my_app",
)

# Configure the logger
LoggerFactory.configure(config)

# Use the logger
from pyslog import get_logger
logger = get_logger()
logger.info("Application started")
```

### Testing Support

The `LoggerFactory.reset()` method allows you to reset configuration between tests:

```python
from pyslog import LoggerFactory, LoggingConfig, LogLevel, LogFormat, LogOutput

def test_my_feature():
    # Reset any previous configuration
    LoggerFactory.reset()
    
    # Configure for test
    config = LoggingConfig(
        level=LogLevel.DEBUG,
        format=LogFormat.CONSOLE,
        output=LogOutput.STDOUT,
    )
    LoggerFactory.configure(config)
    
    # Test your code
    from pyslog import get_logger
    logger = get_logger()
    logger.info("Test message")
    
    # Cleanup
    LoggerFactory.reset()
```

## API Reference

### `get_logger(name: Optional[str] = None) -> structlog.BoundLogger`

Get a structlog logger instance.

- **Parameters:**
  - `name` (optional): Logger name. If `None`, returns the default logger.
- **Returns:** A configured structlog logger instance.

### `replace_stdlib_logger(logger_name: str) -> structlog.BoundLogger`

Replace a standard library logger with a structlog logger. Useful for migrating existing code.

- **Parameters:**
  - `logger_name`: Name of the logger to replace.
- **Returns:** A structlog logger bound to the specified name.

### `get_handler_logger(handler_name: str) -> structlog.BoundLogger`

Get a logger with a specific handler name for distinguishing different log sources.

- **Parameters:**
  - `handler_name`: Name to identify this handler/component.
- **Returns:** A structlog logger with the handler name in context.

### `LoggingConfig`

Configuration dataclass for programmatic logger setup.

- **Attributes:**
  - `level`: LogLevel enum value
  - `format`: LogFormat enum value (CONSOLE or JSON)
  - `output`: LogOutput enum value (STDOUT or FILE)
  - `file_path`: Path to log file (when output is FILE)
  - `include_location`: Whether to include filename, line number, module
  - `logger_name`: Name of the underlying Python logger

- **Class Methods:**
  - `from_env(env: Optional[dict[str, str]] = None) -> LoggingConfig`: Create config from environment variables with validation

### `LoggerFactory`

Thread-safe factory for managing logger configuration.

- **Class Methods:**
  - `configure(config: Optional[LoggingConfig] = None, env: Optional[dict[str, str]] = None) -> None`: Configure the logger
  - `reset() -> None`: Reset configuration (useful for testing)
  - `get_config() -> Optional[LoggingConfig]`: Get current configuration
  - `get_default_logger() -> structlog.BoundLogger`: Get the default logger instance

## Output Formats

### Console Format (Human-Readable)

When `LOGGING_FORMAT=console`, logs are displayed in a human-readable format:

```
2025-12-31T12:00:00.000000Z [info     ] Application started [logs] version=1.0.0 handler=api
```

### JSON Format (Machine-Readable)

When `LOGGING_FORMAT=json`, logs are displayed as JSON:

```json
{"event": "Application started", "level": "info", "logger": "logs", "version": "1.0.0", "handler": "api", "timestamp": "2025-12-31T12:00:00.000000Z"}
```

## Testing

Run tests with:

```bash
uv run pytest tests/ -v
```

Or run specific test files:

```bash
uv run pytest tests/test_logs_pytest.py -v
uv run pytest tests/test_integration.py -v
```

Or with coverage:

```bash
uv run pytest tests/ \
  --cov=packages/pyslog \
  --cov-report=term-missing
```

## Type Checking

Run type checking with mypy:

```bash
uv run mypy packages/pyslog
```

Or check a specific file:

```bash
uv run mypy packages/pyslog/logs.py
```

Mypy configuration is defined in `pyproject.toml` under `[tool.mypy]`.

## Package Location

The package is located at: [`packages/pyslog/`](packages/pyslog/)
