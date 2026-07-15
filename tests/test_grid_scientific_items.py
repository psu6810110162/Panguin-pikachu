from core.items import ItemType
from game.grid import GridManager


def test_scientific_items_spawn_on_centreline_and_reset_clears_them():
    grid = GridManager()
    grid.reset()
    grid._scientific_item_spawn_chance = lambda: 1.0
    grid._build_straight(3)

    assert grid.scientific_items
    assert set(grid.scientific_items) <= set(grid.path)
    assert set(grid.scientific_items.values()) <= set(ItemType)
    grid.reset()
    assert not any(pos not in grid.path_set for pos in grid.scientific_items)
