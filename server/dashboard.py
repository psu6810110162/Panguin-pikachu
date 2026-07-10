"""Teacher Dashboard — หน้าเว็บ (Jinja) + Export CSV + SocketIO room สำหรับ real-time update

MVP ตาม docs/TIMELINE.md: ตารางผู้เล่น + End Session + Export CSV
(ตัด replay timeline ออกเป็น bonus หลัง demo — ดู docs/ENGINEERING_PLAN.md)
"""

import csv
import io

from flask import Blueprint, Response, render_template
from flask_socketio import join_room

from server import services
from server.extensions import socketio

dashboard = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard.get("/")
def index() -> str:
    return render_template("index.html")


@dashboard.get("/<room_code>")
def view(room_code: str) -> str | tuple[str, int]:
    session = services.get_session_by_code(room_code)
    if session is None:
        return f"no session with room_code={room_code!r}", 404

    return render_template(
        "dashboard.html",
        room_code=room_code,
        leaderboard=services.leaderboard_payload(session),
    )


@dashboard.get("/<room_code>/export.csv")
def export_csv(room_code: str) -> Response:
    session = services.get_session_by_code(room_code)
    if session is None:
        return Response(f"no session with room_code={room_code!r}", status=404)

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


@socketio.on("join_dashboard")
def handle_join_dashboard(data: dict[str, str]) -> None:
    join_room(data["room_code"])
