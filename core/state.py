import json
from enum import Enum, auto
from typing import Any


class GameState(Enum):
    """โครงสร้าง Enum สำหรับเก็บสถานะปัจจุบันของเกม"""

    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAMEOVER = auto()
    HISTORY = auto()
    SHOP = auto()


class StateManager:
    """Singleton ที่ควบคุม state ของหน้าจอหลักของเกม"""

    _instance: "StateManager | None" = None
    current_state: GameState
    selected_skin: str

    def __new__(cls) -> "StateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_state = GameState.MENU
            cls._instance.selected_skin = "Ninja Frog"
        return cls._instance

    def change_state(self, new_state: GameState) -> None:
        self.current_state = new_state
        print(f"[State] Changed to: {new_state.name}")

    def is_playing(self) -> bool:
        return self.current_state == GameState.PLAYING


# ══════════════════════════════════════════════════════════════
#  RunState — สถานะวงจรชีวิตของ "การเล่นหนึ่งรอบ" (RunRecord.state)
#  ไม่เกี่ยวกับ GameState/StateManager ด้านบน (ซึ่งคือหน้าจอที่กำลังแสดง)
#  ดู docs/adr/001-runrecord-contract.md
# ══════════════════════════════════════════════════════════════


class RunState(Enum):
    """สถานะของการเล่นหนึ่งรอบ ตั้งแต่เข้าห้องจนซิงก์ข้อมูลเสร็จ"""

    LOBBY = auto()
    RUNNING = auto()
    RESPAWNING = auto()
    BOSS = auto()
    FINISHED = auto()
    SYNCED = auto()


class InvalidTransitionError(Exception):
    """เกิดขึ้นเมื่อพยายามเปลี่ยน RunState ไปยังสถานะที่ไม่อนุญาต หรือไม่ผ่านเงื่อนไข (guard)"""


_ALLOWED_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.LOBBY: {RunState.RUNNING},
    RunState.RUNNING: {RunState.RESPAWNING, RunState.BOSS},
    RunState.RESPAWNING: {RunState.RUNNING},
    RunState.BOSS: {RunState.FINISHED},
    RunState.FINISHED: {RunState.SYNCED},
    RunState.SYNCED: set(),
}

BOSS_MIN_DISTANCE_M = 1000


def validate_transition(current: RunState, new: RunState, **context: object) -> None:
    """ตรวจสอบว่าเปลี่ยนจาก `current` ไปยัง `new` ได้หรือไม่

    Raises:
        InvalidTransitionError: ถ้า transition ไม่อยู่ใน _ALLOWED_TRANSITIONS
            หรือไม่ผ่านเงื่อนไขเฉพาะของ transition นั้น (เช่น RUNNING -> BOSS
            ต้องมี context["distance_m"] >= BOSS_MIN_DISTANCE_M)
    """
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise InvalidTransitionError(f"Cannot transition from {current.name} to {new.name}")

    if current is RunState.RUNNING and new is RunState.BOSS:
        distance_m = context.get("distance_m")
        if not isinstance(distance_m, int | float) or distance_m < BOSS_MIN_DISTANCE_M:
            raise InvalidTransitionError(
                f"RUNNING -> BOSS requires distance_m >= {BOSS_MIN_DISTANCE_M}, got {distance_m!r}"
            )


# ══════════════════════════════════════════════════════════════
#  Dual-Meter & Hearts System (Day 1 - Dev A)
# ══════════════════════════════════════════════════════════════


def load_difficulty() -> dict[str, Any]:
    try:
        with open("balance/v1/difficulty.json", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "meters": {
                "start_heat": 50.0,
                "start_capitalist_anger": 50.0,
                "max": 100.0,
                "game_over_at": 100.0,
                "min": 0.0,
            },
            "hearts": {"start": 5},
        }


class RunMetrics:
    """จัดการ State ของตัวแปรระหว่างการวิ่ง (Day 1: D1-A1 & D1-A4)
    รับผิดชอบเกี่ยวกับทรัพยากรผู้เล่นและการตัดสิน Game Over
    """

    def __init__(
        self,
        heat_meter: float | None = None,
        capitalist_anger: float | None = None,
        hearts: int | None = None,
    ) -> None:
        diff = load_difficulty()
        meters_diff: dict[str, Any] = diff.get("meters", {}) if isinstance(diff, dict) else {}
        hearts_diff: dict[str, Any] = diff.get("hearts", {}) if isinstance(diff, dict) else {}

        self.heat_meter: float = (
            heat_meter if heat_meter is not None else float(meters_diff.get("start_heat", 50.0))
        )
        self.capitalist_anger: float = (
            capitalist_anger
            if capitalist_anger is not None
            else float(meters_diff.get("start_capitalist_anger", 50.0))
        )
        self.hearts: int = hearts if hearts is not None else int(hearts_diff.get("start", 5))

        self.max_meter: float = float(meters_diff.get("max", 100.0))
        self.min_meter: float = float(meters_diff.get("min", 0.0))
        self.game_over_at: float = float(meters_diff.get("game_over_at", 100.0))

        self.is_game_over: bool = False
        self.needs_respawn: bool = False
        self.is_invincible: bool = False

    def update_meters(self, heat_delta: float, anger_delta: float) -> None:
        """D1-A1: รับค่า Delta เพื่ออัปเดตหลอดวัด (Dual-Meter)"""
        if self.is_game_over:
            return

        self.heat_meter = max(
            self.min_meter, min(self.max_meter, self.heat_meter + float(heat_delta))
        )
        self.capitalist_anger = max(
            self.min_meter, min(self.max_meter, self.capitalist_anger + float(anger_delta))
        )

        if self.heat_meter >= self.game_over_at or self.capitalist_anger >= self.game_over_at:
            self.trigger_game_over()

    def decrease_heart(self) -> None:
        """D1-A4: ลดหัวใจเมื่อตกเหว"""
        if self.is_game_over or self.is_invincible:
            return

        self.hearts -= 1
        if self.hearts <= 0:
            self.hearts = 0
            self.trigger_game_over()
        else:
            self.needs_respawn = True
            self.is_invincible = True

    def trigger_game_over(self) -> None:
        """เปลี่ยนสถานะภายในเป็น Game Over เพื่อให้ฝั่งหน้าจอนำไปเช็ค (ป้องกัน Side-effect ใน Test)"""
        self.is_game_over = True
