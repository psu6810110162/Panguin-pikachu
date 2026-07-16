from core.items import ItemType
from game.grid import GridManager


def test_scientific_items_spawn_on_centreline_and_reset_clears_them(monkeypatch):
    grid = GridManager()
    grid.reset()
    grid.scientific_items.clear()
    grid._scientific_item_spawn_chance = lambda: 1.0
    grid._last_pos = (10_000, 10_000)
    grid._last_dir = grid.DIR_A
    grid._seg_count = 1
    grid.obstacles.clear()
    grid.gems.clear()
    monkeypatch.setattr("game.grid.random.random", lambda: 0.99)
    grid._build_straight(3)

    assert grid.scientific_items
    assert set(grid.scientific_items) <= set(grid.path)
    assert set(grid.scientific_items.values()) <= set(ItemType)
    # Disable spawning before reset so this assertion proves stale items were
    # cleared, rather than observing a freshly spawned item on the new path.
    grid._scientific_item_spawn_chance = lambda: 0.0
    grid.reset()
    assert not grid.scientific_items


def test_objects_do_not_spawn_when_straight_overlaps_non_center_fork_tile(monkeypatch):
    grid = GridManager()
    grid.reset()
    grid.scientific_items.clear()
    grid.obstacles.clear()
    grid.gems.clear()
    grid._last_pos = (20_000, 20_000)
    grid._last_dir = grid.DIR_A
    grid._seg_count = 1
    overlap = (20_001, 20_000)
    grid._add_tile(*overlap, is_fork=True)
    grid._scientific_item_spawn_chance = lambda: 1.0
    monkeypatch.setattr("game.grid.random.random", lambda: 0.99)

    grid._build_straight(1)

    assert overlap not in grid.path
    assert overlap not in grid.scientific_items
