"""Font/icon contract: Kenney Future is ASCII-only chrome; assets must exist.

Root cause of the "square glyphs" bug report: Kivy renders one font per
Label with no per-glyph fallback. ``Kenney Future.ttf`` is Latin-only, so any
Thai text or emoji/symbol handed to a Label using it renders as tofu boxes
(e.g. the How to Play title, "วิธีเล่น Penguin Dash", used to be assigned
``font_name=KENNEY_FONT``). This file pins two things so the bug class can't
silently come back:

1. The fonts and icon images referenced by name below actually exist on disk
   (a missing font/image is the same visible symptom — square boxes / blank
   icon — as a font/glyph mismatch, so both are worth guarding).
2. A static AST scan across ``screens/``, ``ui/`` and ``game/`` source: any
   Kivy widget constructor call that sets ``font_name=".../Kenney Future.ttf"``
   and a literal ``text=`` string in the *same call* must be ASCII-only. This
   is a best-effort static check (it cannot see text assigned dynamically
   after construction, e.g. ``label.text = f"..."``), which is why the
   individual dynamic offenders found during the audit were fixed by hand
   instead of relying on this test to catch them.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("screens", "ui", "game")
KENNEY_MARKER = "Kenney Future.ttf"

# Thai script + common arrow/symbol/emoji blocks that Kenney Future does not
# carry glyphs for.
_FORBIDDEN_RANGES = (
    (0x0E00, 0x0E7F),  # Thai
    (0x2190, 0x21FF),  # Arrows
    (0x2600, 0x27BF),  # Misc symbols & dingbats
    (0x1F300, 0x1FAFF),  # Misc emoji blocks
)

REQUIRED_ASSETS = (
    "assets/Component_UI/Font/Kenney Future.ttf",
    "assets/Component_UI/Font/NotoSansThai-Regular.ttf",
    "assets/Gem/Coin_Gems/spr_coin_strip4.png",
    "assets/Component_UI/history/trophy_normal.png",
    "assets/Component_UI/Vector/arrow_left_normal.png",
    "assets/Component_UI/Vector/arrow_right_normal.png",
    "assets/Component_UI/Stop/pause_on.png",
)


def _is_forbidden_char(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _FORBIDDEN_RANGES)


def _iter_py_files():
    for directory in SCAN_DIRS:
        yield from (REPO_ROOT / directory).rglob("*.py")


def _string_literal(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def test_required_font_and_icon_assets_exist_on_disk():
    missing = [asset for asset in REQUIRED_ASSETS if not (REPO_ROOT / asset).is_file()]
    assert not missing, f"Missing font/icon assets referenced by UI code: {missing}"


def test_kenney_font_labels_never_carry_thai_or_symbol_literal_text():
    offenders = []
    for path in _iter_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            font_name = _string_literal(kwargs.get("font_name"))
            if not font_name or KENNEY_MARKER not in font_name:
                continue
            text_value = _string_literal(kwargs.get("text"))
            if text_value is None:
                continue
            bad_chars = sorted({ch for ch in text_value if _is_forbidden_char(ch)})
            if bad_chars:
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)}:{node.lineno}: {text_value!r} "
                    f"(forbidden chars: {bad_chars})"
                )

    assert not offenders, (
        "Kenney Future is Latin-only ASCII chrome; these labels must use "
        "NotoSansThai (Thai copy) or an image asset (icons/emoji) instead:\n" + "\n".join(offenders)
    )


_ARROW_RANGE = range(0x2190, 0x2200)


def _strings_containing_arrows(text: str) -> list[str]:
    return [line for line in text.splitlines() if any(0x2190 <= ord(ch) <= 0x21FF for ch in line)]


def test_how_to_play_content_has_no_unicode_arrows():
    """NotoSansThai also lacks U+2190/U+2192 — HTP row titles rendered with
    that font tofu on arrows. Content + derived HTP bodies must stay ASCII
    for arrow semantics (LEFT/RIGHT, ->)."""
    from core.how_to_play import load_how_to_play

    # Clear lru_cache so this test sees the on-disk JSON after edits in the
    # same pytest process that may have already loaded the catalog.
    load_how_to_play.cache_clear()
    model = load_how_to_play()
    offenders: list[str] = []
    for page in model.pages:
        for field_name, value in (
            ("title", page.title),
            ("body", page.body),
        ):
            for ch in value:
                if ord(ch) in _ARROW_RANGE:
                    offenders.append(f"page {page.id} {field_name}: {value!r}")
                    break
        for i, row in enumerate(page.rows):
            for field_name, value in (
                ("title", row.title),
                ("body", row.body),
                ("detail", row.detail),
            ):
                for ch in value:
                    if ord(ch) in _ARROW_RANGE:
                        offenders.append(f"page {page.id} row[{i}].{field_name}: {value!r}")
                        break

    balance_files = (
        "balance/v1/how_to_play.json",
        "balance/v1/junctions.json",
        "balance/v1/boss.json",
    )
    for rel in balance_files:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for line in _strings_containing_arrows(text):
            offenders.append(f"{rel}: {line.strip()}")

    assert not offenders, (
        "Unicode arrows render as tofu under NotoSansThai; use ASCII "
        "LEFT/RIGHT or '->' instead:\n" + "\n".join(offenders)
    )
