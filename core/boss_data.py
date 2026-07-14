"""Loader for balance/v1/boss.json — boss wave data.

Like junction_data.py, this loads from the JSON file which is the single source of truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BALANCE_DIR = Path(__file__).resolve().parent.parent / "balance" / "v1"


@dataclass(frozen=True)
class BossWave:
    wave: int
    theme: str
    wall_text: str
    correct_item: str
    wrong_item: str
    on_correct: dict[str, int]
    on_wrong: dict[str, int]
    science: str


@dataclass(frozen=True)
class BossData:
    version: int
    boss_id: str
    armor: int
    items: list[str]
    waves: dict[int, BossWave]


@lru_cache(maxsize=1)
def load_boss_data() -> BossData:
    raw = json.loads((BALANCE_DIR / "boss.json").read_text(encoding="utf-8"))

    waves: dict[int, BossWave] = {}
    for entry in raw["waves"]:
        wave = BossWave(
            wave=entry["wave"],
            theme=entry["theme"],
            wall_text=entry["wall_text"],
            correct_item=entry["correct_item"],
            wrong_item=entry["wrong_item"],
            on_correct=dict(entry.get("on_correct", {})),
            on_wrong=dict(entry.get("on_wrong", {})),
            science=entry.get("science", ""),
        )
        waves[wave.wave] = wave

    return BossData(
        version=raw["version"],
        boss_id=raw["boss_id"],
        armor=raw["armor"],
        items=list(raw["items"]),
        waves=waves,
    )
