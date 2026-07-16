"""Local-only, non-identifying operational telemetry."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Any

from infrastructure.paths import RuntimePaths

ALLOWED_FIELDS = {
    "build_version",
    "play_duration_s",
    "terminal_reason",
    "average_fps",
    "p95_fps",
    "crash_count",
    "save_recovery_count",
}


class TelemetryRecorder:
    def __init__(self) -> None:
        self._logger = logging.getLogger("PenguinDash.telemetry")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        if not self._logger.handlers:
            path = RuntimePaths.discover().ensure().telemetry / "metrics.jsonl"
            handler = RotatingFileHandler(
                path,
                maxBytes=1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)

    def record(self, **fields: Any) -> None:
        unknown = set(fields) - ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"telemetry fields are not allowed: {sorted(unknown)}")
        self._logger.info(json.dumps(fields, sort_keys=True, separators=(",", ":")))
