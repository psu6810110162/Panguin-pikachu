import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Choice:
    text: str
    heat_delta: float
    anger_delta: float
    is_systemic: bool


@dataclass
class JunctionData:
    zone_id: int
    category: str
    situation: str
    left_choice: Choice
    right_choice: Choice


def load_junctions(filepath: str | None = None) -> list[JunctionData]:
    """โหลดข้อมูลจาก JSON (Single Source of Truth - PR #58)"""
    if filepath is None:
        base_dir = Path(__file__).resolve().parent.parent
        filepath = str(base_dir / "balance" / "v1" / "junctions.json")

    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load junction data from {filepath}: {e}") from e

    junctions = []
    for j in data.get("junctions", []):
        left_data = j["left"]
        right_data = j["right"]
        left_choice = Choice(
            text=left_data["label"],
            heat_delta=left_data["meter_deltas"]["heat"],
            anger_delta=left_data["meter_deltas"]["capitalist_anger"],
            is_systemic=left_data["systemic"],
        )
        right_choice = Choice(
            text=right_data["label"],
            heat_delta=right_data["meter_deltas"]["heat"],
            anger_delta=right_data["meter_deltas"]["capitalist_anger"],
            is_systemic=right_data["systemic"],
        )
        junctions.append(
            JunctionData(
                zone_id=j["zone"],
                category=j["category"],
                situation=j["situation"],
                left_choice=left_choice,
                right_choice=right_choice,
            )
        )
    return junctions


_JUNCTIONS_CACHE: list[JunctionData] | None = None


def get_junction(zone_id: int) -> JunctionData:
    global _JUNCTIONS_CACHE
    if _JUNCTIONS_CACHE is None:
        _JUNCTIONS_CACHE = load_junctions()

    for junction in _JUNCTIONS_CACHE:
        if junction.zone_id == zone_id:
            return junction
    raise ValueError(f"Junction not found for zone {zone_id}")
