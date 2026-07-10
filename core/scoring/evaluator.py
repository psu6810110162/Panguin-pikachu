"""Orchestration: RunRecord.events -> RunResult

นี่คือ "scoring engine" ตัวเดียวที่ docs/adr/001-runrecord-contract.md อนุญาตให้แก้
RunRecord.result — ทุกที่อื่นต้องอ่านอย่างเดียว
"""

from core.schema import RunRecord, RunResult
from core.scoring import rules
from core.scoring.hake import hake_gain

# phase ที่ใช้คำนวณ quiz_score หลัก — ครอบคลุมทั้งก่อน/หลังเรียนและช่วง boss debunk
_QUIZ_PHASES = ("pretest", "posttest", "boss_debunk")


def evaluate(
    record: RunRecord,
    *,
    pretest_pct: float,
    posttest_pct: float,
    total_missions: int,
    starting_heat: float = 50.0,
) -> RunResult:
    """คำนวณ RunResult จาก record.events แล้ว assign เข้า record.result ก่อน return"""
    events = record.events
    distance_m = max((e.distance_m for e in events), default=0)

    m_score = rules.mission_score(events, total_missions)
    q_score = sum(rules.quiz_score(events, phase) for phase in _QUIZ_PHASES) / len(_QUIZ_PHASES)
    heat_pct = rules.heat_controlled_pct(events, starting_heat=starting_heat)
    p_score = rules.policy_score(events)
    env_score = rules.environmental_score(p_score, heat_pct, m_score)
    gain = hake_gain(pretest_pct, posttest_pct)

    result = RunResult(
        distance_m=distance_m,
        respawn_count=rules.respawn_count(events),
        environmental_score=env_score,
        mission_score=m_score,
        quiz_score=q_score,
        hake_gain=gain,
        heat_controlled_pct=heat_pct,
    )
    record.result = result
    return result
