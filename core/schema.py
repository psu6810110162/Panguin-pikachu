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
    """ผลสรุปของการเล่นหนึ่งรอบ คำนวณโดย core/scoring/ (D7b) — ที่นี่แค่กำหนดรูปร่าง"""

    distance_m: int = 0
    respawn_count: int = 0
    environmental_score: float | None = None
    mission_score: float | None = None
    quiz_score: float | None = None
    hake_gain: float | None = None
    heat_controlled_pct: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "distance_m": self.distance_m,
            "respawn_count": self.respawn_count,
            "environmental_score": self.environmental_score,
            "mission_score": self.mission_score,
            "quiz_score": self.quiz_score,
            "hake_gain": self.hake_gain,
            "heat_controlled_pct": self.heat_controlled_pct,
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
            events=[event_from_dict(e) for e in data.get("events", [])],
            state=RunState[data.get("state", RunState.LOBBY.name)],
            result=RunResult.from_dict(result_data) if result_data else None,
        )
