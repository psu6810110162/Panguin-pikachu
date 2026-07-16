"""Heart pickups + post-policy environment bias on the grid."""

import random

from core.items import ItemType
from core.state import load_difficulty
from game.grid import GridManager


def test_apply_policy_environment_sets_friendly_and_hostile_multipliers():
    grid = GridManager()
    env = load_difficulty()["environment"]

    grid.apply_policy_environment(systemic=True)
    assert grid.environment_bias == "friendly"
    assert grid.obstacle_spawn_multiplier == env["friendly_obstacle_multiplier"]

    grid.apply_policy_environment(systemic=False)
    assert grid.environment_bias == "hostile"
    assert grid.obstacle_spawn_multiplier == env["hostile_obstacle_multiplier"]

    grid.reset_environment_bias()
    assert grid.environment_bias == "neutral"
    assert grid.obstacle_spawn_multiplier == 1.0


def test_hostile_bias_spawns_more_obstacles_than_friendly():
    """Same RNG seeds: hostile multiplier must place at least as many obstacles."""
    friendly_total = 0
    hostile_total = 0

    for seed in range(8):
        random.seed(seed)
        friendly = GridManager()
        friendly.reset()
        friendly.apply_policy_environment(systemic=True)
        before_f = len(friendly.obstacles)
        for _ in range(8):
            friendly._build_straight(10, mark_fork=False)
        friendly_total += len(friendly.obstacles) - before_f

        random.seed(seed)
        hostile = GridManager()
        hostile.reset()
        hostile.apply_policy_environment(systemic=False)
        before_h = len(hostile.obstacles)
        for _ in range(8):
            hostile._build_straight(10, mark_fork=False)
        hostile_total += len(hostile.obstacles) - before_h

    assert hostile_total >= friendly_total


def test_heart_pickups_spawn_when_chance_is_forced(monkeypatch):
    monkeypatch.setattr(GridManager, "_heart_pickup_spawn_chance", staticmethod(lambda: 1.0))
    monkeypatch.setattr(GridManager, "_scientific_item_spawn_chance", staticmethod(lambda: 0.0))

    grid = GridManager()
    grid.reset()
    grid.obstacles.clear()
    grid.gems.clear()
    grid.scientific_items.clear()
    grid.heart_pickups.clear()
    grid._seg_count = 1
    grid._base_obstacle_chance = 0.0
    # Keep RNG low enough that gem chance (0.4) fails, heart chance (1.0) succeeds.
    monkeypatch.setattr(random, "random", lambda: 0.5)

    grid._build_straight(6, mark_fork=False)

    assert grid.heart_pickups
    assert all(pos in grid.path_set or pos in grid.path for pos in grid.heart_pickups)

    grid.heart_pickups.clear()
    assert not grid.heart_pickups


def test_scientific_and_heart_collections_are_distinct_containers():
    grid = GridManager()
    assert isinstance(grid.scientific_items, dict)
    assert isinstance(grid.heart_pickups, set)
    for value in grid.scientific_items.values():
        assert value in ItemType
