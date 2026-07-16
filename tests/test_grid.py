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


def test_reset_is_idempotent():
    grid = GridManager()
    grid.reset()
    grid.forward_tiles = 12
    grid._boss_wave = 2
    grid.next_zone = 7
    grid.reset()

    assert grid.forward_tiles == 0
    assert grid._boss_wave == 0
    assert grid.next_zone in (1, 2)


def test_step_forward_and_distance():
    grid = GridManager()
    grid.reset()

    assert grid.get_distance_m() == 0
    for _ in range(5):
        grid.step_forward()
    assert grid.get_distance_m() == 5


def test_tile_trigger_time_is_slow_early_and_accelerates_late():
    grid = GridManager()

    early = grid.trigger_seconds_for_distance(0)
    middle = grid.trigger_seconds_for_distance(500)
    late = grid.trigger_seconds_for_distance(1000)

    assert early >= 2.5
    assert early > middle > late
    assert late <= 0.65


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


def test_repair_path_ahead_of_checkpoint_restores_destroyed_tiles():
    """Regression: update_tiles decays a tile's trigger_timer globally once
    triggered, regardless of whether the player is still standing on it — so
    a stretch the player walked before dying can fully melt away while they
    wait to respawn. Without a repair step, respawning back at the checkpoint
    then walking forward immediately falls off the (now-missing) path again."""
    grid = GridManager()
    grid.reset()

    checkpoint = grid.path[0]
    stretch = grid.path[1:10]
    for pos in stretch:
        tile = grid.path_set[pos]
        tile.state = "falling"
        tile.offset_y = -2000  # past the destroy threshold
    for pos in stretch:
        grid.path_set.pop(pos, None)

    for pos in stretch:
        assert not grid.is_on_path(*pos)

    grid.repair_path_ahead_of_checkpoint(*checkpoint)

    for pos in stretch:
        assert grid.is_on_path(*pos)
        assert grid.path_set[pos].state == "normal"


def test_repair_path_ahead_of_checkpoint_resets_triggered_tiles_without_removing_them():
    grid = GridManager()
    grid.reset()

    checkpoint = grid.path[0]
    pos = grid.path[3]
    tile = grid.path_set[pos]
    tile.state = "triggered"
    tile.trigger_timer = 0.1

    grid.repair_path_ahead_of_checkpoint(*checkpoint)

    assert grid.path_set[pos].state == "normal"
    assert grid.path_set[pos].trigger_timer == grid.trigger_seconds_for_distance()
