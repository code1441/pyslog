"""Core logging configuration and utilities for pyslog."""

from __future__ import annotations

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
