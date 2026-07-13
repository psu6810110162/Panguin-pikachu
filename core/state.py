from enum import Enum, auto


class GameState(Enum):
    """โครงสร้าง Enum สำหรับเก็บสถานะปัจจุบันของเกม"""

    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAMEOVER = auto()
    HISTORY = auto()
    SHOP = auto()


class StateManager:
    # คลาส Singleton ที่รับหน้าที่เปลี่ยนย้าย State ภาพรวมของเกม
    # เพื่อป้องกันการสับ State ชนกันระหว่างหน้าจอ
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


# สถานะปัจจุบัน -> ชุดสถานะถัดไปที่อนุญาตให้เปลี่ยนได้
#
# ข้อสังเกตเชิงดีไซน์ (ยืนยันกับทีมเกมแล้วถ้าจะเปลี่ยน): BOSS ไม่มีทางกลับไป
# RESPAWNING/RUNNING — สมมติฐานคือ boss phase ไม่มีการ respawn (โดนบอสตีเสีย
# คะแนนผ่าน BossPhaseEvent(outcome="damaged") แต่ไม่ตาย/ไม่ย้อน state) ถ้ากติกา
# เกมเปลี่ยนให้แพ้บอสได้ ต้องเพิ่ม transition ที่นี่พร้อม test ประกบ
_ALLOWED_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.LOBBY: {RunState.RUNNING},
    RunState.RUNNING: {RunState.RESPAWNING, RunState.BOSS},
    RunState.RESPAWNING: {RunState.RUNNING},
    RunState.BOSS: {RunState.FINISHED},
    RunState.FINISHED: {RunState.SYNCED},
    RunState.SYNCED: set(),
}

# BOSS_MIN_DISTANCE_M: เข้าสู่ Boss ได้ก็ต่อเมื่อวิ่งถึงเส้นชัย 1,000 เมตรแล้วเท่านั้น
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


class RunMetrics:
    """จัดการ State ของตัวแปรระหว่างการวิ่ง (Day 1: D1-A1 & D1-A4)
    รับผิดชอบเกี่ยวกับทรัพยากรผู้เล่นและการตัดสิน Game Over
    """

    def __init__(self, heat_meter: int = 0, capitalist_anger: int = 0, hearts: int = 5):
        self.heat_meter = heat_meter
        self.capitalist_anger = capitalist_anger
        self.hearts = hearts
        self.is_game_over = False

    def update_meters(self, heat_delta: int, anger_delta: int) -> None:
        """
        D1-A1: รับค่า Delta เพื่ออัปเดตหลอดวัด (Dual-Meter)
        """
        if self.is_game_over:
            return

        self.heat_meter = max(0, min(100, self.heat_meter + heat_delta))
        self.capitalist_anger = max(0, min(100, self.capitalist_anger + anger_delta))

        # Trigger game-over ถ้าหลอดใดหลอดหนึ่งแตะ 100 (เลข 0 คือปลอดภัยที่สุด)
        if self.heat_meter >= 100 or self.capitalist_anger >= 100:
            self.trigger_game_over()

    def decrease_heart(self) -> None:
        """
        D1-A4: ลดหัวใจเมื่อตกเหว
        """
        if self.is_game_over:
            return

        self.hearts -= 1
        if self.hearts <= 0:
            self.hearts = 0
            self.trigger_game_over()

    def trigger_game_over(self) -> None:
        """เปลี่ยนสถานะภายในเป็น Game Over เพื่อให้ฝั่งหน้าจอนำไปเช็ค (ป้องกัน Side-effect ใน Test)"""
        self.is_game_over = True
