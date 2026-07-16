"""Generate release metadata before invoking PyInstaller."""

import json
import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from core.schema import SCHEMA_VERSION
from infrastructure.atomic import atomic_write_json
from infrastructure.database import SAVE_VERSION
from infrastructure.resources import MANIFEST_SCHEMA_VERSION
from infrastructure.version import APP_VERSION, BALANCE_VERSION, PROTOCOL_VERSION

ROOT = Path(__file__).resolve().parent.parent


def package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not-installed"


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=5
    ).strip()


def main() -> None:
    payload = {
        "version": APP_VERSION,
        "git_sha": git_sha(),
        "build_date_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "kivy": package_version("Kivy"),
        "pyinstaller": package_version("pyinstaller"),
        "run_record_schema": SCHEMA_VERSION,
        "save_version": SAVE_VERSION,
        "balance_version": BALANCE_VERSION,
        "resource_manifest_version": MANIFEST_SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "feature_flags": {"classroom": False, "sync": False},
    }
    atomic_write_json(ROOT / "build_info.json", payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
