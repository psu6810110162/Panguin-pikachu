"""Responsive breakpoint calculator + safe-area provider for Kivy screens.

Screens query this module instead of hardcoding pixel thresholds, so the same
breakpoints are used — and unit-tested (see ``tests/test_responsive.py``) —
everywhere a layout needs to reflow between phone/tablet/desktop.

Everything except :class:`SafeAreaProvider`'s Android bridge is pure Python
with no live ``Window``/GL context required, so it is safe to import and
exercise in this project's headless test environment (``kivy.utils.platform``
is a plain OS-detection string constant, not a Window/GL call).

Scope note: this project currently targets Kivy desktop builds (see
``main.py``); widths/heights passed in here are the raw ``Window.width`` /
``Window.height`` pixel values already used everywhere else in the codebase,
treated as the "dp" unit for breakpoint purposes. A full ``kivy.metrics.dp``
migration (converting every hardcoded pixel constant in ``screens/`` to
density-independent units) is a larger, separate change and out of scope
here — see docs/adr for the corresponding note.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Breakpoint(Enum):
    MOBILE_PORTRAIT = "mobile_portrait"
    MOBILE_LANDSCAPE = "mobile_landscape"
    TABLET = "tablet"
    DESKTOP = "desktop"


# Thresholds are on the *narrow* (shorter) axis: that is what actually forces
# a HUD to reflow, regardless of whether the device is held in portrait or
# landscape. The long axis only decides portrait vs. landscape once we're
# already in the mobile bucket.
MOBILE_MAX_DP = 480.0
TABLET_MAX_DP = 1023.0

MIN_TOUCH_TARGET_DP = 48.0
MIN_SAFE_PADDING_DP = 12.0

# Baseline size_hint_x for the HUD rail on non-compact breakpoints; on
# compact breakpoints it grows to use more of the (narrower) available width.
_HUD_WIDTH_FRACTION_WIDE = 0.80
_HUD_WIDTH_FRACTION_COMPACT = 0.94

# Baseline control (arrow button / pause / help) edge length in dp before
# breakpoint scaling and the MIN_TOUCH_TARGET_DP floor are applied.
_BASE_CONTROL_SIZE_DP = 120.0

_HUD_SCALE_BY_BREAKPOINT = {
    Breakpoint.DESKTOP: 1.0,
    Breakpoint.TABLET: 0.9,
    Breakpoint.MOBILE_LANDSCAPE: 0.8,
    Breakpoint.MOBILE_PORTRAIT: 0.72,
}


def classify_breakpoint(width_dp: float, height_dp: float) -> Breakpoint:
    narrow = min(width_dp, height_dp)
    if narrow > TABLET_MAX_DP:
        return Breakpoint.DESKTOP
    if narrow > MOBILE_MAX_DP:
        return Breakpoint.TABLET
    return Breakpoint.MOBILE_LANDSCAPE if width_dp > height_dp else Breakpoint.MOBILE_PORTRAIT


def is_compact(breakpoint: Breakpoint) -> bool:
    """True when the HUD/controls must use the compact (mobile) layout."""
    return breakpoint in (Breakpoint.MOBILE_PORTRAIT, Breakpoint.MOBILE_LANDSCAPE)


def hud_scale(breakpoint: Breakpoint) -> float:
    """Multiplier applied to HUD rail height / font sizes for this breakpoint."""
    return _HUD_SCALE_BY_BREAKPOINT[breakpoint]


def grid_columns(available_width_dp: float, *, min_cell_width_dp: float, spacing_dp: float) -> int:
    """How many equal-width ``min_cell_width_dp``+ columns fit ``available_width_dp``.

    Used by any responsive card grid (currently the Shop) to decide 2 columns
    vs. 1 instead of a screen hardcoding the same "does N columns fit"
    arithmetic itself. Always returns at least 1 — an available width smaller
    than a single cell still renders one (possibly clipped-on-a-tiny-screen)
    column rather than zero.
    """
    if available_width_dp <= 0:
        return 1
    columns = 1
    while True:
        candidate = columns + 1
        needed = candidate * min_cell_width_dp + (candidate - 1) * spacing_dp
        if needed > available_width_dp:
            return columns
        columns = candidate


@dataclass(frozen=True)
class SafeAreaInsets:
    top: float = 0.0
    bottom: float = 0.0
    left: float = 0.0
    right: float = 0.0


class SafeAreaProvider:
    """Resolves safe-area insets for the current platform/breakpoint.

    - Desktop/tablet windowed apps are never drawn over by a system bar or
      cutout, so insets are always zero there.
    - Android exposes real cutout/system-bar insets through a Java bridge.
      The import is guarded so this module (and the test suite) never
      requires ``pyjnius`` to be installed on desktop/CI.
    - Any platform where the bridge is unavailable — including a real
      Android device before the bridge call succeeds — falls back to a
      minimum safe padding, applied only on the compact breakpoints where an
      OS overlay is actually plausible.
    """

    @staticmethod
    def current(breakpoint: Breakpoint) -> SafeAreaInsets:
        from kivy.utils import platform

        if platform == "android":
            android_insets = SafeAreaProvider._read_android_insets()
            if android_insets is not None:
                return android_insets
            if is_compact(breakpoint):
                return SafeAreaInsets(
                    top=MIN_SAFE_PADDING_DP,
                    bottom=MIN_SAFE_PADDING_DP,
                    left=MIN_SAFE_PADDING_DP,
                    right=MIN_SAFE_PADDING_DP,
                )
        return SafeAreaInsets()

    @staticmethod
    def _read_android_insets() -> SafeAreaInsets | None:
        try:
            from jnius import autoclass  # type: ignore[import-not-found]
        except ImportError:
            return None
        try:
            python_activity = autoclass("org.kivy.android.PythonActivity")
            activity = python_activity.mActivity
            decor_view = activity.getWindow().getDecorView()
            window_insets = decor_view.getRootWindowInsets()
            if window_insets is None:
                return None
            density = activity.getResources().getDisplayMetrics().density
            return SafeAreaInsets(
                top=window_insets.getSystemWindowInsetTop() / density,
                bottom=window_insets.getSystemWindowInsetBottom() / density,
                left=window_insets.getSystemWindowInsetLeft() / density,
                right=window_insets.getSystemWindowInsetRight() / density,
            )
        except Exception:
            # Any bridge failure (no activity yet, older API without the
            # method, ...) degrades to the minimum-padding fallback above —
            # never crash layout because a platform API was unavailable.
            return None


@dataclass(frozen=True)
class ResponsiveLayout:
    breakpoint: Breakpoint
    scale: float
    hud_width_fraction: float
    control_size_dp: float
    safe_area: SafeAreaInsets


def compute_layout(width_dp: float, height_dp: float) -> ResponsiveLayout:
    """Pure layout-metrics calculator — see tests/test_responsive.py.

    Returns the breakpoint plus every derived value screens need
    (HUD scale, HUD width fraction, control edge length, safe-area insets)
    so a caller never re-derives these independently and drifts.
    """
    breakpoint = classify_breakpoint(width_dp, height_dp)
    scale = hud_scale(breakpoint)
    safe_area = SafeAreaProvider.current(breakpoint)

    horizontal_inset_fraction = (
        (safe_area.left + safe_area.right) / width_dp if width_dp > 0 else 0.0
    )
    available_fraction = max(0.0, 1.0 - horizontal_inset_fraction)
    base_fraction = (
        _HUD_WIDTH_FRACTION_COMPACT if is_compact(breakpoint) else (_HUD_WIDTH_FRACTION_WIDE)
    )
    hud_width_fraction = min(base_fraction, available_fraction)

    control_size_dp = max(MIN_TOUCH_TARGET_DP, _BASE_CONTROL_SIZE_DP * scale)

    return ResponsiveLayout(
        breakpoint=breakpoint,
        scale=scale,
        hud_width_fraction=hud_width_fraction,
        control_size_dp=control_size_dp,
        safe_area=safe_area,
    )
