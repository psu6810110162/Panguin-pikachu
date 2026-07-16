import pytest

from core.state import DeathCause, GameOverReason, RunMetrics


def test_run_metrics_initialization():
    metrics = RunMetrics()
    assert metrics.heat_meter == 50.0
    assert metrics.capitalist_anger == 50.0
    assert metrics.hearts == 5
    assert not metrics.is_game_over
    assert not metrics.needs_respawn
    assert not metrics.is_invincible
    assert metrics.game_over_reason is None
    assert metrics.last_death_cause is None


def test_run_metrics_update_safe():
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    metrics.update_meters(-100.0, -100.0)
    assert metrics.heat_meter == 0.0
    assert metrics.capitalist_anger == 0.0
    assert not metrics.is_game_over

    metrics.update_meters(50.5, 60.5)
    assert metrics.heat_meter == 50.5
    assert metrics.capitalist_anger == 60.5
    assert not metrics.is_game_over


def test_run_metrics_game_over_at_100():
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    metrics.update_meters(50.0, 0.0)
    assert metrics.heat_meter == 100.0
    assert metrics.is_game_over
    assert metrics.game_over_reason is GameOverReason.HEAT


def test_run_metrics_game_over_anger_at_100():
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    metrics.update_meters(0.0, 150.0)
    assert metrics.capitalist_anger == 100.0
    assert metrics.is_game_over
    assert metrics.game_over_reason is GameOverReason.ANGER


def test_request_death_records_cause_and_waits_for_respawn():
    metrics = RunMetrics(hearts=5)
    assert metrics.request_death(DeathCause.MELT)
    assert metrics.hearts == 4
    assert metrics.needs_respawn
    assert metrics.grace_active is False
    assert metrics.is_invincible

    assert not metrics.request_death(DeathCause.IDLE)
    assert metrics.last_death_cause is DeathCause.MELT


def test_grace_starts_only_on_complete_respawn_not_on_death():
    metrics = RunMetrics(hearts=2)
    metrics.request_death(DeathCause.FALL)
    assert metrics.grace_active is False
    assert metrics.needs_respawn

    metrics.complete_respawn()
    assert not metrics.needs_respawn
    assert metrics.grace_active
    assert metrics.grace_remaining == metrics.invincible_seconds
    assert metrics.is_invincible


def test_grace_survives_first_move_and_expires_only_on_time():
    metrics = RunMetrics(hearts=2)
    metrics.complete_respawn()
    metrics.tick_grace(metrics.invincible_seconds / 2)
    assert metrics.grace_active
    metrics.tick_grace(metrics.invincible_seconds)
    assert not metrics.grace_active
    assert not metrics.is_invincible


def test_tick_grace_with_dt_larger_than_remaining_clamps_to_zero():
    metrics = RunMetrics()
    metrics.complete_respawn()
    metrics.tick_grace(metrics.invincible_seconds + 10.0)
    assert not metrics.grace_active


def test_complete_respawn_twice_restarts_full_window():
    metrics = RunMetrics()
    metrics.complete_respawn()
    metrics.tick_grace(metrics.invincible_seconds / 2)
    metrics.complete_respawn()
    assert metrics.grace_active
    assert metrics.is_invincible


def test_is_invincible_has_no_setter():
    metrics = RunMetrics()
    with pytest.raises(AttributeError):
        metrics.is_invincible = False  # type: ignore[misc]


def test_simultaneous_heat_and_anger_cap_is_deterministic():
    metrics = RunMetrics(heat_meter=95.0, capitalist_anger=95.0)
    metrics.update_meters(10.0, 10.0)
    assert metrics.game_over_reason is GameOverReason.HEAT

    metrics = RunMetrics(heat_meter=95.0, capitalist_anger=90.0)
    metrics.update_meters(10.0, 20.0)
    assert metrics.game_over_reason is GameOverReason.ANGER


def test_trigger_game_over_keeps_first_reason():
    metrics = RunMetrics()
    metrics.trigger_game_over(GameOverReason.HEAT)
    metrics.trigger_game_over(GameOverReason.ANGER)
    assert metrics.game_over_reason is GameOverReason.HEAT


def test_run_metrics_game_over_callback():
    triggered = False

    def cb():
        nonlocal triggered
        triggered = True

    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0, on_game_over=cb)
    metrics.update_meters(100.0, 0.0)
    assert metrics.is_game_over
    assert triggered


def test_increase_heart():
    metrics = RunMetrics(hearts=4)
    metrics.increase_heart()
    assert metrics.hearts == 5
    metrics.increase_heart()
    assert metrics.hearts == 5


def test_respawn_seconds_loaded_from_difficulty():
    metrics = RunMetrics()
    assert metrics.respawn_seconds == 3.0


def test_request_death_without_respawn_keeps_flags_clear():
    metrics = RunMetrics(hearts=5)
    assert metrics.request_death(None, allow_respawn=False)
    assert metrics.hearts == 4
    assert not metrics.needs_respawn
    assert not metrics.is_invincible

    assert metrics.request_death(None, allow_respawn=False)
    assert metrics.hearts == 3


def test_request_death_without_respawn_triggers_game_over_at_zero():
    metrics = RunMetrics(hearts=1)
    assert metrics.request_death(None, allow_respawn=False)
    assert metrics.hearts == 0
    assert metrics.is_game_over
    assert metrics.game_over_reason is GameOverReason.HEARTS
