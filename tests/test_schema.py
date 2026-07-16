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
    assert record.balance_version == "v1"


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


def test_run_record_round_trips_balance_version():
    record = RunRecord(run_id="run-1", player_id="player-1", balance_version="v2")
    restored = RunRecord.from_dict(record.to_dict())
    assert restored.balance_version == "v2"


def test_run_record_from_dict_defaults_balance_version_to_v1_for_old_payloads():
    """run ที่ sync ก่อนมี field นี้ (ไม่มี balance_version ใน dict เลย) ต้องถือว่าเป็น v1
    เพราะ balance/v1/ คือ version เดียวที่เคยมีอยู่ตอนนั้น"""
    restored = RunRecord.from_dict({"run_id": "run-1", "player_id": "player-1"})
    assert restored.balance_version == "v1"


# ── Malformed data — บันทึกพฤติกรรมปัจจุบันของ contract ──────────────────
# from_dict ใช้ plain dataclass (ไม่ใช่ pydantic) จึง raise TypeError/KeyError ดิบ ๆ
# กับข้อมูลเสีย — ฝั่งที่รับข้อมูลจาก client จริง (server) ต้อง catch แล้วแปลงเป็น
# validation error ของตัวเองก่อนเสมอ test เหล่านี้ตรึงพฤติกรรมนั้นไว้เป็นลายลักษณ์อักษร


def test_run_record_from_dict_missing_required_field_raises_key_error():
    with pytest.raises(KeyError):
        RunRecord.from_dict({"run_id": "run-1"})  # ไม่มี player_id


def test_run_record_from_dict_unknown_state_name_raises_key_error():
    with pytest.raises(KeyError):
        RunRecord.from_dict({"run_id": "run-1", "player_id": "player-1", "state": "NOT_A_STATE"})


def test_run_result_from_dict_unexpected_field_raises_type_error():
    with pytest.raises(TypeError):
        RunResult.from_dict({"distance_m": 10, "not_a_real_field": 1})
