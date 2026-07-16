import json
from pathlib import Path

from core.replay import canonical_result_json, replay, result_sha256

FIXTURES = Path(__file__).parent / "fixtures" / "replays"


def test_golden_replay_is_canonical_and_unchanged():
    with (FIXTURES / "run-v1.json").open(encoding="utf-8") as handle:
        fixture = json.load(handle)
    expected = (FIXTURES / "run-v1.sha256").read_text(encoding="utf-8").strip()

    first = replay(fixture)
    second = replay(fixture)

    assert canonical_result_json(first) == canonical_result_json(second)
    assert result_sha256(first) == expected
