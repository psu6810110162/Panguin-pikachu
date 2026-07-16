"""Packaged, non-GUI release smoke test."""

import json
import os
import tempfile

from infrastructure.atomic import atomic_write_json
from infrastructure.database import DatabaseManager
from infrastructure.paths import USER_DATA_OVERRIDE, RuntimePaths
from infrastructure.resources import validate_resources
from infrastructure.version import load_build_info


def run_self_test() -> int:
    report = validate_resources()
    original_override = os.environ.get(USER_DATA_OVERRIDE)
    try:
        with tempfile.TemporaryDirectory(prefix="penguin-self-test-") as temporary:
            os.environ[USER_DATA_OVERRIDE] = temporary
            paths = RuntimePaths.discover().ensure()
            atomic_write_json(paths.settings / "self-test.json", {"ok": True})
            DatabaseManager.reset_for_tests()
            database = DatabaseManager(paths.data / "self-test.db")
            database.init_db()
            database.save_game_session("SelfTest", distance=1, gems=1)
            assert database.get_personal_best("SelfTest") == 1
            database.close()
    finally:
        DatabaseManager.reset_for_tests()
        if original_override is None:
            os.environ.pop(USER_DATA_OVERRIDE, None)
        else:
            os.environ[USER_DATA_OVERRIDE] = original_override

    print(
        json.dumps(
            {
                "ok": True,
                "resources_checked": report.checked,
                "pending_licenses": report.pending_licenses,
                "build": load_build_info(),
            },
            sort_keys=True,
        )
    )
    return 0
