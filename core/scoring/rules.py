"""กติกาการให้คะแนนแบบ rule-based — แต่ละฟังก์ชันคือกติกาเดียวที่อธิบายได้ในบรรทัดเดียว

ดู docs/adr/003-rule-based-evaluation.md: "Policy ดี + Heat ต่ำ + Mission ผ่าน = Environmental Score"
แทนที่จะใช้ DAG evaluation ที่ซับซ้อนกว่า
"""

from core.events import (
    GameEvent,
    MissionCompleteEvent,
    PolicyChoiceEvent,
    QuizAnswerEvent,
    RespawnEvent,
)

# น้ำหนักของแต่ละองค์ประกอบใน Environmental Score (รวมกันได้ 1.0) — ปรับได้ตรงนี้จุดเดียว
POLICY_WEIGHT = 0.3
HEAT_WEIGHT = 0.3
MISSION_WEIGHT = 0.4


def mission_score(events: list[GameEvent], total_missions: int) -> float:
    """% ของ mission ที่ทำสำเร็จ เทียบกับ total_missions ทั้งหมดใน run"""
    if total_missions <= 0:
        return 0.0
    completed = sum(1 for e in events if isinstance(e, MissionCompleteEvent))
    return min(completed, total_missions) / total_missions * 100


def quiz_score(events: list[GameEvent], phase: str) -> float | None:
    """% ตอบถูกของ QuizAnswerEvent ในช่วง phase ที่ระบุ (pretest/posttest/boss_debunk)

    Returns:
        None ถ้ายังไม่มี QuizAnswerEvent ของ phase นี้เลย (ผู้เล่นยังไปไม่ถึง phase นั้น) —
        แยกจาก 0.0 (ตอบครบแล้วแต่ผิดหมด) เพื่อไม่ให้ "ยังไม่ถึง" ถูกนับเป็น "ตอบผิดหมด"
        ตอนเฉลี่ยรวมหลาย phase ใน evaluator.py
    """
    answers = [e for e in events if isinstance(e, QuizAnswerEvent) and e.phase == phase]
    if not answers:
        return None
    correct = sum(1 for a in answers if a.correct)
    return correct / len(answers) * 100


def heat_controlled_pct(events: list[GameEvent], starting_heat: float = 50.0) -> float:
    """100 - heat สุดท้าย หลังไล่ apply PolicyChoiceEvent.meter_deltas["heat"] ตามลำดับเวลา

    heat ต่ำ = ควบคุมได้ดี = คะแนนสูง (heat ถูก clamp ไว้ที่ [0, 100] ทุกครั้งที่อัปเดต)
    starting_heat เป็นพารามิเตอร์ (ไม่ hardcode) เพราะระบบ meter จริง (D1) ยังไม่เสร็จ —
    ค่อยปรับ baseline ให้ตรงกับของจริงทีหลังโดยไม่ต้องแก้สูตรนี้
    """
    heat = starting_heat
    for e in events:
        if isinstance(e, PolicyChoiceEvent):
            heat += e.meter_deltas.get("heat", 0.0)
            heat = max(0.0, min(100.0, heat))
    return 100.0 - heat


def policy_score(events: list[GameEvent]) -> float:
    """% ของ policy choice ที่ "ดี" — ตามหลักการนี้: ผลรวม meter_deltas ของการเลือกนั้น <= 0
    (ยิ่งลด/ไม่เพิ่ม meter รวม ยิ่งถือว่าเป็นทางเลือกเชิงบวกต่อสิ่งแวดล้อม)
    """
    choices = [e for e in events if isinstance(e, PolicyChoiceEvent)]
    if not choices:
        return 0.0
    good = sum(1 for c in choices if sum(c.meter_deltas.values()) <= 0)
    return good / len(choices) * 100


def respawn_count(events: list[GameEvent]) -> int:
    """จำนวนครั้งที่ผู้เล่น respawn ระหว่าง run"""
    return sum(1 for e in events if isinstance(e, RespawnEvent))


def environmental_score(
    policy_component: float,
    heat_component: float,
    mission_component: float,
) -> float:
    """คะแนนรวมด้านสิ่งแวดล้อม — ผลรวมถ่วงน้ำหนักของ policy_score, heat_controlled_pct,
    mission_score (ทั้งสามอยู่ในสเกล 0-100 อยู่แล้ว)
    """
    return (
        policy_component * POLICY_WEIGHT
        + heat_component * HEAT_WEIGHT
        + mission_component * MISSION_WEIGHT
    )
