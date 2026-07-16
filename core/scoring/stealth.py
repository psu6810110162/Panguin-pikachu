"""Stealth Assessment — the Educational Score concern (ADR-011).

GAME_DESIGN.md §7 describes scoring as two dimensions read from the same event log:

  1. The raw Heat/Capitalist trade-off ("Impact Score" = Σ ΔTemp_i) is already
     computed by core/scoring/rules.py (heat_controlled_pct, policy_score) as the
     Gameplay Score concern — not duplicated here.
  2. Cognitive Score (boss correctness) + Net Impact Score ("อุณหภูมิที่กอบกู้ได้")
     + rank — this module, the Educational Score concern.

This module counts *systemic* junction choices (core.junction_data.JunctionOption
.systemic) and *correct* boss waves, not raw meter deltas — a systemic choice earns
credit even if it happens to raise a meter, which is the whole point of teaching
structural vs. symptomatic fixes (see docs/adr/011-learning-evaluation-pipeline.md).

All tuning constants (points per systemic choice, boss bonus, rank bands) live in
balance/v1/difficulty.json — the single source of truth (docs/ENGINEERING_PLAN.md
§ Balance) — never hardcoded here. Per ADR-012 these functions must be
deterministic: same events -> same result, every time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from core.events import BossPhaseEvent, GameEvent, PolicyChoiceEvent
from core.junction_data import option_for_policy_id

BALANCE_DIR = Path(__file__).resolve().parent.parent.parent / "balance" / "v1"


@dataclass(frozen=True)
class RankBand:
    rank: str
    label: str
    min_c: float
    max_c: float


@dataclass(frozen=True)
class ScoringConfig:
    systemic_point_c: float
    max_run_reduction_c: float
    boss_bonus_per_wave_c: float
    max_boss_reduction_c: float
    ranks: tuple[RankBand, ...]


@lru_cache(maxsize=1)
def load_config() -> ScoringConfig:
    """Read the scoring block of balance/v1/difficulty.json (cached — static content)."""
    raw = json.loads((BALANCE_DIR / "difficulty.json").read_text(encoding="utf-8"))["scoring"]
    ranks = tuple(
        RankBand(rank=r["rank"], label=r["label"], min_c=r["min_c"], max_c=r["max_c"])
        for r in raw["ranks"]
    )
    return ScoringConfig(
        systemic_point_c=raw["systemic_point_c"],
        max_run_reduction_c=raw["max_run_reduction_c"],
        boss_bonus_per_wave_c=raw["boss_bonus_per_wave_c"],
        max_boss_reduction_c=raw["max_boss_reduction_c"],
        ranks=ranks,
    )


def systemic_choice_count(events: list[GameEvent]) -> int:
    """จำนวน Y-Junction ที่ผู้เล่นเลือกตัวเลือก systemic (แก้ที่ต้นเหตุ)"""
    return sum(
        1
        for e in events
        if (
            isinstance(e, PolicyChoiceEvent)
            and e.outcome != "timeout"
            and option_for_policy_id(e.policy_id).systemic
        )
    )


def run_reduction_c(events: list[GameEvent], *, config: ScoringConfig | None = None) -> float:
    """°C ที่กอบกู้ได้จากช่วงวิ่ง = จำนวนตัวเลือก systemic x systemic_point_c (cap max_run_reduction_c)"""
    cfg = config or load_config()
    return min(systemic_choice_count(events) * cfg.systemic_point_c, cfg.max_run_reduction_c)


def correct_boss_wave_count(events: list[GameEvent]) -> int:
    """จำนวนเวฟบอสที่ตอบถูก (BossPhaseEvent.outcome == "damage_dealt")"""
    return sum(1 for e in events if isinstance(e, BossPhaseEvent) and e.outcome == "damage_dealt")


def cognitive_score_c(events: list[GameEvent], *, config: ScoringConfig | None = None) -> float:
    """°C โบนัสจากบอส = จำนวนเวฟที่ตอบถูก x boss_bonus_per_wave_c (cap max_boss_reduction_c)

    ปัจจุบันบอสมี 3 เวฟ (boss.json) x 0.1°C/เวฟ = สูงสุดจริง 0.3°C — cap
    max_boss_reduction_c (0.5°C) เป็นเพดานที่ยังไม่ถูกแตะ เผื่อจำนวนเวฟเพิ่มในอนาคต
    """
    cfg = config or load_config()
    return min(
        correct_boss_wave_count(events) * cfg.boss_bonus_per_wave_c, cfg.max_boss_reduction_c
    )


def net_impact_score_c(events: list[GameEvent], *, config: ScoringConfig | None = None) -> float:
    """ "อุณหภูมิโลกที่คุณกอบกู้ได้" = run_reduction_c + cognitive_score_c"""
    cfg = config or load_config()
    return run_reduction_c(events, config=cfg) + cognitive_score_c(events, config=cfg)


def rank_for(temp_reduced_c: float, *, config: ScoringConfig | None = None) -> str | None:
    """Rank (เช่น "S", "A") ตามช่วง temp_reduced_c ที่ตกอยู่ — None ถ้าไม่เข้าเกณฑ์ไหนเลย"""
    cfg = config or load_config()
    for band in cfg.ranks:
        if band.min_c <= temp_reduced_c <= band.max_c:
            return band.rank
    return None
