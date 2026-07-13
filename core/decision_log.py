from dataclasses import dataclass


@dataclass
class DecisionRecord:
    zone_id: int
    choice_text: str
    is_systemic: bool  # True for green line, False for red line (DAG)
    heat_delta: int
    anger_delta: int


class DecisionLog:
    """ระบบบันทึกการตัดสินใจ Y-Junction (D1-B3) สำหรับวาด DAG"""

    def __init__(self) -> None:
        self.records: list[DecisionRecord] = []

    def log_decision(
        self,
        zone_id: int,
        choice_text: str,
        is_systemic: bool,
        heat_delta: int,
        anger_delta: int,
    ) -> None:
        """บันทึกข้อมูลเมื่อผ่านทางแยก"""
        record = DecisionRecord(
            zone_id=zone_id,
            choice_text=choice_text,
            is_systemic=is_systemic,
            heat_delta=heat_delta,
            anger_delta=anger_delta,
        )
        self.records.append(record)

    def get_all_records(self) -> list[DecisionRecord]:
        return self.records

    def clear(self) -> None:
        self.records.clear()
