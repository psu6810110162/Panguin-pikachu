from core.events import PolicyChoiceEvent
from core.interaction import YJunctionInteraction
from core.junction_data import get_junction
from core.session import GameSession
from core.state import DeathCause, RunMetrics


def test_timeout_is_recorded_without_faking_a_side_choice():
    session = GameSession()
    session.start()
    metrics = RunMetrics(heat_meter=50, capitalist_anger=50)
    interaction = YJunctionInteraction(metrics, session)

    interaction.handle_timeout(get_junction(1), distance_m=42, meter_penalty=5)

    event = session.run_record.events[-1]
    assert isinstance(event, PolicyChoiceEvent)
    assert event.outcome == "timeout"
    assert event.policy_id == "zone1-timeout"
    assert event.meter_deltas == {"heat": 5, "capitalist_anger": 5}
    assert metrics.heat_meter == 55
    assert metrics.capitalist_anger == 55


def test_respawn_grace_ignores_fall_damage_without_consuming_a_heart():
    """A protected checkpoint cannot leave the player in a dead-but-running state."""
    metrics = RunMetrics(hearts=2)
    metrics.complete_respawn()

    assert not metrics.request_death(DeathCause.FALL)

    assert metrics.hearts == 2
    assert metrics.needs_respawn is False
    assert metrics.is_game_over is False
