"""ชนิดของ Event ทั้งหมดที่เกิดขึ้นระหว่างการเล่นหนึ่งรอบ (RunRecord.events)

Event = source of truth (ดู docs/adr/001-runrecord-contract.md) — ทุกการกระทำของผู้เล่น
ถูกเก็บเป็น event ที่นี่ ไม่มีที่ไหนแก้ RunResult ตรง ๆ
"""

from dataclasses import asdict, dataclass
from typing import Any, Literal

# ── Collect ──────────────────────────────────────────────


@dataclass
class CollectEvent:
    timestamp: float
    distance_m: int
    item_type: Literal["gem", "scientific_item"]
    col: int
    row: int
    value: int
    event_type: Literal["collect"] = "collect"


# ── Obstacle / Respawn ───────────────────────────────────


@dataclass
class ObstacleHitEvent:
    timestamp: float
    distance_m: int
    col: int
    row: int
    damage: int
    destroyed: bool
    event_type: Literal["obstacle_hit"] = "obstacle_hit"


@dataclass
class RespawnEvent:
    timestamp: float
    distance_m: int
    checkpoint_col: int
    checkpoint_row: int
    respawn_count: int
    score_penalty: float
    event_type: Literal["respawn"] = "respawn"


# ── Checkpoint / Policy ──────────────────────────────────


@dataclass
class CheckpointReachedEvent:
    timestamp: float
    distance_m: int
    checkpoint_index: int
    event_type: Literal["checkpoint_reached"] = "checkpoint_reached"


@dataclass
class PolicyChoiceEvent:
    timestamp: float
    distance_m: int
    checkpoint_index: int
    policy_id: str
    meter_deltas: dict[str, float]
    event_type: Literal["policy_choice"] = "policy_choice"


# ── Mission ───────────────────────────────────────────────


@dataclass
class MissionProgressEvent:
    timestamp: float
    distance_m: int
    module_index: int
    mission_id: str
    progress: int
    target: int
    event_type: Literal["mission_progress"] = "mission_progress"


@dataclass
class MissionCompleteEvent:
    timestamp: float
    distance_m: int
    module_index: int
    mission_id: str
    event_type: Literal["mission_complete"] = "mission_complete"


# ── Boss ──────────────────────────────────────────────────


@dataclass
class BossPhaseEvent:
    timestamp: float
    distance_m: int
    phase: int
    outcome: Literal["damage_dealt", "damaged", "phase_complete"]
    event_type: Literal["boss_phase"] = "boss_phase"


@dataclass
class BossVictoryEvent:
    timestamp: float
    distance_m: int
    total_time_s: float
    event_type: Literal["boss_victory"] = "boss_victory"


# ── Quiz ──────────────────────────────────────────────────


@dataclass
class QuizAnswerEvent:
    timestamp: float
    distance_m: int
    quiz_id: str
    question_id: str
    correct: bool
    phase: Literal["pretest", "posttest", "boss_debunk"]
    event_type: Literal["quiz_answer"] = "quiz_answer"


GameEvent = (
    CollectEvent
    | ObstacleHitEvent
    | RespawnEvent
    | CheckpointReachedEvent
    | PolicyChoiceEvent
    | MissionProgressEvent
    | MissionCompleteEvent
    | BossPhaseEvent
    | BossVictoryEvent
    | QuizAnswerEvent
)

_EVENT_TYPES: dict[str, type[GameEvent]] = {
    "collect": CollectEvent,
    "obstacle_hit": ObstacleHitEvent,
    "respawn": RespawnEvent,
    "checkpoint_reached": CheckpointReachedEvent,
    "policy_choice": PolicyChoiceEvent,
    "mission_progress": MissionProgressEvent,
    "mission_complete": MissionCompleteEvent,
    "boss_phase": BossPhaseEvent,
    "boss_victory": BossVictoryEvent,
    "quiz_answer": QuizAnswerEvent,
}


def event_to_dict(event: GameEvent) -> dict[str, Any]:
    """แปลง event เป็น dict ที่ JSON-serializable ได้ (ใช้โดย RunRecord.to_dict / D8 sync)"""
    return asdict(event)  # type: ignore[call-overload]


def event_from_dict(data: dict[str, Any]) -> GameEvent:
    """สร้าง event กลับจาก dict ตาม `event_type` — คู่กับ event_to_dict สำหรับ round-trip ผ่าน JSON"""
    event_type = data.get("event_type")
    cls = _EVENT_TYPES.get(event_type)  # type: ignore[arg-type]
    if cls is None:
        raise ValueError(f"Unknown event_type: {event_type!r}")
    return cls(**data)
