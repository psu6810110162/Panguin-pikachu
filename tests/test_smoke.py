import importlib
import pkgutil

import core
import game
import screens

MODULES_TO_SKIP = set()


def _submodule_names(package):
    return [
        f"{package.__name__}.{info.name}"
        for info in pkgutil.iter_modules(package.__path__)
        if f"{package.__name__}.{info.name}" not in MODULES_TO_SKIP
    ]


def test_all_core_modules_import_cleanly():
    for name in _submodule_names(core):
        importlib.import_module(name)


def test_all_game_modules_import_cleanly():
    for name in _submodule_names(game):
        importlib.import_module(name)


def test_all_screens_modules_import_cleanly():
    # Import-only: instantiating a Screen (e.g. HoverButton's Window.bind in __init__)
    # needs a real windowed Kivy context that this headless test environment doesn't
    # have. Importing the module (class definitions only, no instantiation) is safe
    # and still catches syntax/import errors in screens/.
    for name in _submodule_names(screens):
        importlib.import_module(name)
