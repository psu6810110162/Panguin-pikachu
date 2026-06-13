"""F12 screenshot hook for capturing report figures during development.

Enabled only when ``ENABLE_REPORT_CAPTURE=1`` is set in the environment so
production builds stay free of debug bindings.
"""
import os
import time

from kivy.core.window import Keyboard, Window

from core.logger import logger

# Resolve from Kivy's keycode table; fall back to the documented value.
F12_KEYCODE = Keyboard.keycodes.get('f12', 293)

_CAPTURE_DIR = os.path.join('assets', 'report_figures', 'captures')


def _on_key_down(window, key, *_):
    if key != F12_KEYCODE:
        return False
    try:
        os.makedirs(_CAPTURE_DIR, exist_ok=True)
        fname = os.path.join(_CAPTURE_DIR, f'capture_{time.strftime("%H%M%S")}.png')
        window.screenshot(name=fname)
        logger.info(f'capture saved: {fname}')
    except Exception as exc:
        logger.warning(f'capture failed: {exc}')
    return True


def register_capture():
    Window.bind(on_key_down=_on_key_down)
