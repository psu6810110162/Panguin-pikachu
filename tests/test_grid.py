"""Unit tests for the procedural map generator (game/grid.py)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.grid import GridManager
from core.config import TILE_TO_METER


def test_reset_builds_initial_path():
    """reset() must produce a non-empty, preloaded path."""
    gm = GridManager()
    gm.reset()
    assert len(gm.path) > 0
    assert len(gm.path_set) > 0
    # start tile (1,1) must exist on the path
    assert gm.is_on_path(1, 1)


def test_distance_increases_with_steps():
    """get_distance_m must scale linearly with forward steps."""
    gm = GridManager()
    gm.reset()
    assert gm.get_distance_m() == 0
    gm.step_forward()
    gm.step_forward()
    assert gm.get_distance_m() == 2 * TILE_TO_METER


def test_obstacle_chance_is_monotonic_piecewise():
    """_obstacle_chance must follow the documented 5-band step function."""
    gm = GridManager()
    assert gm._obstacle_chance(5) == 0.00     # 0–15 safe zone
    assert gm._obstacle_chance(50) == 0.30    # 15–80
    assert gm._obstacle_chance(150) == 0.50   # 80–250
    assert gm._obstacle_chance(400) == 0.65   # 250–500
    assert gm._obstacle_chance(700) == 0.75   # 500+
    # must be non-decreasing
    samples = [gm._obstacle_chance(d) for d in range(0, 800, 25)]
    assert samples == sorted(samples)


def test_off_path_tile_is_detected_as_gap():
    """A coordinate far from any generated tile must read as a fall (not on path)."""
    gm = GridManager()
    gm.reset()
    assert gm.is_on_path(9999, 9999) is False


def test_extend_grows_path():
    """Walking near the end must extend the path with new tiles."""
    gm = GridManager()
    gm.reset()
    before = len(gm.path)
    gm._append_segment()
    assert len(gm.path) > before
