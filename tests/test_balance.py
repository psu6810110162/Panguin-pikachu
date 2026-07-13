"""Content validation for balance/v1/*.json — catches bad data at CI time, not runtime.

See docs/ENGINEERING_PLAN.md § Balance single source of truth and
docs/GAME_DESIGN.md § 6 for the design this data implements.
"""

import json
from pathlib import Path
from typing import Any

import pytest

BALANCE_DIR = Path(__file__).resolve().parent.parent / "balance" / "v1"
ALLOWED_METER_KEYS = {"heat", "capitalist_anger"}


def _load(name: str) -> dict[str, Any]:
    return json.loads((BALANCE_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def junctions() -> dict[str, Any]:
    return _load("junctions.json")


@pytest.fixture(scope="module")
def boss() -> dict[str, Any]:
    return _load("boss.json")


@pytest.fixture(scope="module")
def dag() -> dict[str, Any]:
    return _load("dag.json")


@pytest.fixture(scope="module")
def difficulty() -> dict[str, Any]:
    return _load("difficulty.json")


def test_all_balance_files_have_a_version(
    junctions: dict[str, Any], boss: dict[str, Any], dag: dict[str, Any], difficulty: dict[str, Any]
) -> None:
    for data in (junctions, boss, dag, difficulty):
        assert data["version"] == 1


def test_junctions_cover_all_ten_zones_with_no_duplicates(junctions: dict[str, Any]) -> None:
    zones = [j["zone"] for j in junctions["junctions"]]
    assert sorted(zones) == list(range(1, 11))


def test_junction_meter_deltas_use_only_known_meters(junctions: dict[str, Any]) -> None:
    for junction in junctions["junctions"]:
        for side in ("left", "right"):
            assert set(junction[side]["meter_deltas"]) <= ALLOWED_METER_KEYS


def test_junction_categories_match_zone_bands(junctions: dict[str, Any]) -> None:
    expected = {
        **{z: "cause" for z in range(1, 4)},
        **{z: "impact" for z in range(4, 7)},
        **{z: "solution" for z in range(7, 11)},
    }
    for junction in junctions["junctions"]:
        assert junction["category"] == expected[junction["zone"]]


def test_boss_has_exactly_three_waves(boss: dict[str, Any]) -> None:
    assert len(boss["waves"]) == 3
    assert [w["wave"] for w in boss["waves"]] == [1, 2, 3]


def test_boss_wave_items_are_declared_in_item_list(boss: dict[str, Any]) -> None:
    items = set(boss["items"])
    for wave in boss["waves"]:
        assert wave["correct_item"] in items
        assert wave["wrong_item"] in items
        assert wave["correct_item"] != wave["wrong_item"]


def test_dag_has_thirteen_edges_covering_all_decisions(dag: dict[str, Any]) -> None:
    assert len(dag["edges"]) == 13
    decisions = sorted(edge["decision"] for edge in dag["edges"])
    assert decisions == list(range(1, 14))


def test_dag_has_no_dangling_node_references(dag: dict[str, Any]) -> None:
    node_ids = {node["id"] for node in dag["nodes"]}
    for edge in dag["edges"]:
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids


def test_difficulty_meter_bounds_are_consistent(difficulty: dict[str, Any]) -> None:
    meters = difficulty["meters"]
    assert meters["min"] < meters["max"]
    assert meters["min"] <= meters["start_heat"] <= meters["max"]
    assert meters["min"] <= meters["start_capitalist_anger"] <= meters["max"]
    assert meters["game_over_at"] == meters["max"]


def test_difficulty_hearts_start_within_cap(difficulty: dict[str, Any]) -> None:
    hearts = difficulty["hearts"]
    assert 0 < hearts["start"] <= hearts["cap"]
