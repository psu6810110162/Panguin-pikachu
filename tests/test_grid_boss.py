from collections import deque

from game.grid import GridManager

FORWARD_MOVES = ((1, 0), (0, 1))


def _grid_with_boss_waves():
    grid = GridManager()
    grid.reset()
    for wave in range(3):
        grid._build_boss_wave(wave)
    return grid


def _reachable_from(grid, start):
    seen = {start}
    queue = deque([start])
    while queue:
        col, row = queue.popleft()
        for dc, dr in FORWARD_MOVES:
            candidate = (col + dc, row + dr)
            if candidate in grid.path_set and candidate not in seen:
                seen.add(candidate)
                queue.append(candidate)
    return seen


def test_boss_items_reachable_with_forward_only_moves():
    grid = _grid_with_boss_waves()
    reachable = _reachable_from(grid, grid.path[0])

    assert set(grid.boss_items) <= reachable
    assert set(grid.merge_points[-3:]) <= reachable


def test_no_dead_end_from_any_meaningful_boss_tile():
    grid = _grid_with_boss_waves()
    end = grid._last_pos

    for pos in [*grid.boss_items, *grid.merge_points[-3:]]:
        assert end in _reachable_from(grid, pos)


def test_reset_twice_still_places_boss_items():
    grid = GridManager()
    for _ in range(2):
        grid.reset()
        for wave in range(3):
            grid._build_boss_wave(wave)
        assert len(grid.boss_items) == 6
        assert grid._boss_wave == 0


def test_boss_placement_has_wave_and_one_choice_per_side():
    grid = _grid_with_boss_waves()

    for wave in range(1, 4):
        placements = [placement for placement in grid.boss_items.values() if placement.wave == wave]
        assert {placement.side for placement in placements} == {"left", "right"}
        assert len({placement.item_id for placement in placements}) == 2


def test_pop_boss_wave_removes_only_its_two_choices():
    grid = _grid_with_boss_waves()
    grid.pop_boss_wave(2)

    assert {placement.wave for placement in grid.boss_items.values()} == {1, 3}
    assert len(grid.boss_items) == 4
