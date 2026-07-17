"""Regression: gameplay keyboard must survive FocusableIconButton focus.

FocusBehavior in ``auto`` mode steals ``Window.request_keyboard`` on click,
which used to leave GamePlayScreen with ``_keyboard is None`` and no
left/right movement until the next ``on_enter``. These tests pin the two
defenses from the gameplay-loop plan: managed keyboard mode on icon buttons,
and rebind-after-steal on the screen itself.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from ui.components import FocusableIconButton


def test_focusable_icon_button_defaults_to_managed_keyboard_mode():
    """Managed mode must be the constructor default so Pause/Help never
    auto-call ``request_keyboard`` and release GamePlayScreen's bindings."""
    import inspect

    source = inspect.getsource(FocusableIconButton.__init__)
    assert 'setdefault("keyboard_mode", "managed")' in source


def test_keyboard_closed_rebinding_when_still_wanted():
    """Unbound call of GamePlayScreen._keyboard_closed must schedule a rebind
    when ``_keyboard_wanted`` is True — the steal-recovery path."""
    from screens.gameplay import GamePlayScreen

    scheduled: list = []
    fake_keyboard = MagicMock()
    fake = SimpleNamespace(
        _keyboard=fake_keyboard,
        _keyboard_wanted=True,
        _on_keyboard_down=lambda *a: None,
        _on_keyboard_up=lambda *a: None,
        _bind_gameplay_keyboard=MagicMock(),
    )

    # Patch Clock.schedule_once used inside the unbound method via the module.
    import screens.gameplay as gameplay_mod

    original = gameplay_mod.Clock.schedule_once

    def _capture(callback, timeout=0):
        scheduled.append((callback, timeout))
        return MagicMock()

    gameplay_mod.Clock.schedule_once = _capture
    try:
        GamePlayScreen._keyboard_closed(fake)
    finally:
        gameplay_mod.Clock.schedule_once = original

    assert fake._keyboard is None
    fake_keyboard.unbind.assert_called()
    assert len(scheduled) == 1
    callback, timeout = scheduled[0]
    assert timeout == 0
    callback(0)
    fake._bind_gameplay_keyboard.assert_called_once()


def test_keyboard_closed_does_not_rebind_after_leave():
    from screens.gameplay import GamePlayScreen

    scheduled: list = []
    fake = SimpleNamespace(
        _keyboard=None,
        _keyboard_wanted=False,
        _bind_gameplay_keyboard=MagicMock(),
    )
    import screens.gameplay as gameplay_mod

    original = gameplay_mod.Clock.schedule_once

    def _capture(callback, timeout=0):
        scheduled.append(callback)
        return MagicMock()

    gameplay_mod.Clock.schedule_once = _capture
    try:
        GamePlayScreen._keyboard_closed(fake)
    finally:
        gameplay_mod.Clock.schedule_once = original

    assert scheduled == []
    fake._bind_gameplay_keyboard.assert_not_called()
