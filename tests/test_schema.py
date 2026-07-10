import pytest

from core.events import CollectEvent, RespawnEvent
from core.schema import SCHEMA_VERSION, RunRecord, RunResult
from core.state import InvalidTransitionError, RunState


def _make_record() -> RunRecord:
    return RunRecord(run_id="run-1", player_id="player-1")


def test_new_record_defaults_to_lobby_with_no_events():
    record = _make_record()
    assert record.schema_version == SCHEMA_VERSION
    assert record.state == RunState.LOBBY
    assert record.events == []
    assert record.result is None


def test_record_appends_events_in_order():
    record = _make_record()
    first = CollectEvent(timestamp=1.0, distance_m=10, item_type="gem", col=0, row=0, value=1)
    second = RespawnEvent(
        timestamp=2.0,
        distance_m=110,
        checkpoint_col=1,
        checkpoint_row=0,
        respawn_count=1,
        score_penalty=0.1,
    )

    record.record(first)
    record.record(second)

    assert record.events == [first, second]


def test_advance_state_follows_the_validated_transition_table():
    record = _make_record()
    record.advance_state(RunState.RUNNING)
    assert record.state == RunState.RUNNING

    record.advance_state(RunState.BOSS, distance_m=1000)
    assert record.state == RunState.BOSS


def test_advance_state_rejects_invalid_transitions_and_leaves_state_unchanged():
    record = _make_record()
    with pytest.raises(InvalidTransitionError):
        record.advance_state(RunState.BOSS)
    assert record.state == RunState.LOBBY


def test_run_record_round_trips_through_dict():
    record = _make_record()
    record.record(
        CollectEvent(timestamp=1.0, distance_m=10, item_type="gem", col=0, row=0, value=1)
    )
    record.advance_state(RunState.RUNNING)
    record.result = RunResult(distance_m=10, respawn_count=0)

    restored = RunRecord.from_dict(record.to_dict())

    assert restored.run_id == record.run_id
    assert restored.player_id == record.player_id
    assert restored.state == record.state
    assert restored.events == record.events
    assert restored.result == record.result


def test_run_record_round_trip_with_no_result():
    record = _make_record()
    restored = RunRecord.from_dict(record.to_dict())
    assert restored.result is None
