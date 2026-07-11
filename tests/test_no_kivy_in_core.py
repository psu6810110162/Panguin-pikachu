"""core/ ต้องไม่ import kivy — เพราะ server/ (ยังไม่มี) จะ import core/ ตรง ๆ
โดยไม่ต้องติดตั้ง Kivy ดู docs/adr/006-server-authoritative-scoring.md
"""

import re
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "core"
_KIVY_IMPORT_RE = re.compile(r"^\s*(import kivy\b|from kivy\b)", re.MULTILINE)

# core/audio.py needs the Kivy audio backend to load sound files — accepted exception,
# it is never imported by server/ (D9 only touches core/schema.py, events.py, state.py,
# scoring/, sync.py).
ALLOWED_KIVY_IMPORTS = {"audio.py"}


def test_core_modules_do_not_import_kivy():
    offenders = []
    for path in sorted(CORE_DIR.rglob("*.py")):
        if path.name in ALLOWED_KIVY_IMPORTS:
            continue
        if _KIVY_IMPORT_RE.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(CORE_DIR)))

    assert not offenders, f"core/ modules must not import kivy: {offenders}"
