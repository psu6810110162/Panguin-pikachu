from core.boss_data import load_boss_data
from core.events import BossPhaseEvent, BossVictoryEvent, PolicyChoiceEvent
from core.interaction import YJunctionInteraction
from core.junction_data import get_junction, parse_policy_id
from core.session import GameSession
from core.state import RunMetrics, RunState
from game.grid import GridManager


def _play_once(grid):
    grid.reset()
    session = GameSession()
    metrics = RunMetrics()
    interaction = YJunctionInteraction(metrics, session)
    session.start()

    while grid.next_zone <= grid.spawning_system.NUM_ZONES:
        grid._append_segment()
    resolved_zones = set()
    for tile in grid.path_set.values():
        if tile.zone_id is not None and tile.zone_id not in resolved_zones:
            interaction.handle_choice(get_junction(tile.zone_id), tile.side)
            resolved_zones.add(tile.zone_id)

    for wave in range(3):
        grid._build_boss_wave(wave)
    session.enter_boss(distance_m=1000)
    boss_data = load_boss_data()
    for wave in range(1, 4):
        placement = next(
            item
            for item in grid.boss_items.values()
            if item.wave == wave and item.item_id == boss_data.waves[wave].correct_item
        )
        session.boss_phase(phase=placement.wave, outcome="damage_dealt", distance_m=1000)
        grid.pop_boss_wave(wave)
    session.boss_victory(total_time_s=session.elapsed(), distance_m=1000)
    session.finish()
    return session


def test_two_complete_headless_runs_have_all_decisions():
    grid = GridManager()
    for _ in range(2):
        session = _play_once(grid)
        events = session.run_record.events
        policy_events = [event for event in events if isinstance(event, PolicyChoiceEvent)]
        assert len(policy_events) == 10
        assert {parse_policy_id(event.policy_id)[0] for event in policy_events} == set(range(1, 11))
        assert len([event for event in events if isinstance(event, BossPhaseEvent)]) == 3
        assert len([event for event in events if isinstance(event, BossVictoryEvent)]) == 1
        assert session.state is RunState.FINISHED
