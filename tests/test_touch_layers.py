"""Kivy touch-dispatch contract for full-screen decorative/modal overlays.

``kivy.uix.widget.Widget.on_touch_down`` consumes any touch colliding with a
``disabled`` widget regardless of ``opacity``. A full-screen widget built with
plain ``disabled=True`` therefore silently swallows every touch on screen —
including buttons added earlier in the tree — even while invisible. This is
exactly what happened to the Pause/How to Play buttons in
``screens/gameplay.py`` (blocked by ``decision_dim``/``respawn_overlay``, both
full-screen and ``disabled=True`` by default).

These tests pin the fix so it cannot regress silently: a hidden/passive
full-screen overlay must return ``False`` from every touch handler, gating on
an explicit active flag (``opacity`` / ``is_open``) instead of ``disabled``.

The methods are called unbound against a lightweight stand-in object instead
of a constructed widget: constructing real Kivy widgets needs a live Window
provider, which this headless test environment does not have (see
``tests/test_smoke.py`` for the same constraint). The "hidden -> False"
branches below never touch ``super()``/GL state, so they are safe to exercise
this way; the "active -> consumes" branches still depend on real widget
dispatch and are covered by manual verification (Task 9 matrix) instead.
"""

from types import SimpleNamespace

from ui.components import PassiveOverlay, StateOverlay
from ui.how_to_play_overlay import HowToPlayOverlay


def _touch_at(x: float, y: float) -> SimpleNamespace:
    return SimpleNamespace(pos=(x, y))


def test_passive_overlay_never_consumes_touch_even_when_disabled():
    fake = SimpleNamespace(disabled=True, opacity=0)
    touch = _touch_at(400, 300)

    assert PassiveOverlay.on_touch_down(fake, touch) is False
    assert PassiveOverlay.on_touch_move(fake, touch) is False
    assert PassiveOverlay.on_touch_up(fake, touch) is False


def test_passive_overlay_never_consumes_touch_when_visible():
    fake = SimpleNamespace(disabled=False, opacity=1)

    assert PassiveOverlay.on_touch_down(fake, _touch_at(1, 1)) is False


def test_hidden_state_overlay_does_not_block_touch_regardless_of_disabled():
    touch = _touch_at(400, 300)
    for disabled in (True, False):
        fake = SimpleNamespace(opacity=0, disabled=disabled)
        assert StateOverlay.on_touch_down(fake, touch) is False
        assert StateOverlay.on_touch_move(fake, touch) is False
        assert StateOverlay.on_touch_up(fake, touch) is False


def test_hidden_how_to_play_overlay_does_not_block_touch():
    fake = SimpleNamespace(is_open=False)
    touch = _touch_at(400, 300)

    assert HowToPlayOverlay.on_touch_down(fake, touch) is False
    assert HowToPlayOverlay.on_touch_move(fake, touch) is False
    assert HowToPlayOverlay.on_touch_up(fake, touch) is False
