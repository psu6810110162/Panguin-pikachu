from core import config


def test_window_dimensions_are_positive():
    assert config.WINDOW_WIDTH > 0
    assert config.WINDOW_HEIGHT > 0


def test_grid_dimensions_are_positive():
    assert config.GRID_WIDTH > 0
    assert config.GRID_HEIGHT > 0
    assert config.TILE_SIZE > 0
    assert config.TILE_TO_METER > 0


def test_speed_curve_is_sane():
    assert config.INITIAL_SPEED > 0
    assert config.SPEED_MULTIPLIER > 1.0
    assert config.MAX_SPEED > config.INITIAL_SPEED


def test_revive_cost_is_positive():
    assert config.REVIVE_COST_GEM > 0
