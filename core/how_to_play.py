"""Pure, data-driven model for the in-game How to Play overlay.

Presentation copy lives in ``balance/v1/how_to_play.json``. Values that must
stay aligned with gameplay are derived from the existing balance loaders, so
the tutorial cannot drift from junction, boss, meter, or scoring content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

from core.boss_data import load_boss_data
from core.junction_data import all_junctions
from core.scoring.dag import load_graph_data
from core.scoring.stealth import load_config
from core.state import load_difficulty

BALANCE_DIR = Path(__file__).resolve().parent.parent / "balance" / "v1"
PageKind = Literal[
    "authored",
    "derived_meters",
    "scaffolding",
    "items",
    "junctions",
    "boss",
    "outcomes",
    "scoring",
]


@dataclass(frozen=True)
class HelpRow:
    """One compact card or table row for a tutorial page."""

    title: str
    body: str
    detail: str = ""


@dataclass(frozen=True)
class HowToPlayPage:
    id: str
    title: str
    body: str
    rows: tuple[HelpRow, ...] = ()


@dataclass(frozen=True)
class HowToPlayModel:
    title: str
    pages: tuple[HowToPlayPage, ...]


class HowToPlayPager:
    """Pure bounded page navigation, intentionally independent of Kivy."""

    def __init__(self, pages: tuple[HowToPlayPage, ...]) -> None:
        if not pages:
            raise ValueError("How to Play requires at least one page")
        self._pages = pages
        self._index = 0

    @property
    def current(self) -> HowToPlayPage:
        return self._pages[self._index]

    @property
    def index(self) -> int:
        return self._index

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def indicator(self) -> str:
        return f"{self._index + 1} / {self.page_count}"

    @property
    def can_go_previous(self) -> bool:
        return self._index > 0

    @property
    def can_go_next(self) -> bool:
        return self._index < self.page_count - 1

    def go_to(self, index: int) -> bool:
        bounded = max(0, min(index, self.page_count - 1))
        changed = bounded != self._index
        self._index = bounded
        return changed

    def next_page(self) -> bool:
        return self.go_to(self._index + 1)

    def previous_page(self) -> bool:
        return self.go_to(self._index - 1)


def _signed(value: float) -> str:
    return f"{value:+.0f}"


def _difficulty_block(name: str) -> dict[str, Any]:
    difficulty = load_difficulty()
    block = difficulty.get(name)
    if not isinstance(block, dict):
        raise ValueError(f"difficulty.json has no object block {name!r}")
    return cast(dict[str, Any], block)


def _parse_kind(value: object) -> PageKind:
    valid: set[str] = {
        "authored",
        "derived_meters",
        "scaffolding",
        "items",
        "junctions",
        "boss",
        "outcomes",
        "scoring",
    }
    if not isinstance(value, str) or value not in valid:
        raise ValueError(f"Unknown How to Play page kind: {value!r}")
    return cast(PageKind, value)


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"How to Play page requires non-empty {key!r}")
    return value


def _rows_for_page(raw: dict[str, Any], kind: PageKind) -> tuple[HelpRow, ...]:
    if kind == "authored":
        controls = raw.get("controls", [])
        if not isinstance(controls, list):
            raise ValueError("controls must be a list")
        return tuple(
            HelpRow(
                title=_required_string(cast(dict[str, Any], control), "keys"),
                body=_required_string(cast(dict[str, Any], control), "action"),
            )
            for control in controls
            if isinstance(control, dict)
        )

    if kind == "derived_meters":
        meters = _difficulty_block("meters")
        hearts = _difficulty_block("hearts")
        return (
            HelpRow(
                title="Heat Meter / Capitalist Anger",
                body=(
                    f"เริ่มที่ Heat {meters['start_heat']:.0f} และ Anger "
                    f"{meters['start_capitalist_anger']:.0f} จากช่วง "
                    f"{meters['min']:.0f}–{meters['max']:.0f}"
                ),
                detail=f"หลอดใดถึง {meters['game_over_at']:.0f} = Game Over",
            ),
            HelpRow(
                title="Hearts และ checkpoint",
                body=(
                    f"เริ่ม {hearts['start']} หัวใจ สูงสุด {hearts['cap']} "
                    f"ตกเหวเสีย {hearts['fall_penalty']} หัวใจ แล้ว respawn"
                ),
                detail=f"เวลารอ respawn {hearts['respawn_seconds']:.1f} วินาที",
            ),
        )

    if kind == "scaffolding":
        entries = raw.get("scaffolding")
        if not isinstance(entries, list) or len(entries) != 4:
            raise ValueError("scaffolding page requires exactly four entries")
        return tuple(
            HelpRow(
                title=_required_string(cast(dict[str, Any], entry), "title"),
                body=_required_string(cast(dict[str, Any], entry), "description"),
                detail=(
                    "พร้อมใช้งานใน build นี้"
                    if cast(dict[str, Any], entry).get("status") == "active"
                    else "แนวทางจาก GDD / กำลังพัฒนาสำหรับ build ถัดไป"
                ),
            )
            for entry in entries
            if isinstance(entry, dict)
        )

    if kind == "items":
        item_entries = raw.get("items")
        boss = load_boss_data()
        eco_seed = _difficulty_block("eco_seed")
        if not isinstance(item_entries, list):
            raise ValueError("items page requires item entries")
        known_items = set(boss.items)
        rows: list[HelpRow] = []
        for entry in item_entries:
            if not isinstance(entry, dict):
                raise ValueError("item entry must be an object")
            item_id = _required_string(entry, "item_id")
            if item_id not in known_items:
                raise ValueError(f"Unknown evidence item {item_id!r}")
            waves = [wave.wave for wave in boss.waves.values() if wave.correct_item == item_id]
            detail = f"คำตอบที่ถูกในบอสเวฟ {', '.join(map(str, waves))}"
            if item_id == "eco_seed":
                detail += f" · Spacebar: Heat {_signed(float(eco_seed['heat_reduction']))}"
            rows.append(
                HelpRow(
                    title=_required_string(entry, "display_name"),
                    body=_required_string(entry, "description"),
                    detail=detail,
                )
            )
        return tuple(rows)

    if kind == "junctions":
        zones = raw.get("zones")
        if not isinstance(zones, list) or len(zones) != 2:
            raise ValueError("junction page requires exactly two zones")
        by_zone = {junction.zone: junction for junction in all_junctions()}
        rows = []
        for zone in zones:
            if not isinstance(zone, int) or zone not in by_zone:
                raise ValueError(f"Unknown junction zone {zone!r}")
            junction = by_zone[zone]
            left = junction.left
            right = junction.right
            left_text = (
                f"ซ้าย: {left.label} "
                f"(Heat {_signed(left.meter_deltas['heat'])}, "
                f"Anger {_signed(left.meter_deltas['capitalist_anger'])})"
            )
            right_text = (
                f"ขวา: {right.label} "
                f"(Heat {_signed(right.meter_deltas['heat'])}, "
                f"Anger {_signed(right.meter_deltas['capitalist_anger'])})"
            )
            systemic_side = "ซ้าย" if left.systemic else "ขวา"
            note = left.note if left.systemic and left.note else right.note
            detail = f"Systemic choice: {systemic_side}"
            if note:
                detail += f" · {note}"
            rows.append(
                HelpRow(
                    title=f"Zone {zone}: {junction.situation}",
                    body=f"{left_text}\n{right_text}",
                    detail=detail,
                )
            )
        return tuple(rows)

    if kind == "boss":
        boss = load_boss_data()
        return tuple(
            HelpRow(
                title=f"Wave {wave.wave}: {wave.wall_text}",
                body=(
                    f"ถูก: {wave.correct_item.replace('_', ' ').title()} -> เกราะ "
                    f"{_signed(wave.on_correct.get('boss_armor', 0))}\n"
                    f"ผิด: {wave.wrong_item.replace('_', ' ').title()} -> หัวใจ "
                    f"{_signed(wave.on_wrong.get('hearts', 0))}"
                ),
                detail=wave.science,
            )
            for wave in boss.waves.values()
        )

    if kind == "outcomes":
        return (
            HelpRow(title="ชนะ", body=_required_string(raw, "win")),
            HelpRow(title="แพ้", body=_required_string(raw, "loss")),
            HelpRow(title="กติกาในบอส", body=_required_string(raw, "boss_note")),
        )

    if kind == "scoring":
        config = load_config()
        graph = load_graph_data()
        return (
            HelpRow(
                title="Gameplay / Survival",
                body="วัดการควบคุมหลอดและการเอาตัวรอดตลอดการวิ่ง",
                detail="คะแนนนี้อยู่ใน gameplay scoring ไม่ใช่ค่า °C",
            ),
            HelpRow(
                title="Run Reduction",
                body=f"เลือก systemic ที่ทางแยกได้ {config.systemic_point_c:.1f}°C ต่อครั้ง",
                detail=f"สูงสุด {config.max_run_reduction_c:.1f}°C",
            ),
            HelpRow(
                title="Cognitive Score",
                body=f"ตอบบอสถูกได้ {config.boss_bonus_per_wave_c:.1f}°C ต่อเวฟ",
                detail=f"สูงสุด {config.max_boss_reduction_c:.1f}°C",
            ),
            HelpRow(
                title="Net Impact และ DAG",
                body="Net Impact = Run Reduction + Cognitive Score",
                detail=(
                    f"DAG มี {len(graph.edges)} เส้น: เขียว = systemic/ตอบบอสถูก, "
                    "แดง = ความเข้าใจคลาดเคลื่อนพร้อมคำอธิบาย"
                ),
            ),
        )

    return ()


@lru_cache(maxsize=1)
def load_how_to_play() -> HowToPlayModel:
    """Load authored tutorial copy and merge it with live balance data."""
    raw = json.loads((BALANCE_DIR / "how_to_play.json").read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("how_to_play.json version must be 1")
    pages_data = raw.get("pages")
    if not isinstance(pages_data, list) or not pages_data:
        raise ValueError("how_to_play.json requires a non-empty pages list")

    pages: list[HowToPlayPage] = []
    ids: set[str] = set()
    for entry in pages_data:
        if not isinstance(entry, dict):
            raise ValueError("How to Play page must be an object")
        page_id = _required_string(entry, "id")
        if page_id in ids:
            raise ValueError(f"Duplicate How to Play page id {page_id!r}")
        ids.add(page_id)
        kind = _parse_kind(entry.get("kind"))
        pages.append(
            HowToPlayPage(
                id=page_id,
                title=_required_string(entry, "title"),
                body=_required_string(entry, "body"),
                rows=_rows_for_page(cast(dict[str, Any], entry), kind),
            )
        )

    required_ids = {
        "goal_controls",
        "meters_hearts",
        "visual_scaffolding",
        "evidence_items",
        "carbon_baron",
        "win_loss",
        "scores_dag",
    }
    if not required_ids <= ids:
        missing = sorted(required_ids - ids)
        raise ValueError(f"How to Play is missing required pages: {missing}")
    expected_zones = list(range(1, 11))
    actual_zones = [
        zone
        for entry in pages_data
        if isinstance(entry, dict) and entry.get("kind") == "junctions"
        for zone in entry.get("zones", [])
    ]
    if actual_zones != expected_zones:
        raise ValueError("How to Play junction page zones must cover 1 through 10 in order")

    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("how_to_play.json requires a title")
    return HowToPlayModel(title=title, pages=tuple(pages))
