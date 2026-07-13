from typing import Any

from core.junction_data import JunctionData
from core.state import RunMetrics


class YJunctionInteraction:
    """ระบบจัดการการตอบสนอง Y-Junction (D1-A3)"""

    def __init__(self, run_metrics: RunMetrics, game_session: Any) -> None:
        self.run_metrics = run_metrics
        self.game_session = game_session  # ใช้ GameSession เป็นตัวจัดการรวม

    def handle_choice(self, junction: JunctionData, choice_side: str) -> None:
        """
        รับค่า Input (ซ้าย/ขวา) อัปเดตสเตตัส Dual-Meter และบันทึก Log ผ่าน GameSession
        """
        if choice_side == 'left':
            selected_choice = junction.left_choice
        elif choice_side == 'right':
            selected_choice = junction.right_choice
        else:
            raise ValueError("choice_side must be 'left' or 'right'")

        # อัปเดตค่า Dual-Meter
        self.run_metrics.update_meters(
            heat_delta=selected_choice.heat_delta,
            anger_delta=selected_choice.anger_delta
        )

        # บันทึกประวัติการตัดสินใจส่งให้ GameSession (PR #58)
        if hasattr(self.game_session, 'policy_choice'):
            self.game_session.policy_choice(
                zone_id=junction.zone_id,
                choice_text=selected_choice.text,
                is_systemic=selected_choice.is_systemic,
                heat_delta=selected_choice.heat_delta,
                anger_delta=selected_choice.anger_delta
            )
