"""Write sanitized crash reports without exposing player identity or choices."""

from __future__ import annotations

import platform
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.schema import RunRecord
from infrastructure.atomic import atomic_write_json
from infrastructure.paths import RuntimePaths


def _sanitized_run(record: RunRecord | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "run_id": record.run_id,
        "schema_version": record.schema_version,
        "balance_version": record.balance_version,
        "state": record.state.name,
        "event_count": len(record.events),
        "event_types": [type(event).__name__ for event in record.events],
        "result": record.result.to_dict() if record.result else None,
    }


def write_crash_report(
    error: BaseException,
    *,
    run_record: RunRecord | None = None,
    view_state: dict[str, Any] | None = None,
    build_info: dict[str, Any] | None = None,
) -> Path:
    now = datetime.now(UTC)
    target = RuntimePaths.discover().ensure().crash / now.strftime("crash-%Y%m%dT%H%M%SZ.json")
    payload = {
        "created_at": now.isoformat(),
        "exception": {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": "".join(traceback.format_exception(error)),
        },
        "run": _sanitized_run(run_record),
        "view_state": view_state,
        "build": build_info or {},
        "runtime": {
            "python": platform.python_version(),
            "os": platform.platform(),
        },
    }
    atomic_write_json(target, payload)
    return target
