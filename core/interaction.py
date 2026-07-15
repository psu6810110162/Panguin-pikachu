from typing import Protocol, cast

from core.junction_data import Junction, Side
from core.state import RunMetrics


def junction_prompt_text(junction: Junction) -> str:
    """Pure text for a pre-commit Y-junction banner."""
    return f"{junction.situation}\n< LEFT: {junction.left.label} | RIGHT: {junction.right.label} >"


class PolicyChoiceSink(Protocol):
    """รูปร่างของสิ่งที่ YJunctionInteraction ต้องการจาก game_session — ประกาศเป็น
    Protocol แทน import GameSession ตรง ๆ เพราะ core/session.py มาจากเลน Dev B (#58/#62)
    ที่ยังไม่ถูก merge เข้า branch นี้ (import จริงจะพัง). structural typing ให้ mypy ตรวจ
    signature ของ policy_choice() ได้จริง — ต่างจาก Any ที่ปิดการตรวจทั้งก้อน
    """

    def policy_choice(
        self,
        *,
        checkpoint_index: int,
        policy_id: str,
        meter_deltas: dict[str, float],
        distance_m: int,
    ) -> None: ...


class YJunctionInteraction:
    """ระบบจัดการการตอบสนอง Y-Junction (D1-A3)"""

    def __init__(self, run_metrics: RunMetrics, game_session: PolicyChoiceSink) -> None:
        self.run_metrics = run_metrics
        self.game_session = game_session  # ใช้ GameSession เป็นตัวจัดการรวม

    def handle_choice(self, junction: Junction, choice_side: str, distance_m: int) -> None:
        """
        รับค่า Input (ซ้าย/ขวา) อัปเดตสเตตัส Dual-Meter และบันทึก Log ผ่าน GameSession

        Args:
            distance_m: ระยะวิ่งจริง ณ ตอนตัดสินใจ (จาก grid.get_distance_m()) —
                ห้ามใช้ zone*100 เพราะ junction spawn แบบสุ่มในโซน telemetry จะเพี้ยน
        """
        if choice_side == "left":
            selected_choice = junction.left
        elif choice_side == "right":
            selected_choice = junction.right
        else:
            raise ValueError("choice_side must be 'left' or 'right'")
        side = cast(Side, choice_side)  # validated ข้างบนแล้ว

        # อัปเดตค่า Dual-Meter
        self.run_metrics.update_meters(
            heat_delta=selected_choice.meter_deltas.get("heat", 0.0),
            anger_delta=selected_choice.meter_deltas.get("capitalist_anger", 0.0),
        )

        # บันทึกประวัติการตัดสินใจส่งให้ GameSession (PR #58)
        # policy_id ต้องเป็น canonical form "zone{N}-{side}" (Junction.policy_id) — ฝั่ง
        # consumer (core/scoring/stealth.py, dag.py) parse ด้วย parse_policy_id/
        # option_for_policy_id ซึ่ง raise ValueError ถ้าได้ "left"/"right" ดิบ ๆ
        # ไม่ต้อง hasattr แล้ว — PolicyChoiceSink การันตีว่าเมธอดมีจริง (mypy บังคับ caller)
        self.game_session.policy_choice(
            checkpoint_index=junction.zone,
            policy_id=junction.policy_id(side),
            meter_deltas=dict(selected_choice.meter_deltas),
            distance_m=distance_m,
        )
