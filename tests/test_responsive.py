from ui.responsive import (
    MIN_TOUCH_TARGET_DP,
    Breakpoint,
    classify_breakpoint,
    compute_layout,
    grid_columns,
    is_compact,
)

# Desktop, small-laptop desktop, tablet landscape, small window, mobile
# portrait, mobile landscape — the exact resolution matrix called out in the
# plan.
RESOLUTIONS = [
    (1920, 1080),
    (1280, 800),
    (1024, 768),
    (800, 600),
    (390, 844),
    (844, 390),
]


def test_classify_breakpoint_is_deterministic_and_orientation_aware():
    assert classify_breakpoint(1920, 1080) is Breakpoint.DESKTOP
    assert classify_breakpoint(390, 844) is Breakpoint.MOBILE_PORTRAIT
    assert classify_breakpoint(844, 390) is Breakpoint.MOBILE_LANDSCAPE
    # Same physical size, only orientation flipped -> only portrait/landscape
    # differs, never a different bucket entirely.
    assert is_compact(classify_breakpoint(390, 844))
    assert is_compact(classify_breakpoint(844, 390))


def test_classify_breakpoint_uses_narrow_axis_not_raw_width():
    # A very wide but short window (e.g. an ultra-thin browser strip) must
    # still be treated as compact — width alone would wrongly call this
    # "desktop".
    assert classify_breakpoint(2000, 300) in (
        Breakpoint.MOBILE_LANDSCAPE,
        Breakpoint.MOBILE_PORTRAIT,
    )


def test_every_resolution_in_matrix_has_no_horizontal_overflow():
    for width, height in RESOLUTIONS:
        layout = compute_layout(width, height)
        hud_pixel_width = layout.hud_width_fraction * width
        total_with_safe_area = hud_pixel_width + layout.safe_area.left + layout.safe_area.right
        assert 0 < layout.hud_width_fraction <= 1.0
        assert total_with_safe_area <= width + 1e-6, (width, height, layout)


def test_every_resolution_in_matrix_has_non_negative_finite_bounds():
    for width, height in RESOLUTIONS:
        layout = compute_layout(width, height)
        assert layout.hud_width_fraction > 0
        assert layout.control_size_dp > 0
        assert layout.safe_area.top >= 0
        assert layout.safe_area.bottom >= 0
        assert layout.safe_area.left >= 0
        assert layout.safe_area.right >= 0


def test_every_resolution_in_matrix_meets_minimum_touch_target():
    for width, height in RESOLUTIONS:
        layout = compute_layout(width, height)
        assert layout.control_size_dp >= MIN_TOUCH_TARGET_DP, (width, height, layout)


def test_desktop_breakpoint_has_zero_safe_area():
    layout = compute_layout(1920, 1080)
    assert layout.breakpoint is Breakpoint.DESKTOP
    assert layout.safe_area.top == 0
    assert layout.safe_area.bottom == 0
    assert layout.safe_area.left == 0
    assert layout.safe_area.right == 0


def test_desktop_uses_wider_hud_fraction_than_compact_breakpoints():
    desktop_layout = compute_layout(1920, 1080)
    mobile_layout = compute_layout(390, 844)
    assert is_compact(mobile_layout.breakpoint)
    # Compact breakpoints intentionally use *more* of the narrow width for
    # the HUD rail (there's no room to spare), not less.
    assert mobile_layout.hud_width_fraction >= desktop_layout.hud_width_fraction


def test_compact_breakpoints_scale_down_controls_but_stay_above_floor():
    desktop_layout = compute_layout(1920, 1080)
    mobile_layout = compute_layout(390, 844)
    assert mobile_layout.control_size_dp < desktop_layout.control_size_dp
    assert mobile_layout.control_size_dp >= MIN_TOUCH_TARGET_DP


def test_grid_columns_fits_two_when_width_allows():
    assert grid_columns(600, min_cell_width_dp=240, spacing_dp=20) == 2


def test_grid_columns_falls_back_to_one_on_narrow_width():
    assert grid_columns(390, min_cell_width_dp=240, spacing_dp=20) == 1


def test_grid_columns_accounts_for_spacing_between_columns_not_just_cell_width():
    # Exactly two cell-widths with no room left for the spacing between them
    # must not report 2 columns.
    assert grid_columns(480, min_cell_width_dp=240, spacing_dp=20) == 1
    assert grid_columns(500, min_cell_width_dp=240, spacing_dp=20) == 2


def test_grid_columns_never_returns_less_than_one():
    assert grid_columns(0, min_cell_width_dp=240, spacing_dp=20) == 1
    assert grid_columns(-100, min_cell_width_dp=240, spacing_dp=20) == 1
