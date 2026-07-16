from core.asset_contract import BOSS_REVIEW_SHEET, DRONE_REVIEW_SHEET, ENVIRONMENT_TILE_ATLAS


def test_boss_review_sheet_has_stable_named_cells():
    assert BOSS_REVIEW_SHEET.cell_origin("wave_1_red_pulse") == (1024, 512)
    assert BOSS_REVIEW_SHEET.cell_origin("wave_2_methane_heat") == (0, 0)
    assert BOSS_REVIEW_SHEET.cell_origin("wave_3_overheat") == (512, 0)


def test_unknown_frame_is_rejected():
    try:
        BOSS_REVIEW_SHEET.cell_origin("not-a-frame")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown frame names must not silently crop the atlas")


def test_environment_atlas_keeps_named_variant_order():
    assert ENVIRONMENT_TILE_ATLAS.cell_origin("cool_moss_ice") == (0, 512)
    assert ENVIRONMENT_TILE_ATLAS.cell_origin("boss_safe") == (1024, 0)


def test_drone_contract_covers_all_support_states():
    assert DRONE_REVIEW_SHEET.cell_origin("warning") == (0, 0)
    assert DRONE_REVIEW_SHEET.cell_origin("report_celebration") == (627, 0)
