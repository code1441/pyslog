"""Core logging configuration and utilities for pyslog."""

from __future__ import annotations

from pyslog import logs
import structlog


def log_configs_as_table(logger: structlog.stdlib.BoundLogger, config_data: dict, **kwargs):
    keys = [str(k) for k in config_data.keys()]
    vals = [repr(v) for v in config_data.values()]

    k_w = max(len("KEY"), *(len(k) for k in keys))
    v_w = max(len("VALUE"), *(len(v) for v in vals))

    line = f"+-{'-' * k_w}-+-{'-' * v_w}-+"

    logger.debug("loaded model with config, config_data", **kwargs)
    logger.debug(line, **kwargs)
    for k, v in zip(keys, vals, strict=True):
        logger.debug(f"| {k.ljust(k_w)} | {v.ljust(v_w)} |", **kwargs)
    logger.debug(line, **kwargs)

if __name__ == "__main__":
    logger = logs.get_handler_logger("pyslog.tools")
    example_data = {"id": "abc", "name": "test-station", "expiry": "2026-09-30"}
    log_configs_as_table(logger, example_data, context_var=10)
    # RESULT:
    # """
    # 2026-01-13T11:06:16.786635Z [debug    ] loaded model with config, config_data [logs] context_var=10 handler=pyslog.tools
    # 2026-01-13T11:06:16.786836Z [debug    ] +--------+----------------+    [logs] context_var=10 handler=pyslog.tools
    # 2026-01-13T11:06:16.786951Z [debug    ] | id     | 'abc'          |    [logs] context_var=10 handler=pyslog.tools
    # 2026-01-13T11:06:16.787027Z [debug    ] | name   | 'test-station' |    [logs] context_var=10 handler=pyslog.tools
    # 2026-01-13T11:06:16.787090Z [debug    ] | expiry | '2026-09-30'   |    [logs] context_var=10 handler=pyslog.tools
    # 2026-01-13T11:06:16.787164Z [debug    ] +--------+----------------+    [logs] context_var=10 handler=pyslog.tools
    # """