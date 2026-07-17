"""State-machine contract for ``HowToPlayOverlay.open``/``close``.

Constructing a real overlay needs a live Kivy Window (unavailable in this
headless test environment — see ``tests/test_smoke.py``), so these tests call
the unbound methods against a minimal stand-in object instead. Both methods
only touch attributes/methods on ``self`` — no ``super()`` — so this is safe.
"""

from types import SimpleNamespace

from ui.how_to_play_overlay import HowToPlayOverlay


class _FakePager:
    def __init__(self):
        self.gone_to = []

    def go_to(self, index):
        self.gone_to.append(index)


def _fake_overlay(is_open: bool, on_close_callback=None) -> SimpleNamespace:
    render_calls = []
    fake = SimpleNamespace(
        is_open=is_open,
        pager=_FakePager(),
        opacity=1 if is_open else 0,
        disabled=not is_open,
        on_close_callback=on_close_callback,
        render_calls=render_calls,
    )
    fake._render_page = lambda: render_calls.append(1)
    return fake


def test_open_is_idempotent_when_already_open():
    fake = _fake_overlay(is_open=True)

    HowToPlayOverlay.open(fake, 3)

    # Already-open modal must not reset the reader's current page.
    assert fake.pager.gone_to == []
    assert fake.render_calls == []


def test_open_when_closed_activates_and_jumps_to_page():
    fake = _fake_overlay(is_open=False)

    HowToPlayOverlay.open(fake, 2)

    assert fake.pager.gone_to == [2]
    assert fake.is_open is True
    assert fake.opacity == 1
    assert fake.disabled is False
    assert fake.render_calls == [1]


def test_close_is_idempotent_when_already_closed():
    calls = []
    fake = _fake_overlay(is_open=False, on_close_callback=lambda: calls.append(1))

    HowToPlayOverlay.close(fake)

    assert calls == []


def test_close_when_open_deactivates_and_fires_callback_once():
    calls = []
    fake = _fake_overlay(is_open=True, on_close_callback=lambda: calls.append(1))

    HowToPlayOverlay.close(fake)

    assert fake.is_open is False
    assert fake.opacity == 0
    assert fake.disabled is True
    assert calls == [1]
