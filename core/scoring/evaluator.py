"""Orchestration: RunRecord.events -> RunResult

นี่คือ "scoring engine" ตัวเดียวที่ docs/adr/001-runrecord-contract.md อนุญาตให้แก้
RunRecord.result — ทุกที่อื่นต้องอ่านอย่างเดียว
"""

from core.schema import RunRecord, RunResult
from core.scoring import rules, stealth
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
    answered_scores = [
        s for s in (rules.quiz_score(events, phase) for phase in _QUIZ_PHASES) if s is not None
    ]
    q_score = sum(answered_scores) / len(answered_scores) if answered_scores else 0.0
    heat_pct = rules.heat_controlled_pct(events, starting_heat=starting_heat)
    p_score = rules.policy_score(events)
    env_score = rules.environmental_score(p_score, heat_pct, m_score)
    gain = hake_gain(pretest_pct, posttest_pct)

    # Stealth Assessment (Educational Score, ADR-011) — derive เสมอไม่ขึ้นกับ feature
    # flag ใด ๆ (flag ฝั่ง server คุมแค่ persist/แสดงผล ไม่คุม logic การคำนวณ — ดู ADR-012
    # และ server/config.py::STEALTH_ASSESSMENT_ENABLED)
    # TODO(balance-v2): record.balance_version ถูก persist แล้วแต่ยังไม่ถูกใช้เลือกชุด
    # ค่า balance ที่นี่ — scoring ใช้ balance/v1 เสมอ เมื่อมี balance/v2/ ต้อง branch ตาม
    # record.balance_version เพื่อ replay run เก่าให้ตรง (ดู core/schema.py::balance_version)
    net_impact = stealth.net_impact_score_c(events)
    cognitive = stealth.cognitive_score_c(events)
    rank = stealth.rank_for(net_impact)

    result = RunResult(
        distance_m=distance_m,
        respawn_count=rules.respawn_count(events),
        environmental_score=env_score,
        mission_score=m_score,
        quiz_score=q_score,
        hake_gain=gain,
        heat_controlled_pct=heat_pct,
        net_impact_score=net_impact,
        cognitive_score=cognitive,
        rank=rank,
    )
    record.result = result
    return result
