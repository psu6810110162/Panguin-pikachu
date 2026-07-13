"""GameSession — เจ้าของ RunRecord แบบ single-writer หนึ่งตัวต่อการเล่นหนึ่งรอบ

ดู docs/adr/001-runrecord-contract.md และ docs/ENGINEERING_PLAN.md (RunRecord Ownership):
GamePlayScreen ถือ GameSession หนึ่งตัว, ทุกระบบ (meter/heart/junction/boss/item)
เรียก emit ผ่าน session เท่านั้น — ไม่มีใคร append เข้า RunRecord.events เอง
→ กัน race และให้ event log มีลำดับเดียวที่เชื่อถือได้

เลเยอร์นี้เป็น pure Python (ห้าม import kivy — บังคับด้วย tests/test_no_kivy_in_core.py)
เวลา timestamp คิดจาก clock ที่ inject ได้ เพื่อให้ unit test คุมเวลาได้แน่นอน
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Literal

from core.events import (
    BossPhaseEvent,
    BossVictoryEvent,
    CheckpointReachedEvent,
    CollectEvent,
    MissionCompleteEvent,
    MissionProgressEvent,
    ObstacleHitEvent,
    PolicyChoiceEvent,
    QuizAnswerEvent,
    RespawnEvent,
)
from core.schema import RunRecord
from core.state import RunState


class GameSession:
    """ห่อ RunRecord หนึ่งรอบ + เป็นทางเดียวที่บันทึก event และเปลี่ยน RunState

    Args:
        run_id: id ของรอบเล่น (สุ่ม uuid ถ้าไม่ระบุ)
        player_id: id ผู้เล่น (ยังไม่มีระบบ join ห้อง → default "local", ต่อกับ server ใน PR8)
        clock: ฟังก์ชันคืนเวลาเป็นวินาที (default time.monotonic) — inject ได้เพื่อ test
    """

    def __init__(
        self,
        *,
        run_id: str | None = None,
        player_id: str = "local",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._record = RunRecord(run_id=run_id or uuid.uuid4().hex, player_id=player_id)
        self._clock = clock
        self._start = clock()

    # ── การเข้าถึงแบบอ่านอย่างเดียว ────────────────────────────────

    @property
    def run_record(self) -> RunRecord:
        """RunRecord ที่ session นี้เป็นเจ้าของ — ผู้เรียกควรอ่านอย่างเดียว (scoring/sync)"""
        return self._record

    @property
    def state(self) -> RunState:
        return self._record.state

    @property
    def events_count(self) -> int:
        return len(self._record.events)

    def elapsed(self) -> float:
        """วินาทีนับจากตอนสร้าง session — ใช้เป็น timestamp ของ event"""
        return self._clock() - self._start

    # ── lifecycle (เปลี่ยน RunState ผ่าน state machine ที่ validate แล้ว) ──

    def start(self) -> None:
        """LOBBY → RUNNING (เริ่มวิ่ง)"""
        self._record.advance_state(RunState.RUNNING)

    def begin_respawn(self) -> None:
        """RUNNING → RESPAWNING (ตกเหว รอเกิดใหม่)"""
        self._record.advance_state(RunState.RESPAWNING)

    def resume_after_respawn(self) -> None:
        """RESPAWNING → RUNNING (เกิดใหม่ที่ checkpoint แล้ววิ่งต่อ)"""
        self._record.advance_state(RunState.RUNNING)

    def enter_boss(self, *, distance_m: int) -> None:
        """RUNNING → BOSS (ต้องถึง 1,000m — validate ใน state machine)"""
        self._record.advance_state(RunState.BOSS, distance_m=distance_m)

    def finish(self) -> None:
        """BOSS → FINISHED (จบรอบ ไปหน้า report)"""
        self._record.advance_state(RunState.FINISHED)

    def mark_synced(self) -> None:
        """FINISHED → SYNCED (ซิงก์ขึ้น server แล้ว)"""
        self._record.advance_state(RunState.SYNCED)

    # ── event emitters (single-writer surface) ────────────────────
    # ทุกเมธอดเป็น thin wrapper 1:1 กับ dataclass ใน core/events.py
    # ระบบ gameplay เรียกผ่านตรงนี้ ไม่สร้าง event เอง

    def collect(
        self,
        *,
        item_type: Literal["gem", "scientific_item"],
        col: int,
        row: int,
        value: int,
        distance_m: int,
    ) -> None:
        self._record.record(
            CollectEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                item_type=item_type,
                col=col,
                row=row,
                value=value,
            )
        )

    def obstacle_hit(
        self, *, col: int, row: int, damage: int, destroyed: bool, distance_m: int
    ) -> None:
        self._record.record(
            ObstacleHitEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                col=col,
                row=row,
                damage=damage,
                destroyed=destroyed,
            )
        )

    def respawn(
        self,
        *,
        checkpoint_col: int,
        checkpoint_row: int,
        respawn_count: int,
        score_penalty: float,
        distance_m: int,
    ) -> None:
        self._record.record(
            RespawnEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                checkpoint_col=checkpoint_col,
                checkpoint_row=checkpoint_row,
                respawn_count=respawn_count,
                score_penalty=score_penalty,
            )
        )

    def checkpoint_reached(self, *, checkpoint_index: int, distance_m: int) -> None:
        self._record.record(
            CheckpointReachedEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                checkpoint_index=checkpoint_index,
            )
        )

    def policy_choice(
        self,
        *,
        checkpoint_index: int,
        policy_id: str,
        meter_deltas: dict[str, float],
        distance_m: int,
    ) -> None:
        self._record.record(
            PolicyChoiceEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                checkpoint_index=checkpoint_index,
                policy_id=policy_id,
                meter_deltas=meter_deltas,
            )
        )

    def mission_progress(
        self, *, module_index: int, mission_id: str, progress: int, target: int, distance_m: int
    ) -> None:
        self._record.record(
            MissionProgressEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                module_index=module_index,
                mission_id=mission_id,
                progress=progress,
                target=target,
            )
        )

    def mission_complete(self, *, module_index: int, mission_id: str, distance_m: int) -> None:
        self._record.record(
            MissionCompleteEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                module_index=module_index,
                mission_id=mission_id,
            )
        )

    def boss_phase(
        self,
        *,
        phase: int,
        outcome: Literal["damage_dealt", "damaged", "phase_complete"],
        distance_m: int,
    ) -> None:
        self._record.record(
            BossPhaseEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                phase=phase,
                outcome=outcome,
            )
        )

    def boss_victory(self, *, total_time_s: float, distance_m: int) -> None:
        self._record.record(
            BossVictoryEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                total_time_s=total_time_s,
            )
        )

    def quiz_answer(
        self,
        *,
        quiz_id: str,
        question_id: str,
        correct: bool,
        phase: Literal["pretest", "posttest", "boss_debunk"],
        distance_m: int,
    ) -> None:
        self._record.record(
            QuizAnswerEvent(
                timestamp=self.elapsed(),
                distance_m=distance_m,
                quiz_id=quiz_id,
                question_id=question_id,
                correct=correct,
                phase=phase,
            )
        )
