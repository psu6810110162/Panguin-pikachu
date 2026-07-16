"""Structured, rotating local logs for console and windowed releases."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from infrastructure.paths import RuntimePaths

LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUPS = 3


def setup_logger(name: str = "PenguinDash") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(module)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def configure_file_logging(target: logging.Logger | None = None) -> logging.Logger:
    """Attach local rotating files once the application runtime has started."""

    target = target or logger
    if any(isinstance(handler, RotatingFileHandler) for handler in target.handlers):
        return target
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(module)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    paths = RuntimePaths.discover().ensure()
    runtime = RotatingFileHandler(
        paths.logs / "runtime.log",
        maxBytes=LOG_BYTES,
        backupCount=LOG_BACKUPS,
        encoding="utf-8",
    )
    runtime.setLevel(logging.DEBUG)
    runtime.setFormatter(formatter)
    target.addHandler(runtime)

    errors = RotatingFileHandler(
        paths.logs / "error.log",
        maxBytes=LOG_BYTES,
        backupCount=LOG_BACKUPS,
        encoding="utf-8",
    )
    errors.setLevel(logging.WARNING)
    errors.setFormatter(formatter)
    target.addHandler(errors)
    return target


logger = setup_logger()
