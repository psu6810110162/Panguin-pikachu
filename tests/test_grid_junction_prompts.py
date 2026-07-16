from core.interaction import junction_prompt_text
from core.junction_data import all_junctions, get_junction
from game.grid import GridManager


def _grid_with_all_zones():
    grid = GridManager()
    grid.reset()
    while grid.next_zone <= grid.spawning_system.NUM_ZONES:
        grid._append_segment()
    return grid


def test_prompt_tiles_precede_each_commit_tile_for_all_zones():
    grid = _grid_with_all_zones()
    commits = {
        tile.zone_id: pos
        for pos, tile in grid.path_set.items()
        if tile.zone_id is not None and grid.get_path_index(*pos) >= 0
    }

    assert set(commits) == set(range(1, 11))
    for zone, commit in commits.items():
        prompt_positions = {
            pos for pos, prompt_zone in grid.junction_prompts.items() if prompt_zone == zone
        }
        assert prompt_positions
        assert all(
            grid.get_path_index(pos[0], pos[1]) < grid.get_path_index(*commit)
            for pos in prompt_positions
        )


def test_prompt_reset_and_text_are_pure_policy_presentation():
    grid = _grid_with_all_zones()
    assert grid.junction_prompts
    grid.reset()
    assert set(grid.junction_prompts.values()) <= {1}

    for junction in all_junctions():
        text = junction_prompt_text(get_junction(junction.zone))
        assert junction.situation in text
        assert junction.left.label in text
        assert junction.right.label in text
        assert "Heat" in text
        assert "Anger" in text
        assert "systemic" not in text
