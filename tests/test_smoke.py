import importlib
import pkgutil

import core
import game

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
