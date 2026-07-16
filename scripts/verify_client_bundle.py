"""Reject development/server material from a built client directory."""

from __future__ import annotations

import argparse
from pathlib import Path

FORBIDDEN_NAMES = {
    ".env",
    "docker-compose.yml",
    "dockerfile",
    "game.db",
    "instance",
    "server",
}
FORBIDDEN_TEXT = (
    "dev-secret-change-me",
    "/Users/",
    "\\Users\\",
)
TEXT_SUFFIXES = {".json", ".md", ".txt", ".kv", ".py", ".toml", ".yaml", ".yml"}


def verify_bundle(root: Path) -> list[str]:
    failures: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part.casefold() in FORBIDDEN_NAMES for part in relative.parts):
            failures.append(f"forbidden client path: {relative}")
        if path.is_file() and path.suffix.casefold() in TEXT_SUFFIXES:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for marker in FORBIDDEN_TEXT:
                if marker in content:
                    failures.append(f"forbidden text {marker!r} in {relative}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    failures = verify_bundle(args.bundle)
    if failures:
        print("\n".join(failures))
        return 1
    print(f"client bundle security check passed: {args.bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
