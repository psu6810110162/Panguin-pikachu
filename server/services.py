"""Business logic ของ backend — session lifecycle, ingest run ที่ verify+score+เก็บ DB

ทุกอย่างที่นี่ import จาก core/ เท่านั้น (ห้าม import game/ เพราะลาก Kivy —
ดู docs/adr/006-server-authoritative-scoring.md)
"""

import json
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError

from core.events import GameEvent
from core.schema import RunRecord, RunResult
from core.scoring import rules
from core.scoring.evaluator import evaluate
from core.state import RunState
from core.sync import NonceStore, SignedPayload, verify_signed_payload
from server.extensions import db
from server.models import PlayerModel, RunModel, SessionModel

# จำนวน mission ทั้งหมดต่อ run — ตรงกับ "3 modules" ใน docs/OVERVIEW.md (mission ย่อยละ 1
# ต่อ module) ค่านี้ควรมาจาก config ของเนื้อหาเกมจริงในอนาคต ตอนนี้ hardcode ไว้ก่อน
TOTAL_MISSIONS = 3

# room_code มีแค่ 9000 ค่าที่เป็นไปได้ (secrets.randbelow(9000)) — ชนกันได้จริงเมื่อมีหลาย
# session พร้อมกัน จำนวน attempt นี้เผื่อไว้มากกว่าพอสำหรับสเกลห้องเรียน (< 5 session พร้อมกัน)
_MAX_ROOM_CODE_ATTEMPTS = 5

_STATE_TO_DASHBOARD_STATUS: dict[RunState, str] = {
    RunState.LOBBY: "ACTIVE",
    RunState.RUNNING: "ACTIVE",
    RunState.BOSS: "ACTIVE",
    RunState.RESPAWNING: "RESPAWNING",
    RunState.FINISHED: "FINISHED",
    RunState.SYNCED: "FINISHED",
}


class ValidationError(Exception):
    """ข้อมูล run ที่รับมาไม่สมเหตุผล (เช่น distance ย้อนกลับ) — ปฏิเสธก่อนคำนวณคะแนน"""


def generate_room_code() -> str:
    return f"PENGUIN-{secrets.randbelow(9000) + 1000}"


def create_session() -> SessionModel:
    # teacher_token คือสิทธิ์ครูประจำ session (end/export/dashboard) — คืนให้ครั้งเดียว
    # ตอนสร้างเท่านั้น 32 bytes (~256 bits) เกินพอจนไม่ต้องถกเรื่อง entropy อีก
    for _ in range(_MAX_ROOM_CODE_ATTEMPTS):
        session = SessionModel(
            room_code=generate_room_code(), teacher_token=secrets.token_urlsafe(32)
        )
        db.session.add(session)
        try:
            db.session.commit()
            return session
        except IntegrityError:
            db.session.rollback()
    raise RuntimeError(
        f"failed to generate a unique room code after {_MAX_ROOM_CODE_ATTEMPTS} attempts"
    )


def get_session_by_code(room_code: str) -> SessionModel | None:
    return db.session.query(SessionModel).filter_by(room_code=room_code).first()


def join_session(session: SessionModel, name: str) -> PlayerModel:
    if not session.is_active:
        raise ValidationError(f"session {session.room_code} has ended")
    player = PlayerModel(session_id=session.id, player_id=uuid.uuid4().hex, name=name)
    db.session.add(player)
    db.session.commit()
    return player


def end_session(session: SessionModel) -> None:
    session.ended_at = datetime.now(UTC)
    db.session.commit()


def validate_events(events: list[GameEvent]) -> None:
    """เช็คความสมเหตุผลอย่างง่าย: distance_m ต้องไม่ย้อนกลับตามลำดับเวลาที่บันทึกไว้
    (กัน client ที่ถูกแก้ไขส่งข้อมูลมั่ว ๆ — ดู "Server-authoritative scoring" ใน
    docs/ENGINEERING_PLAN.md)
    """
    last_distance = -1
    for event in events:
        if event.distance_m < last_distance:
            raise ValidationError(
                f"distance_m went backwards: {last_distance} -> {event.distance_m}"
            )
        last_distance = event.distance_m


def ingest_signed_run(
    session: SessionModel,
    signed_payload: SignedPayload,
    secret: bytes,
    nonce_store: NonceStore,
    *,
    stealth_enabled: bool = False,
) -> RunModel:
    """Verify -> parse -> validate -> score -> upsert ทับ run_id เดิม (idempotent)

    Raises:
        VerificationError: signature/nonce/timestamp ไม่ผ่าน
        ValidationError: ข้อมูล events ไม่สมเหตุผล
    """
    verify_signed_payload(signed_payload, secret, nonce_store)

    if not session.is_active:
        raise ValidationError(f"session {session.room_code} has ended")

    # from_dict เป็น plain dataclass ที่ raise TypeError/KeyError/ValueError ดิบกับข้อมูล
    # เสีย (พฤติกรรมที่ตรึงไว้ใน tests/test_schema.py) — แปลงเป็น ValidationError ที่นี่
    # เพื่อให้ client ที่ส่ง body เพี้ยนได้ 400 ไม่ใช่ 500
    try:
        record = RunRecord.from_dict(json.loads(signed_payload.body))
    except (TypeError, KeyError, ValueError) as error:
        raise ValidationError(f"malformed run record body: {error!r}") from error
    validate_events(record.events)

    # scope ด้วย session ด้วยเสมอ — player_id เป็น uuid unique ข้ามทุก session ก็จริง
    # แต่ payload ที่อ้าง player ของ session อื่นต้องไม่ resolve ชื่อข้ามห้องได้
    player = (
        db.session.query(PlayerModel)
        .filter_by(player_id=record.player_id, session_id=session.id)
        .first()
    )
    player_name = player.name if player else record.player_id

    pretest_pct = rules.quiz_score(record.events, phase="pretest") or 0.0
    posttest_pct = rules.quiz_score(record.events, phase="posttest") or 0.0
    result = evaluate(
        record,
        pretest_pct=pretest_pct,
        posttest_pct=posttest_pct,
        total_missions=TOTAL_MISSIONS,
    )

    run = db.session.query(RunModel).filter_by(run_id=record.run_id, session_id=session.id).first()
    if run is None:
        run = RunModel(session_id=session.id, run_id=record.run_id, player_id=record.player_id)
        db.session.add(run)

    _apply_result(run, record, result, player_name, stealth_enabled=stealth_enabled)

    # query-แล้วค่อย-insert ข้างบนไม่ atomic ภายใต้ async_mode="threading" — สอง request
    # ของ run_id เดียวกัน (เช่น client retry จาก offline queue) อาจเห็น run is None พร้อม
    # กันแล้ว insert ชน unique constraint ฝั่งที่แพ้ rollback แล้ว update ทับแถวของฝั่งที่
    # ชนะแทน ปลอดภัยเพราะ duplicate ingest ต้อง converge: ทั้งสองฝั่งเขียนค่าที่คำนวณจาก
    # payload เดียวกันลง run เดียวกัน (upsert idempotent)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        run = (
            db.session.query(RunModel).filter_by(run_id=record.run_id, session_id=session.id).one()
        )
        _apply_result(run, record, result, player_name, stealth_enabled=stealth_enabled)
        db.session.commit()
    return run


def _apply_result(
    run: RunModel,
    record: RunRecord,
    result: RunResult,
    player_name: str,
    *,
    stealth_enabled: bool = False,
) -> None:
    run.player_name = player_name
    run.status = _STATE_TO_DASHBOARD_STATUS[record.state]
    run.distance_m = result.distance_m
    run.respawn_count = result.respawn_count
    run.environmental_score = result.environmental_score
    run.mission_score = result.mission_score
    run.quiz_score = result.quiz_score
    run.hake_gain = result.hake_gain
    run.heat_controlled_pct = result.heat_controlled_pct
    run.balance_version = record.balance_version

    # Stealth Assessment fields: evaluator() คำนวณเสมอ (result.* มีค่าอยู่แล้ว) แต่ persist
    # เฉพาะตอน flag เปิด — ปิดอยู่แล้วเว้นเป็น None (nullable) แทนที่จะเขียนค่าที่ยังไม่พร้อม
    # โชว์ต่อสาธารณะ (ดู server/config.py::STEALTH_ASSESSMENT_ENABLED, docs/adr/012)
    if stealth_enabled:
        run.net_impact_score = result.net_impact_score
        run.cognitive_score = result.cognitive_score
        run.rank = result.rank
    run.events_json = json.dumps(record.to_dict())
    run.synced_at = datetime.now(UTC)


def leaderboard(session: SessionModel) -> list[RunModel]:
    """จัดอันดับด้วย environmental_score (คะแนนรวมถ่วงน้ำหนัก — ดู core/scoring/rules.py)
    เป็นหลัก, distance_m เป็นตัวรอง — และ player_id เป็นตัวตัดสินสุดท้ายเมื่อคะแนน/ระยะเท่ากัน
    เป๊ะ ๆ (กันอันดับสลับไปมาทุกครั้งที่มี update ทั้งที่ผลไม่ได้เปลี่ยนจริง) ตาม docs/OVERVIEW.md
    """
    return (
        db.session.query(RunModel)
        .filter_by(session_id=session.id)
        .order_by(
            RunModel.environmental_score.desc(),
            RunModel.distance_m.desc(),
            RunModel.player_id,
        )
        .all()
    )


def leaderboard_payload(session: SessionModel) -> list[dict[str, Any]]:
    """แปลง leaderboard() เป็น dict ธรรมดา — ใช้ทั้งใน SocketIO emit และ JSON response

    มี player_id ติดไปด้วยเพื่อให้ dashboard ฝั่ง client ใช้เป็น key สำหรับ diff/update
    DOM ทีละแถวได้ (ไม่ต้อง render ตารางใหม่ทั้งหมดทุกครั้งที่มี event เข้ามา)
    """
    return [
        {
            "player_id": run.player_id,
            "player_name": run.player_name,
            "distance_m": run.distance_m,
            "respawn_count": run.respawn_count,
            "environmental_score": run.environmental_score,
            "status": run.status,
            # None ถ้า STEALTH_ASSESSMENT_ENABLED ปิดอยู่ตอน ingest — client ต้อง null-safe
            # อยู่แล้ว (เหมือน environmental_score ตอนยังไม่ finish)
            "net_impact_score": run.net_impact_score,
            "rank": run.rank,
        }
        for run in leaderboard(session)
    ]
