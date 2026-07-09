from game.grid import VISIBLE_BUFFER, GridManager


def test_to_isometric_origin_maps_to_origin():
    assert GridManager.to_isometric(0, 0, 130, 65) == (0, 0)


def test_to_isometric_matches_formula():
    x, y = GridManager.to_isometric(3, 1, 130, 65)
    assert x == (3 - 1) * (130 / 2)
    assert y == (3 + 1) * (65 / 2)


def test_reset_builds_start_platform_and_preloads_segments():
    grid = GridManager()
    grid.reset()

    assert grid.forward_tiles == 0
    assert len(grid.path) > 0
    assert len(grid.path_set) > 0
    # start platform always includes the origin tile
    assert (0, 0) in grid.path_set


def test_step_forward_and_distance():
    grid = GridManager()
    grid.reset()

    assert grid.get_distance_m() == 0
    for _ in range(5):
        grid.step_forward()
    assert grid.get_distance_m() == 5


def test_is_on_path_reflects_path_set():
    grid = GridManager()
    grid.reset()

    assert grid.is_on_path(0, 0) is True
    assert grid.is_on_path(9999, 9999) is False


def test_get_path_index_returns_minus_one_when_missing():
    grid = GridManager()
    grid.reset()

    assert grid.get_path_index(9999, 9999) == -1
    assert grid.get_path_index(*grid.path[0]) == 0


def test_extend_if_needed_grows_the_path_when_close_to_the_end():
    grid = GridManager()
    grid.reset()

    length_before = len(grid.path)
    grid.extend_if_needed(length_before - 1)
    assert len(grid.path) > length_before


def test_extend_if_needed_does_nothing_once_buffer_is_satisfied():
    grid = GridManager()
    grid.reset()

    # keep extending until the visible buffer ahead of index 0 is filled
    while len(grid.path) < VISIBLE_BUFFER:
        grid.extend_if_needed(0)

    length_before = len(grid.path)
    grid.extend_if_needed(0)
    assert len(grid.path) == length_before


def test_remove_tile_drops_tile_and_its_occupants():
    grid = GridManager()
    grid.reset()

    pos = grid.path[0]
    assert pos in grid.path_set

    grid.remove_tile(*pos)

    assert pos not in grid.path_set
    assert pos not in grid.obstacles
    assert pos not in grid.gems


def test_remove_tile_is_a_no_op_for_a_missing_tile():
    grid = GridManager()
    grid.reset()

    # should not raise even though (9999, 9999) was never added
    grid.remove_tile(9999, 9999)


def test_cleanup_behind_removes_stale_obstacles_and_gems():
    grid = GridManager()
    grid.reset()

    # force some objects onto the very first tiles so cleanup has something to remove
    pos = grid.path[0]
    grid.obstacles[pos] = object()
    grid.gems[pos] = object()

    grid.cleanup_behind(30)

    assert pos not in grid.obstacles
    assert pos not in grid.gems
