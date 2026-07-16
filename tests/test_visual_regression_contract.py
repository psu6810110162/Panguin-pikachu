import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_generated_runtime_manifest_is_complete_and_theme_consistent():
    manifest = json.loads(
        (ROOT / "assets" / "generated" / "manifest.json").read_text(encoding="utf-8")
    )
    runtime_assets = [asset for asset in manifest["assets"] if asset.get("runtime")]

    assert {asset["role"] for asset in runtime_assets} >= {
        "gameplay_background",
        "player_character_runtime_sheet",
        "obstacle_runtime_sheet",
        "support_character",
        "runtime_gameplay_sfx",
    }
    for asset in runtime_assets:
        path = ROOT / asset["path"]
        if path.is_dir():
            assert any(path.iterdir()), f"runtime asset directory is empty: {path}"
        else:
            assert path.is_file(), f"missing runtime asset: {path}"


def test_state_compositions_have_single_overlay_and_decision_owner():
    source = (ROOT / "screens" / "gameplay.py").read_text(encoding="utf-8")

    assert source.count("self.decision_dim.opacity = 1") == 2
    assert source.count("self.respawn_overlay.opacity = 1") == 1
    assert "if self.decision_phase is None and not self.is_respawning" in source
    assert "self.respawn_grace_label" in source
    assert "if decision_phase is DecisionPhase.POLICY:\n                return" in source
