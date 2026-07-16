"""Versioned contracts for generated raster assets.

Gameplay owns when an asset is shown; this module owns the immutable geometry and
frame names needed to crop a review sheet without scattering magic coordinates in
the renderer.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpriteSheetContract:
    """Describe a regular sprite atlas in texture coordinates.

    Kivy texture origins are bottom-left, so ``cell_origin`` returns coordinates
    in that convention. Names are intentionally explicit: changing frame order is
    an asset migration, not an invisible renderer tweak.
    """

    frame_width: int
    frame_height: int
    columns: int
    rows: int
    frame_names: tuple[str, ...]

    def cell_origin(self, frame_name: str) -> tuple[int, int]:
        index = self.frame_names.index(frame_name)
        column = index % self.columns
        row_from_top = index // self.columns
        row_from_bottom = self.rows - 1 - row_from_top
        return column * self.frame_width, row_from_bottom * self.frame_height


BOSS_REVIEW_SHEET = SpriteSheetContract(
    frame_width=512,
    frame_height=512,
    columns=3,
    rows=2,
    frame_names=(
        "idle_hover",
        "warning_smoke",
        "wave_1_red_pulse",
        "wave_2_methane_heat",
        "wave_3_overheat",
        "defeated_shutdown",
    ),
)

ENVIRONMENT_TILE_ATLAS = SpriteSheetContract(
    frame_width=512,
    frame_height=512,
    columns=3,
    rows=2,
    frame_names=(
        "cool_moss_ice",
        "frozen_ice",
        "neon_pivot",
        "amber_warning",
        "thawed_smog",
        "boss_safe",
    ),
)

DRONE_REVIEW_SHEET = SpriteSheetContract(
    frame_width=627,
    frame_height=627,
    columns=2,
    rows=2,
    frame_names=("idle_hover", "point_forward", "warning", "report_celebration"),
)
