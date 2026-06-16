"""Smoke tests — importable modules should not raise.

We deliberately avoid importing ``main`` directly because it has side
effects (creates a window, binds keyboard). Use ``find_spec`` to confirm
it resolves, and import only pure-logic modules.
"""
import importlib.util


def test_main_entrypoint_resolves():
    assert importlib.util.find_spec('main') is not None


def test_import_core_modules():
    from core import audio, config, database, i18n, logger, state  # noqa: F401


def test_import_game_logic():
    from game import buffs, chaser, grid, quiz_manager  # noqa: F401
