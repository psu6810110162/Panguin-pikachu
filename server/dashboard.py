"""Teacher Dashboard — หน้าเว็บ (Jinja) + Export CSV + SocketIO room สำหรับ real-time update

MVP ตาม docs/TIMELINE.md: ตารางผู้เล่น + End Session + Export CSV
(ตัด replay timeline ออกเป็น bonus หลัง demo — ดู docs/ENGINEERING_PLAN.md)

การเข้าถึง: view/export/end ต้องมี teacher_token (ดู server/api.py) ส่วน
GET /api/sessions/<code>/leaderboard และ SocketIO ยังเปิด — ข้อมูลชุดเดียวกับที่ฉาย
บนโปรเจกเตอร์หน้าห้องอยู่แล้ว จึงยอมรับได้ใน MVP (จดเป็น known limitation)
"""

import csv
import io

from flask import Blueprint, Response, render_template, request
from flask_socketio import join_room

from server import services
from server.api import TEACHER_TOKEN_HEADER, ForbiddenError, require_teacher_token
from server.extensions import socketio

dashboard = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard.errorhandler(ForbiddenError)
def _handle_forbidden(error: ForbiddenError) -> tuple[str, int]:
    return str(error), 403


@dashboard.get("/")
def index() -> str:
    return render_template("index.html")


@dashboard.get("/<room_code>")
def view(room_code: str) -> str | tuple[str, int]:
    session = services.get_session_by_code(room_code)
    if session is None:
        return f"no session with room_code={room_code!r}", 404

    # จุดเดียวที่รับ token ทาง query string — การเปิดหน้าแรกจาก browser แนบ header
    # เองไม่ได้ known limitation: token โผล่ใน URL หนึ่งครั้ง (history/proxy log)
    # ฝั่ง JS ต้อง strip ออกจาก URL ทันทีหลังโหลด (history.replaceState) แล้วใช้
    # header กับทุก request ถัดไป
    require_teacher_token(session, request.args.get("token"))

    return render_template(
        "dashboard.html",
        room_code=room_code,
        teacher_token=session.teacher_token,
        leaderboard=services.leaderboard_payload(session),
    )


@dashboard.get("/<room_code>/export.csv")
def export_csv(room_code: str) -> Response:
    session = services.get_session_by_code(room_code)
    if session is None:
        return Response(f"no session with room_code={room_code!r}", status=404)
    require_teacher_token(session, request.headers.get(TEACHER_TOKEN_HEADER))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["player_name", "distance_m", "respawn_count", "environmental_score", "status"])
    for row in services.leaderboard_payload(session):
        writer.writerow(
            [
                row["player_name"],
                row["distance_m"],
                row["respawn_count"],
                row["environmental_score"],
                row["status"],
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={room_code}-report.csv"},
    )


# Socket contract: ทาง socket มี event ขาออกแค่ leaderboard_update / session_ended
# (public scoreboard — ข้อมูลเดียวกับที่ฉายโปรเจกเตอร์) ไม่มี privileged action ใด ๆ
# ผ่าน socket — end/export เป็น REST ที่ตรวจ teacher_token เท่านั้น ห้ามเพิ่ม event
# ที่เกินขอบเขตนี้โดยไม่เพิ่ม auth ฝั่ง socket ก่อน
@socketio.on("join_dashboard")
def handle_join_dashboard(data: dict[str, str]) -> None:
    # เช็คว่า session มีจริงก่อน join — ไม่ให้เข้า room ผี ๆ ตาม string ที่ client ส่งมา
    # (สอดคล้องกับ REST ที่ทุก endpoint มี _get_session_or_404)
    room_code = data.get("room_code", "")
    if services.get_session_by_code(room_code) is None:
        return
    join_room(room_code)
