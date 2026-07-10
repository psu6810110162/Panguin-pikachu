import json

import pytest
from flask.testing import FlaskClient
from flask_socketio import SocketIOTestClient

from core.events import CheckpointReachedEvent, MissionCompleteEvent, RespawnEvent
from core.schema import RunRecord
from core.state import RunState
from core.sync import _compute_signature, sign_run_record
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


def _create_session(client: FlaskClient) -> tuple[str, str]:
    data = client.post("/api/sessions").json
    return data["room_code"], data["teacher_token"]


def _teacher(token: str) -> dict[str, str]:
    return {"X-Teacher-Token": token}


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


def test_create_session_returns_a_room_code_and_teacher_token(client: FlaskClient):
    response = client.post("/api/sessions")
    assert response.status_code == 201
    assert response.json["room_code"].startswith("PENGUIN-")
    assert len(response.json["teacher_token"]) >= 32


def test_join_session_returns_a_player_id(client: FlaskClient):
    room_code, _ = _create_session(client)

    response = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"})

    assert response.status_code == 201
    assert response.json["player_id"]


def test_join_unknown_session_returns_404(client: FlaskClient):
    response = client.post("/api/sessions/PENGUIN-0000/join", json={"name": "Alice"})
    assert response.status_code == 404


def test_ingest_run_scores_it_and_appears_on_the_leaderboard(client: FlaskClient):
    room_code, _ = _create_session(client)
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
    room_code, _ = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    body = _make_signed_run_body(player_id)
    body["body"] = body["body"].replace("FINISHED", "SYNCED")

    response = client.post(f"/api/sessions/{room_code}/runs", json=body)
    assert response.status_code == 401


def test_ingest_run_rejects_a_malformed_body_with_400(client: FlaskClient):
    # signature ถูกต้องแต่ body ไม่ใช่ RunRecord ที่ parse ได้ — ต้องเป็น 400 ไม่ใช่ 500
    room_code, _ = _create_session(client)

    payload = sign_run_record(RunRecord(run_id="run-1", player_id="p1"), DEV_SYNC_SECRET)
    broken = json.loads(payload.body)
    del broken["player_id"]
    body = json.dumps(broken, sort_keys=True)
    signature = _compute_signature(DEV_SYNC_SECRET, "run-1", payload.timestamp, payload.nonce, body)

    response = client.post(
        f"/api/sessions/{room_code}/runs",
        json={
            "run_id": "run-1",
            "timestamp": payload.timestamp,
            "nonce": payload.nonce,
            "body": body,
            "signature": signature,
        },
    )
    assert response.status_code == 400


def test_ingest_run_with_the_same_run_id_upserts_instead_of_duplicating(client: FlaskClient):
    room_code, _ = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))
    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    leaderboard = client.get(f"/api/sessions/{room_code}/leaderboard").json
    assert len(leaderboard) == 1


def test_ingest_does_not_resolve_a_player_name_across_sessions(client: FlaskClient):
    # player join ห้อง A แล้ว payload อ้าง player_id เดียวกันแต่ยิงเข้าห้อง B —
    # ต้องไม่ resolve ชื่อข้ามห้อง (fallback เป็น player_id ดิบแทน)
    room_a, _ = _create_session(client)
    room_b, _ = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_a}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    client.post(f"/api/sessions/{room_b}/runs", json=_make_signed_run_body(player_id))

    leaderboard = client.get(f"/api/sessions/{room_b}/leaderboard").json
    assert leaderboard[0]["player_name"] == player_id  # ไม่ใช่ "Alice"


# ── Teacher token auth ────────────────────────────────────


def test_end_session_requires_the_teacher_token(client: FlaskClient):
    room_code, token = _create_session(client)

    assert client.post(f"/api/sessions/{room_code}/end").status_code == 403
    assert (
        client.post(f"/api/sessions/{room_code}/end", headers=_teacher("wrong-token")).status_code
        == 403
    )

    response = client.post(f"/api/sessions/{room_code}/end", headers=_teacher(token))
    assert response.status_code == 200
    assert response.json["ended"] is True


def test_join_and_ingest_are_rejected_after_the_session_ends(client: FlaskClient):
    room_code, token = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]
    client.post(f"/api/sessions/{room_code}/end", headers=_teacher(token))

    join = client.post(f"/api/sessions/{room_code}/join", json={"name": "Bob"})
    assert join.status_code == 400

    ingest = client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))
    assert ingest.status_code == 400


def test_dashboard_index_offers_a_create_session_affordance(client: FlaskClient):
    response = client.get("/dashboard/")
    assert response.status_code == 200
    assert b"Create Session" in response.data


def test_dashboard_view_requires_the_teacher_token(client: FlaskClient):
    room_code, token = _create_session(client)

    assert client.get(f"/dashboard/{room_code}").status_code == 403
    assert client.get(f"/dashboard/{room_code}?token=wrong").status_code == 403

    response = client.get(f"/dashboard/{room_code}?token={token}")
    assert response.status_code == 200
    assert room_code.encode() in response.data


def test_leaderboard_payload_includes_player_id(client: FlaskClient):
    room_code, _ = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]
    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    leaderboard = client.get(f"/api/sessions/{room_code}/leaderboard").json
    assert leaderboard[0]["player_id"] == player_id


def test_leaderboard_tie_break_order_is_stable_across_calls(client: FlaskClient):
    room_code, _ = _create_session(client)
    alice_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]
    bob_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Bob"}).json["player_id"]

    # identical events/state for both -> identical environmental_score and distance_m,
    # so only the player_id tie-break decides the order
    client.post(
        f"/api/sessions/{room_code}/runs",
        json=_make_signed_run_body(alice_id, run_id="run-alice"),
    )
    client.post(
        f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(bob_id, run_id="run-bob")
    )

    first = client.get(f"/api/sessions/{room_code}/leaderboard").json
    second = client.get(f"/api/sessions/{room_code}/leaderboard").json
    expected_order = sorted([alice_id, bob_id])

    assert [row["player_id"] for row in first] == expected_order
    assert [row["player_id"] for row in second] == expected_order


def test_player_name_with_markup_is_never_interpreted_as_html(client: FlaskClient):
    room_code, token = _create_session(client)
    malicious_name = "<script>alert(1)</script>"
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": malicious_name}).json[
        "player_id"
    ]
    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    leaderboard = client.get(f"/api/sessions/{room_code}/leaderboard").json
    assert leaderboard[0]["player_name"] == malicious_name

    dashboard_html = client.get(f"/dashboard/{room_code}?token={token}").data.decode()
    # the raw tag must never appear unescaped in the server-rendered page - Jinja's
    # |tojson filter escapes it into the #initial-leaderboard <script> payload instead
    assert malicious_name not in dashboard_html
    assert "\\u003cscript\\u003e" in dashboard_html


def test_dashboard_export_requires_the_teacher_token_header(client: FlaskClient):
    room_code, token = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]
    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    assert client.get(f"/dashboard/{room_code}/export.csv").status_code == 403

    response = client.get(f"/dashboard/{room_code}/export.csv", headers=_teacher(token))
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "Alice" in response.get_data(as_text=True)


def test_socketio_emits_leaderboard_update_on_run_ingestion(
    client: FlaskClient, socket_client: SocketIOTestClient
):
    room_code, _ = _create_session(client)
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


def test_join_dashboard_for_an_unknown_room_does_not_receive_updates(
    client: FlaskClient, socket_client: SocketIOTestClient
):
    room_code, _ = _create_session(client)
    player_id = client.post(f"/api/sessions/{room_code}/join", json={"name": "Alice"}).json[
        "player_id"
    ]

    # join ห้องผี — server ต้องไม่ join_room ให้ จึงไม่ได้รับ update ของห้องจริงด้วย
    socket_client.emit("join_dashboard", {"room_code": "PENGUIN-0000"})
    socket_client.get_received()

    client.post(f"/api/sessions/{room_code}/runs", json=_make_signed_run_body(player_id))

    received = socket_client.get_received()
    assert [e for e in received if e["name"] == "leaderboard_update"] == []
