import pytest
from flask.testing import FlaskClient
from flask_socketio import SocketIOTestClient

from core.events import CheckpointReachedEvent, MissionCompleteEvent, RespawnEvent
from core.schema import RunRecord
from core.state import RunState
from core.sync import sign_run_record
from server import DEV_SYNC_SECRET, create_app
from server.extensions import db, socketio


@pytest.fixture(scope="module")
def app():
    """สร้าง Flask app แค่ครั้งเดียวต่อไฟล์ test — Flask-SocketIO ผูก @socketio.on(...)
    handler เข้ากับ socketio.server ตัวที่ init_app() สร้างไว้ ณ ตอน import module
    ครั้งแรกเท่านั้น (Python cache import) ถ้าเรียก create_app() ใหม่ทุก test (fixture
    ปกติแบบ function-scoped) จะได้ server ใหม่ที่ handler เดิมไม่ผูกด้วย — ห้อง
    join_dashboard จะเงียบ ไม่มี error ให้เห็น เป็น pattern เดียวกับที่แอปจริงรันเป็น
    process เดียวตลอดอายุ server อยู่แล้ว
    """
    flask_app = create_app(db_uri="sqlite:///:memory:")
    with flask_app.app_context():
        yield flask_app


@pytest.fixture(autouse=True)
def _reset_db(app):
    with app.app_context():
        yield
        db.session.remove()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def socket_client(app, client) -> SocketIOTestClient:
    sio = socketio.test_client(app, flask_test_client=client)
    yield sio
    sio.disconnect()


def _make_signed_run_body(player_id: str, run_id: str = "run-1") -> dict:
    record = RunRecord(run_id=run_id, player_id=player_id)
    record.record(CheckpointReachedEvent(timestamp=0.1, distance_m=100, checkpoint_index=1))
    record.record(
        RespawnEvent(
            timestamp=0.2,
            distance_m=100,
            checkpoint_col=1,
            checkpoint_row=0,
            respawn_count=1,
            score_penalty=0.1,
        )
    )
    record.record(
        MissionCompleteEvent(timestamp=0.3, distance_m=1000, module_index=0, mission_id="a")
    )
    record.advance_state(RunState.RUNNING)
    record.advance_state(RunState.BOSS, distance_m=1000)
    record.advance_state(RunState.FINISHED)

    payload = sign_run_record(record, DEV_SYNC_SECRET)
    return {
        "run_id": payload.run_id,
        "timestamp": payload.timestamp,
        "nonce": payload.nonce,
        "body": payload.body,
        "signature": payload.signature,
    }


def test_create_session_returns_a_room_code(client: FlaskClient):
    response = client.post("/api/sessions")
    assert response.status_code == 201
    assert response.json["room_code"].startswith("PENGUIN-")


def test_join_session_returns_a_player_id(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]

    response = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"})

    assert response.status_code == 201
    assert response.json["player_id"]


def test_join_unknown_session_returns_404(client: FlaskClient):
    response = client.post("/api/sessions/PENGUIN-0000/join", json={"name": "Alice"})
    assert response.status_code == 404


def test_ingest_run_scores_it_and_appears_on_the_leaderboard(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    body = _make_signed_run_body(player_id)
    response = client.post(f"/api/sessions/{room_code}/runs", json=body)
    assert response.status_code == 200
    assert response.json["status"] == "FINISHED"

    leaderboard = client.get(f"/api/sessions/{room_code}/leaderboard").json
    assert len(leaderboard) == 1
    assert leaderboard[0]["player_name"] == "Alice"
    assert leaderboard[0]["distance_m"] == 1000
    assert leaderboard[0]["respawn_count"] == 1


def test_ingest_run_rejects_a_tampered_payload(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    body = _make_signed_run_body(player_id)
    body["body"] = body["body"].replace("FINISHED", "SYNCED")

    response = client.post(f"/api/sessions/{room_code}/runs", json=body)
    assert response.status_code == 401


def test_ingest_run_with_the_same_run_id_upserts_instead_of_duplicating(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))
    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    leaderboard = client.get(f"/api/sessions/{room_code}/leaderboard").json
    assert len(leaderboard) == 1


def test_end_session_marks_it_ended(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]
    response = client.post(f"/api/sessions/{room_code}/end")
    assert response.status_code == 200
    assert response.json["ended"] is True


def test_dashboard_view_renders_for_a_known_session(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]
    response = client.get(f"/dashboard/{room_code}")
    assert response.status_code == 200
    assert room_code.encode() in response.data


def test_dashboard_export_csv_contains_the_leaderboard_row(client: FlaskClient):
    room_code = client.post("/api/sessions").json["room_code"]
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]
    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    response = client.get(f"/dashboard/{room_code}/export.csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "Alice" in response.get_data(as_text=True)


def test_socketio_emits_leaderboard_update_on_run_ingestion(
    client: FlaskClient, socket_client: SocketIOTestClient
):
    room_code = client.post("/api/sessions").json["room_code"]
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    socket_client.emit("join_dashboard", {"room_code": room_code})
    socket_client.get_received()  # drain the join ack, if any

    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    received = socket_client.get_received()
    updates = [e for e in received if e["name"] == "leaderboard_update"]
    assert len(updates) == 1
    assert updates[0]["args"][0][0]["player_name"] == "Alice"
