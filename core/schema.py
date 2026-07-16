"""RunRecord — contract กลางระหว่างเกม (client) กับ backend ที่จะมาทีหลัง

ดู docs/adr/001-runrecord-contract.md — events คือ source of truth, result คือ projection
ที่คำนวณทีหลัง (D7b) ห้ามมีที่ไหนแก้ RunRecord.result ตรง ๆ นอกจากตัว scoring engine
"""

from dataclasses import dataclass, field
from typing import Any

from core.events import GameEvent, event_from_dict, event_to_dict
from core.state import RunState, validate_transition

SCHEMA_VERSION = "1.0"


@dataclass
class RunResult:
    """ผลสรุปของการเล่นหนึ่งรอบ คำนวณโดย core/scoring/ (D7b) — ที่นี่แค่กำหนดรูปร่าง

    net_impact_score/cognitive_score/rank มาจาก Stealth Assessment (docs/adr/011,
    core/scoring/stealth.py) — เป็น projection ที่ recompute จาก events ได้เสมอ
    (docs/adr/012-runresult-contract.md) evaluator เป็นจุดเดียวที่ derive ค่าพวกนี้
    ไม่ขึ้นกับ feature flag ฝั่ง server (flag คุมแค่ persist/แสดงผล ดู
    server/config.py::STEALTH_ASSESSMENT_ENABLED). net_impact_score **คือ**
    "อุณหภูมิที่กอบกู้ได้" ตาม GAME_DESIGN.md §7 — ไม่มี field แยกชื่อ temp_reduced_c
    เพราะเป็นค่าเดียวกันเป๊ะ (stealth.net_impact_score_c = run_reduction + cognitive)
    """

    distance_m: int = 0
    respawn_count: int = 0
    environmental_score: float | None = None
    mission_score: float | None = None
    quiz_score: float | None = None
    hake_gain: float | None = None
    heat_controlled_pct: float | None = None
    net_impact_score: float | None = None
    cognitive_score: float | None = None
    rank: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "distance_m": self.distance_m,
            "respawn_count": self.respawn_count,
            "environmental_score": self.environmental_score,
            "mission_score": self.mission_score,
            "quiz_score": self.quiz_score,
            "hake_gain": self.hake_gain,
            "heat_controlled_pct": self.heat_controlled_pct,
            "net_impact_score": self.net_impact_score,
            "cognitive_score": self.cognitive_score,
            "rank": self.rank,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunResult":
        return cls(**data)


@dataclass
class RunRecord:
    """การเล่นหนึ่งรอบ ตั้งแต่เข้าห้องจนซิงก์ข้อมูลเสร็จ"""

    run_id: str
    player_id: str
    schema_version: str = SCHEMA_VERSION
    # ผูก run กับ balance content version ที่ใช้ตอนเล่น (balance/v1/*.json) — ต้องมีตั้งแต่
    # v1 เพื่อกัน replay พังทันทีที่มี balance/v2/: evaluator ใหม่จะรู้ว่า run เก่าอ้างอิง
    # ตัวเลข balance ชุดไหน แทนที่จะ derive ผิดด้วยค่า v2 ทับ run ที่เล่นด้วย v1
    balance_version: str = "v1"
    events: list[GameEvent] = field(default_factory=list)
    state: RunState = RunState.LOBBY
    result: RunResult | None = None

    def record(self, event: GameEvent) -> None:
        """เพิ่ม event ใหม่เข้า log — เป็นวิธีเดียวที่อนุญาตให้แก้ RunRecord.events"""
        self.events.append(event)

    def advance_state(self, new_state: RunState, **context: object) -> None:
        """เปลี่ยน RunState — เป็นวิธีเดียวที่อนุญาตให้แก้ RunRecord.state

        ตรวจสอบผ่าน core.state.validate_transition ก่อนเสมอ (raises
        InvalidTransitionError ถ้าเปลี่ยนไม่ได้)
        """
        validate_transition(self.state, new_state, **context)
        self.state = new_state

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "player_id": self.player_id,
            "balance_version": self.balance_version,
            "events": [event_to_dict(e) for e in self.events],
            "state": self.state.name,
            "result": self.result.to_dict() if self.result else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunRecord":
        result_data = data.get("result")
        return cls(
            run_id=data["run_id"],
            player_id=data["player_id"],
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            # run เก่าก่อนมี balance_version (ก่อน field นี้เกิด) ถือว่าเล่นด้วย "v1" เสมอ
            # เพราะ balance/v1/ คือ version เดียวที่เคยมีอยู่ตอนนั้น
            balance_version=data.get("balance_version", "v1"),
            events=[event_from_dict(e) for e in data.get("events", [])],
            state=RunState[data.get("state", RunState.LOBBY.name)],
            result=RunResult.from_dict(result_data) if result_data else None,
        )
