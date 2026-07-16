"""Canonical event-log replay helpers used by the golden regression gate."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from core.schema import RunRecord, RunResult
from core.scoring.evaluator import evaluate


def replay(fixture: dict[str, Any]) -> RunResult:
    record = RunRecord.from_dict(fixture["run_record"])
    inputs = fixture["evaluation"]
    return evaluate(
        record,
        pretest_pct=float(inputs["pretest_pct"]),
        posttest_pct=float(inputs["posttest_pct"]),
        total_missions=int(inputs["total_missions"]),
        starting_heat=float(inputs.get("starting_heat", 50.0)),
    )


def canonical_result_json(result: RunResult) -> str:
    return json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def result_sha256(result: RunResult) -> str:
    return hashlib.sha256(canonical_result_json(result).encode()).hexdigest()
