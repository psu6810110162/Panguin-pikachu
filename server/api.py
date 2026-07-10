"""REST API — session lifecycle + run ingestion

Blueprint แยกจาก dashboard.py (หน้าเว็บ) ตามโครง server/{api,services,models,dashboard}/
ใน docs/ENGINEERING_PLAN.md
"""

import secrets
from typing import Any

from flask import Blueprint, current_app, jsonify, request
from flask import Response as FlaskResponse

from core.sync import SignedPayload, VerificationError
from server import services
from server.extensions import socketio
from server.models import PlayerModel, SessionModel

api = Blueprint("api", __name__, url_prefix="/api")

# Header ที่ครูต้องแนบสำหรับ endpoint ที่ใช้สิทธิ์เกินผู้เล่น (end/export) — ใช้ header
# ไม่ใช่ query string เพื่อไม่ให้ token ติดเข้า browser history/access log
TEACHER_TOKEN_HEADER = "X-Teacher-Token"


def _get_session_or_404(room_code: str) -> SessionModel:
    session = services.get_session_by_code(room_code)
    if session is None:
        raise _NotFound(f"no session with room_code={room_code!r}")
    return session


def require_teacher_token(session: SessionModel, provided: str | None) -> None:
    """ตรวจสิทธิ์ครูของ session — raise ForbiddenError ถ้า token ขาด/ผิด

    เทียบด้วย compare_digest กัน timing attack เช่นเดียวกับฝั่ง HMAC sync
    """
    if provided is None or not secrets.compare_digest(session.teacher_token, provided):
        raise ForbiddenError("missing or invalid teacher token")


class _NotFound(Exception):
    pass


class ForbiddenError(Exception):
    """คำขอที่ต้องมีสิทธิ์ครู (teacher_token) แต่ token ขาดหรือไม่ตรง"""


@api.errorhandler(_NotFound)
def _handle_not_found(error: _NotFound) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 404


@api.errorhandler(ForbiddenError)
def _handle_forbidden(error: ForbiddenError) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 403


@api.errorhandler(VerificationError)
def _handle_verification_error(error: VerificationError) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 401


@api.errorhandler(services.ValidationError)
def _handle_validation_error(error: services.ValidationError) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 400


@api.post("/sessions")
def create_session() -> tuple[FlaskResponse, int]:
    session = services.create_session()
    # teacher_token คืนครั้งเดียวที่นี่เท่านั้น — ผู้สร้าง session (ครู) ต้องเก็บไว้ใช้กับ
    # end/export/dashboard เอง ไม่มี endpoint ไหนคืนซ้ำ
    return jsonify({"room_code": session.room_code, "teacher_token": session.teacher_token}), 201


@api.post("/sessions/<room_code>/join")
def join_session(room_code: str) -> tuple[FlaskResponse, int]:
    session = _get_session_or_404(room_code)
    data: dict[str, Any] = request.get_json(force=True)
    player: PlayerModel = services.join_session(session, name=data["name"])
    return jsonify({"player_id": player.player_id}), 201


@api.post("/sessions/<room_code>/runs")
def ingest_run(room_code: str) -> tuple[FlaskResponse, int]:
    session = _get_session_or_404(room_code)
    data: dict[str, Any] = request.get_json(force=True)
    payload = SignedPayload(
        run_id=data["run_id"],
        timestamp=data["timestamp"],
        nonce=data["nonce"],
        body=data["body"],
        signature=data["signature"],
    )

    secret: bytes = current_app.config["SYNC_SECRET"]
    nonce_store = current_app.config["NONCE_STORE"]
    run = services.ingest_signed_run(session, payload, secret, nonce_store)

    socketio.emit(
        "leaderboard_update",
        services.leaderboard_payload(session),
        room=room_code,
    )
    return jsonify({"run_id": run.run_id, "status": run.status}), 200


@api.post("/sessions/<room_code>/end")
def end_session(room_code: str) -> tuple[FlaskResponse, int]:
    session = _get_session_or_404(room_code)
    require_teacher_token(session, request.headers.get(TEACHER_TOKEN_HEADER))
    services.end_session(session)
    socketio.emit("session_ended", {"room_code": room_code}, room=room_code)
    return jsonify({"room_code": room_code, "ended": True}), 200


@api.get("/sessions/<room_code>/leaderboard")
def get_leaderboard(room_code: str) -> tuple[FlaskResponse, int]:
    session = _get_session_or_404(room_code)
    return jsonify(services.leaderboard_payload(session)), 200
