"""Loader for balance/v1/junctions.json — the 10 Y-Junction policy encounters.

Content (situations, left/right options, meter deltas, systemic flag) lives in JSON —
the single source of truth (docs/ENGINEERING_PLAN.md § Balance) — so a content edit
never touches this module. tests/test_balance.py already enforces zone coverage and
meter-key integrity at CI time; this module only loads + shapes that data for
gameplay/scoring code to consume.

policy_id convention: game/ (Y-Junction interaction, D1-A3) must emit
PolicyChoiceEvent.policy_id as f"zone{zone}-{side}" (e.g. "zone1-left",
"zone6-right") — Junction.policy_id() builds it, parse_policy_id() reverses it.
core/scoring/stealth.py and core/scoring/dag.py rely on this to look back from an
event to the systemic flag of the choice that produced it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

BALANCE_DIR = Path(__file__).resolve().parent.parent / "balance" / "v1"

Side = Literal["left", "right"]
Category = Literal["cause", "impact", "solution"]


@dataclass(frozen=True)
class JunctionOption:
    label: str
    meter_deltas: dict[str, float]
    systemic: bool
    note: str | None = None


@dataclass(frozen=True)
class Junction:
    zone: int
    category: Category
    situation: str
    left: JunctionOption
    right: JunctionOption

    def option(self, side: Side) -> JunctionOption:
        return self.left if side == "left" else self.right

    def policy_id(self, side: Side) -> str:
        """Canonical policy_id for PolicyChoiceEvent — see module docstring."""
        return f"zone{self.zone}-{side}"


def _parse_option(data: dict[str, object]) -> JunctionOption:
    return JunctionOption(
        label=cast(str, data["label"]),
        meter_deltas=dict(cast(dict[str, float], data["meter_deltas"])),
        systemic=cast(bool, data["systemic"]),
        note=cast("str | None", data.get("note")),
    )


@lru_cache(maxsize=1)
def _load_all() -> dict[int, Junction]:
    raw = json.loads((BALANCE_DIR / "junctions.json").read_text(encoding="utf-8"))
    result: dict[int, Junction] = {}
    for entry in raw["junctions"]:
        junction = Junction(
            zone=entry["zone"],
            category=entry["category"],
            situation=entry["situation"],
            left=_parse_option(entry["left"]),
            right=_parse_option(entry["right"]),
        )
        result[junction.zone] = junction
    return result


def get_junction(zone_id: int) -> Junction:
    """Junction data for zone_id (1-10). Raises KeyError if zone_id is out of range."""
    junctions = _load_all()
    if zone_id not in junctions:
        raise KeyError(f"No junction data for zone {zone_id!r}")
    return junctions[zone_id]


def all_junctions() -> list[Junction]:
    """All 10 junctions, sorted by zone ascending."""
    return [get_junction(zone) for zone in sorted(_load_all())]


def parse_policy_id(policy_id: str) -> tuple[int, Side]:
    """Inverse of Junction.policy_id — e.g. "zone3-left" -> (3, "left")."""
    zone_part, _, side = policy_id.partition("-")
    if not zone_part.startswith("zone") or side not in ("left", "right"):
        raise ValueError(f"Malformed policy_id: {policy_id!r}")
    return int(zone_part.removeprefix("zone")), cast(Side, side)


def option_for_policy_id(policy_id: str) -> JunctionOption:
    """The JunctionOption a PolicyChoiceEvent.policy_id refers to."""
    zone, side = parse_policy_id(policy_id)
    return get_junction(zone).option(side)


def parse_policy_id_or_none(policy_id: str) -> tuple[int, Side] | None:
    """Tolerant parse_policy_id — returns None instead of raising on a malformed id.

    See option_for_policy_id_or_none for why scoring must never crash on client input.
    """
    try:
        return parse_policy_id(policy_id)
    except ValueError:
        return None


def option_for_policy_id_or_none(policy_id: str) -> JunctionOption | None:
    """Tolerant option_for_policy_id — returns None for a malformed or out-of-range
    policy_id instead of raising.

    Scoring (core/scoring/stealth.py, dag.py) runs server-side on client-supplied
    event logs (server-authoritative, docs/adr/006). A malformed/unknown policy_id
    from a buggy or hostile client must never crash evaluate()/ingest — callers treat
    None as "not a recognized systemic choice" (non-systemic / skipped). This does NOT
    excuse producers: game/ must still emit the canonical f"zone{zone}-{side}" (see
    module docstring) or systemic choices silently score zero.
    """
    try:
        return option_for_policy_id(policy_id)
    except (ValueError, KeyError):
        return None
