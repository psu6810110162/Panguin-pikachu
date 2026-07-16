from unittest.mock import patch

from core.items import ItemType
from game.grid import GridManager


def test_scientific_items_spawn_on_centreline_and_reset_clears_them():
    grid = GridManager()
    grid.reset()
    grid._scientific_item_spawn_chance = lambda: 1.0
    # Make the spawn assertion deterministic: preloaded segments may contain
    # random obstacle/gem placements that otherwise occupy every new tile.
    grid.obstacles.clear()
    grid.gems.clear()
    # 0.99 blocks obstacle/gem rolls (< 0.2/< 0.4) but succeeds for the
    # forced scientific-item chance (1.0).
    with patch("game.grid.random.random", return_value=0.99):
        grid._build_straight(3)

    assert grid.scientific_items
    assert set(grid.scientific_items) <= set(grid.path)
    assert set(grid.scientific_items.values()) <= set(ItemType)
    # Disable spawning before reset so this assertion proves stale items were
    # cleared, rather than observing a freshly spawned item on the new path.
    grid._scientific_item_spawn_chance = lambda: 0.0
    grid.reset()
    assert not grid.scientific_items
