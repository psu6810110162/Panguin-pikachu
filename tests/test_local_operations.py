import json
import re
from pathlib import Path

import pytest

from infrastructure.atomic import atomic_write_json
from infrastructure.crash_report import write_crash_report
from infrastructure.paths import RuntimePaths, resource_path
from infrastructure.resources import (
    ResourceValidationError,
    load_resource_manifest,
    validate_resources,
)
from infrastructure.telemetry import TelemetryRecorder
from scripts.verify_client_bundle import verify_bundle


def test_runtime_paths_are_separate_from_bundle(monkeypatch, tmp_path):
    monkeypatch.setenv("PENGUIN_USER_DATA_DIR", str(tmp_path / "user"))
    paths = RuntimePaths.discover().ensure()
    assert paths.root == (tmp_path / "user").resolve()
    assert paths.root not in resource_path().parents
    assert all(path.is_dir() for path in (paths.data, paths.logs, paths.crash, paths.telemetry))


def test_atomic_json_replaces_complete_document(tmp_path):
    target = tmp_path / "settings" / "settings.json"
    atomic_write_json(target, {"version": 1})
    atomic_write_json(target, {"version": 2, "ok": True})
    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True, "version": 2}
    assert not target.with_name(".settings.json.tmp").exists()


def test_resource_manifest_validates_and_pending_licenses_block_ga():
    report = validate_resources()
    assert report.checked >= 47
    assert {"bgm-gameplay", "sfx-jump", "ui-button-flat", "gem-strip"} <= set(
        report.pending_licenses
    )
    with pytest.raises(ResourceValidationError, match="license review"):
        validate_resources(require_release_licenses=True)


def test_manifest_covers_every_literal_runtime_asset_reference():
    root = Path(__file__).resolve().parent.parent
    manifest_sources = {entry["source"] for entry in load_resource_manifest()["entries"]}
    pattern = re.compile(r"assets/[A-Za-z0-9_ ./-]+\.(?:jpeg|jpg|mp3|ogg|png|ttf|wav)")
    references = set()
    targets = (root / "style.kv", root / "core", root / "game", root / "screens", root / "ui")
    for target in targets:
        files = [target] if target.is_file() else target.rglob("*.py")
        for path in files:
            references.update(pattern.findall(path.read_text(encoding="utf-8")))

    assert references <= manifest_sources


def test_crash_report_is_written_atomically_without_player_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("PENGUIN_USER_DATA_DIR", str(tmp_path))
    report = write_crash_report(RuntimeError("boom"))
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["exception"]["type"] == "RuntimeError"
    assert "player_id" not in report.read_text(encoding="utf-8")


def test_telemetry_rejects_identifying_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("PENGUIN_USER_DATA_DIR", str(tmp_path))
    recorder = TelemetryRecorder()
    with pytest.raises(ValueError, match="not allowed"):
        recorder.record(player_name="Ada")


def test_client_bundle_scan_rejects_server_secret_and_developer_path(tmp_path):
    (tmp_path / "server").mkdir()
    (tmp_path / "build_info.json").write_text('{"path":"/Users/developer/game"}')
    failures = verify_bundle(tmp_path)
    assert any("server" in failure for failure in failures)
    assert any("/Users/" in failure for failure in failures)
