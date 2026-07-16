"""Resolve immutable bundle resources separately from writable user data."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_DIR_NAME = "PenguinDash"
USER_DATA_OVERRIDE = "PENGUIN_USER_DATA_DIR"


def resource_root() -> Path:
    """Return the source root or PyInstaller bundle data root.

    PyInstaller sets module ``__file__`` inside its bundle. Mirroring assets,
    balance, and style.kv at the bundle root keeps this path identical in source
    and packaged runs without depending on the process working directory.
    """

    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def user_data_root() -> Path:
    override = os.environ.get(USER_DATA_OVERRIDE)
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_DIR_NAME


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    data: Path
    settings: Path
    logs: Path
    crash: Path
    telemetry: Path

    @classmethod
    def discover(cls) -> RuntimePaths:
        root = user_data_root()
        return cls(
            root=root,
            data=root / "data",
            settings=root / "settings",
            logs=root / "logs",
            crash=root / "crash",
            telemetry=root / "telemetry",
        )

    def ensure(self) -> RuntimePaths:
        for directory in (
            self.root,
            self.data,
            self.settings,
            self.logs,
            self.crash,
            self.telemetry,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self
