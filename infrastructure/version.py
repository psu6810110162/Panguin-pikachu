"""Independent application, save, balance, resource, and protocol versions."""

import json
import platform
from pathlib import Path
from typing import Any

from core.schema import SCHEMA_VERSION
from infrastructure.database import SAVE_VERSION
from infrastructure.paths import resource_path
from infrastructure.resources import MANIFEST_SCHEMA_VERSION

APP_VERSION = "0.1.0"
BALANCE_VERSION = "v1"
PROTOCOL_VERSION = "1"


def load_build_info() -> dict[str, Any]:
    path: Path = resource_path("build_info.json")
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            payload: dict[str, Any] = json.load(handle)
        return payload
    return {
        "version": APP_VERSION,
        "git_sha": "source-tree",
        "build_date_utc": "not-packaged",
        "python": platform.python_version(),
        "run_record_schema": SCHEMA_VERSION,
        "save_version": SAVE_VERSION,
        "balance_version": BALANCE_VERSION,
        "resource_manifest_version": MANIFEST_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "feature_flags": {"classroom": False, "sync": False},
    }
