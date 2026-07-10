"""REST API — session lifecycle + run ingestion

Blueprint แยกจาก dashboard.py (หน้าเว็บ) ตามโครง server/{api,services,models,dashboard}/
ใน docs/ENGINEERING_PLAN.md
"""

from typing import Any

from flask import Blueprint, current_app, jsonify, request
from flask import Response as FlaskResponse
from flask_limiter.errors import RateLimitExceeded

from core.sync import SignedPayload, VerificationError
from server import services
from server.extensions import limiter, socketio
from server.models import PlayerModel, SessionModel

api = Blueprint("api", __name__, url_prefix="/api/v1")
# ค่า limit มาจาก app.config["RATELIMIT_DEFAULT"] (ตั้งจาก create_app(rate_limit=...)) อ่าน
# แบบ lambda เพื่อให้ยังปรับได้ต่อ-app instance (เช่น test ตั้ง limit ต่ำเพื่อ trigger 429 ได้ไว)
# แทนที่จะ fix ค่าตายตัวตอน import module
limiter.limit(lambda: current_app.config["RATELIMIT_DEFAULT"])(api)

# Blueprint แยกไม่มี url_prefix เพราะ health check ควรอยู่ที่ /healthz เฉยๆ (ตำแหน่งมาตรฐาน
# ที่ Docker HEALTHCHECK / Railway / load balancer คาดหวัง) ไม่ใช่ /api/healthz
health = Blueprint("health", __name__)


@health.get("/healthz")
def healthz() -> tuple[FlaskResponse, int]:
    """Health check เปล่า ๆ ไม่แตะ DB/logic ใด ๆ — endpoint เดียวที่ Docker HEALTHCHECK,
    Compose depends_on.condition, และ future Railway health probe ควรชี้มาที่นี่ แทนที่จะ
    ยิงใส่ route จริงอย่าง /dashboard/ ที่มี application logic ปนอยู่
    """
    return jsonify({"status": "ok"}), 200


def _get_session_or_404(room_code: str) -> SessionModel:
    session = services.get_session_by_code(room_code)
    if session is None:
        raise _NotFound(f"no session with room_code={room_code!r}")
    return session


class _NotFound(Exception):
    pass


@api.errorhandler(_NotFound)
def _handle_not_found(error: _NotFound) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 404


@api.errorhandler(VerificationError)
def _handle_verification_error(error: VerificationError) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 401


@api.errorhandler(services.ValidationError)
def _handle_validation_error(error: services.ValidationError) -> tuple[FlaskResponse, int]:
    return jsonify({"error": str(error)}), 400


@api.errorhandler(RateLimitExceeded)
def _handle_rate_limit_exceeded(error: RateLimitExceeded) -> tuple[FlaskResponse, int]:
    return jsonify({"error": "rate limit exceeded, slow down"}), 429


@api.post("/sessions")
def create_session() -> tuple[FlaskResponse, int]:
    session = services.create_session()
    return jsonify({"room_code": session.room_code}), 201


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
    # ingest ต้อง commit ก่อน emit เสมอ (ตอนนี้ ingest_signed_run() commit ภายในตัวมันเองอยู่
    # แล้ว) — ถ้า emit ล้มเหลว dashboard แค่ค้างข้อมูลเก่าไปจนกว่า update รอบถัดไป แต่ข้อมูล
    # ใน DB ยังถูกต้องเสมอ ห้ามสลับลำดับเป็น emit ก่อน commit เด็ดขาด เพราะจะทำให้ dashboard
    # โชว์ค่าที่ยังไม่ถูก persist จริง (ถ้า commit ล้มเหลวทีหลัง)
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
    services.end_session(session)
    socketio.emit("session_ended", {"room_code": room_code}, room=room_code)
    return jsonify({"room_code": room_code, "ended": True}), 200


@api.get("/sessions/<room_code>/leaderboard")
def get_leaderboard(room_code: str) -> tuple[FlaskResponse, int]:
    session = _get_session_or_404(room_code)
    return jsonify(services.leaderboard_payload(session)), 200
