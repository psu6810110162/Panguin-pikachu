"""Tests for core.session.GameSession — the single-writer owner of a RunRecord.

Verifies event emission, timestamps from an injected clock, and lifecycle
transitions. See docs/adr/001-runrecord-contract.md and core/session.py.
"""

import pytest

from core.events import CheckpointReachedEvent, CollectEvent, ObstacleHitEvent
from core.schema import RunRecord
from core.session import GameSession
from core.state import InvalidTransitionError, RunState


class StubClock:
    """Controllable clock so timestamps are deterministic in tests."""

    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def test_new_session_starts_in_lobby_with_no_events() -> None:
    session = GameSession()
    assert session.state == RunState.LOBBY
    assert session.events_count == 0
    assert isinstance(session.run_record, RunRecord)


def test_run_id_defaults_to_a_unique_value() -> None:
    assert GameSession().run_record.run_id != GameSession().run_record.run_id


def test_explicit_run_id_and_player_id_are_kept() -> None:
    session = GameSession(run_id="run-42", player_id="alice")
    assert session.run_record.run_id == "run-42"
    assert session.run_record.player_id == "alice"


def test_start_advances_lobby_to_running() -> None:
    session = GameSession()
    session.start()
    assert session.state == RunState.RUNNING


def test_collect_records_a_collect_event_with_expected_fields() -> None:
    session = GameSession()
    session.collect(item_type="gem", col=3, row=4, value=1, distance_m=120)

    assert session.events_count == 1
    event = session.run_record.events[0]
    assert isinstance(event, CollectEvent)
    assert (event.item_type, event.col, event.row, event.value, event.distance_m) == (
        "gem",
        3,
        4,
        1,
        120,
    )


def test_obstacle_hit_records_destroyed_flag() -> None:
    session = GameSession()
    session.obstacle_hit(col=1, row=2, damage=1, destroyed=True, distance_m=50)

    event = session.run_record.events[0]
    assert isinstance(event, ObstacleHitEvent)
    assert event.destroyed is True
    assert event.damage == 1


def test_checkpoint_reached_records_index() -> None:
    session = GameSession()
    session.checkpoint_reached(checkpoint_index=2, distance_m=200)

    event = session.run_record.events[0]
    assert isinstance(event, CheckpointReachedEvent)
    assert event.checkpoint_index == 2


def test_timestamps_are_measured_from_session_start_via_injected_clock() -> None:
    clock = StubClock(100.0)
    session = GameSession(clock=clock)  # start captured at t=100.0

    clock.t = 100.5
    session.collect(item_type="gem", col=0, row=0, value=1, distance_m=10)
    clock.t = 102.0
    session.collect(item_type="gem", col=1, row=0, value=1, distance_m=20)

    timestamps = [e.timestamp for e in session.run_record.events]
    assert timestamps == pytest.approx([0.5, 2.0])


def test_events_are_recorded_in_call_order() -> None:
    session = GameSession()
    session.collect(item_type="gem", col=0, row=0, value=1, distance_m=10)
    session.obstacle_hit(col=1, row=0, damage=1, destroyed=False, distance_m=20)
    session.checkpoint_reached(checkpoint_index=1, distance_m=100)

    types = [e.event_type for e in session.run_record.events]
    assert types == ["collect", "obstacle_hit", "checkpoint_reached"]


def test_full_lifecycle_transitions_are_valid() -> None:
    session = GameSession()
    session.start()
    session.enter_boss(distance_m=1000)
    session.finish()
    session.mark_synced()
    assert session.state == RunState.SYNCED


def test_respawn_round_trip_transitions() -> None:
    session = GameSession()
    session.start()
    session.begin_respawn()
    assert session.state == RunState.RESPAWNING
    session.resume_after_respawn()
    assert session.state == RunState.RUNNING


def test_enter_boss_before_finish_line_is_rejected() -> None:
    session = GameSession()
    session.start()
    with pytest.raises(InvalidTransitionError):
        session.enter_boss(distance_m=500)


def test_recorded_events_survive_run_record_json_round_trip() -> None:
    session = GameSession(run_id="run-1", player_id="p1")
    session.start()
    session.collect(item_type="scientific_item", col=2, row=2, value=1, distance_m=300)
    session.policy_choice(
        checkpoint_index=3,
        policy_id="zone3-left",
        meter_deltas={"heat": -5.0, "capitalist_anger": 25.0},
        distance_m=300,
    )

    restored = RunRecord.from_dict(session.run_record.to_dict())
    assert restored.run_id == "run-1"
    assert restored.player_id == "p1"
    assert [e.event_type for e in restored.events] == ["collect", "policy_choice"]
    assert restored.state == RunState.RUNNING

    collect_event, policy_event = restored.events
    assert (collect_event.item_type, collect_event.col, collect_event.row, collect_event.value) == (
        "scientific_item",
        2,
        2,
        1,
    )
    assert (policy_event.checkpoint_index, policy_event.policy_id) == (3, "zone3-left")
    assert policy_event.meter_deltas == {"heat": -5.0, "capitalist_anger": 25.0}


def test_policy_choice_copies_meter_deltas_so_caller_mutation_cannot_alter_the_recorded_event() -> (
    None
):
    session = GameSession()
    deltas = {"heat": -5.0, "capitalist_anger": 25.0}
    session.policy_choice(
        checkpoint_index=1, policy_id="zone1-right", meter_deltas=deltas, distance_m=100
    )

    deltas["heat"] = 999.0  # mutate the caller's dict after recording

    recorded = session.run_record.events[0]
    assert recorded.meter_deltas == {"heat": -5.0, "capitalist_anger": 25.0}
