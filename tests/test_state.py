import pytest

from core.state import (
    GameState,
    InvalidTransitionError,
    RunState,
    StateManager,
    validate_transition,
)


def test_state_manager_starts_at_menu():
    StateManager._instance = None
    sm = StateManager()
    assert sm.current_state == GameState.MENU


def test_state_manager_change_state():
    StateManager._instance = None
    sm = StateManager()
    sm.change_state(GameState.PLAYING)
    assert sm.current_state == GameState.PLAYING
    assert sm.is_playing() is True


def test_valid_run_state_path():
    state = RunState.LOBBY
    for next_state, context in [
        (RunState.RUNNING, {}),
        (RunState.BOSS, {"distance_m": 1000}),
        (RunState.FINISHED, {}),
        (RunState.SYNCED, {}),
    ]:
        validate_transition(state, next_state, **context)
        state = next_state


def test_respawn_and_resume_running():
    validate_transition(RunState.RUNNING, RunState.RESPAWNING)
    validate_transition(RunState.RESPAWNING, RunState.RUNNING)


def test_game_over_can_finish_from_running_or_respawning():
    validate_transition(RunState.RUNNING, RunState.FINISHED)
    validate_transition(RunState.RESPAWNING, RunState.FINISHED)


def test_rejects_out_of_order_transition():
    with pytest.raises(InvalidTransitionError):
        validate_transition(RunState.LOBBY, RunState.BOSS)


def test_rejects_boss_transition_before_reaching_the_finish_line():
    with pytest.raises(InvalidTransitionError, match="distance_m"):
        validate_transition(RunState.RUNNING, RunState.BOSS, distance_m=500)


def test_boss_guard_boundary_one_meter_short_is_rejected():
    with pytest.raises(InvalidTransitionError, match="distance_m"):
        validate_transition(RunState.RUNNING, RunState.BOSS, distance_m=999)


def test_boss_guard_boundary_exactly_at_the_finish_line_passes():
    validate_transition(RunState.RUNNING, RunState.BOSS, distance_m=1000)


def test_boss_cannot_respawn_by_design():
    # สมมติฐานที่บันทึกไว้ใน _ALLOWED_TRANSITIONS: boss phase ไม่มีการ respawn
    with pytest.raises(InvalidTransitionError):
        validate_transition(RunState.BOSS, RunState.RESPAWNING)


def test_synced_is_a_terminal_state():
    with pytest.raises(InvalidTransitionError):
        validate_transition(RunState.SYNCED, RunState.RUNNING)
