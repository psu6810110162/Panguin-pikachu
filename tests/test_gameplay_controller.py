import gc
import statistics
import time
import tracemalloc
import weakref
from dataclasses import FrozenInstanceError

import pytest

from core.items import ItemType
from core.state import GameOverReason, RunState
from game.controller import GameplayController


def test_view_state_is_frozen_fresh_and_does_not_change_retroactively():
    controller = GameplayController()
    old = controller.view_state()
    controller.gems = 7
    new = controller.view_state()

    assert old is not new
    assert old.gems == 0
    assert new.gems == 7
    with pytest.raises(FrozenInstanceError):
        old.gems = 99  # type: ignore[misc]


def test_controller_contract_pause_restart_and_terminal_take_once():
    controller = GameplayController()
    assert controller.pause().run_state is controller.view_state().run_state
    controller.resume()
    controller.grid.forward_tiles += 1  # type: ignore[attr-defined]
    result = controller.finish()
    assert result.distance_m > 0
    assert controller.take_terminal_result() is result
    assert controller.take_terminal_result() is None
    assert controller.restart().distance_m == 0


def test_game_over_from_running_produces_finished_terminal_result():
    controller = GameplayController()
    result = controller.finish(GameOverReason.HEARTS)

    assert result.state is RunState.FINISHED
    assert result.reason is GameOverReason.HEARTS


def test_eco_seed_mutates_domain_through_controller():
    controller = GameplayController()
    controller.inventory.add_item(ItemType.ECO_SEED)
    before = controller.view_state().heat
    assert controller.use_eco_seed() is True
    assert controller.view_state().heat < before


def test_controller_tick_p95_is_below_ci_guard():
    controller = GameplayController()
    durations_ms = []
    for _ in range(1_000):
        started = time.perf_counter()
        controller.tick(1 / 60)
        durations_ms.append((time.perf_counter() - started) * 1_000)
    p95 = statistics.quantiles(durations_ms, n=100)[94]
    assert p95 < 8.0


def test_100_runs_do_not_retain_controllers_or_more_than_five_mib():
    tracemalloc.start()
    for _ in range(10):
        warmup = GameplayController()
        warmup.tick(1 / 60)
    del warmup
    gc.collect()
    baseline = tracemalloc.take_snapshot()

    references = []
    for _ in range(100):
        controller = GameplayController()
        controller.tick(1 / 60)
        references.append(weakref.ref(controller))
    del controller
    gc.collect()
    final = tracemalloc.take_snapshot()
    retained = sum(stat.size_diff for stat in final.compare_to(baseline, "filename"))
    tracemalloc.stop()

    assert all(reference() is None for reference in references)
    assert retained <= 5 * 1024 * 1024
