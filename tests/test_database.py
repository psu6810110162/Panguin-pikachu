import core.database as database
from core.database import DatabaseManager


def _fresh_db(monkeypatch, tmp_path):
    """DatabaseManager เป็น singleton hardcode DB_FILE — reset instance +
    ชี้ DB_FILE ไปไฟล์ชั่วคราวต่อเทสต์ กัน state รั่วข้ามเทสต์"""
    db_file = tmp_path / "test_game.db"
    monkeypatch.setattr(database, "DB_FILE", str(db_file))
    DatabaseManager._instance = None
    db = DatabaseManager()
    db.connect()
    return db


def test_get_history_empty_when_no_runs(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    assert db.get_history("Nobody") == []


def test_get_history_single_run(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=100, gems=5)

    history = db.get_history("Alice")

    assert len(history) == 1
    assert history[0]["distance_m"] == 100
    assert history[0]["gems_collected"] == 5


def test_get_history_sorted_by_distance_not_date(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    # บันทึกตามลำดับเวลา: 100 -> 500 -> 300 — ผลต้องเรียงตามระยะ ไม่ใช่ลำดับที่บันทึก
    db.save_game_session("Alice", distance=100, gems=0)
    db.save_game_session("Alice", distance=500, gems=0)
    db.save_game_session("Alice", distance=300, gems=0)

    history = db.get_history("Alice")

    assert [row["distance_m"] for row in history] == [500, 300, 100]


def test_get_history_tie_breaks_by_played_at_desc(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=200, gems=0)
    assert db.conn is not None
    cursor = db.conn.cursor()
    cursor.execute("UPDATE sessions SET played_at = '2026-01-01 00:00:00'")
    db.conn.commit()

    db.save_game_session("Alice", distance=200, gems=0)
    cursor.execute(
        "UPDATE sessions SET played_at = '2026-06-01 00:00:00' "
        "WHERE played_at != '2026-01-01 00:00:00'"
    )
    db.conn.commit()

    history = db.get_history("Alice")

    assert [row["distance_m"] for row in history] == [200, 200]
    assert history[0]["played_at"] == "2026-06-01 00:00:00"
    assert history[1]["played_at"] == "2026-01-01 00:00:00"


def test_get_personal_best_returns_max_distance(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=100, gems=0)
    db.save_game_session("Alice", distance=500, gems=0)
    db.save_game_session("Alice", distance=300, gems=0)

    assert db.get_personal_best("Alice") == 500


def test_get_personal_best_zero_when_no_runs(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    assert db.get_personal_best("Nobody") == 0


def test_purchase_skin_deducts_once_and_grants_ownership(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=0, gems=15)

    assert db.purchase_skin("Alice", "Mask Dude", price=10) is True

    assert db.get_gem_balance("Alice") == 5
    assert db.is_skin_owned("Alice", "Mask Dude") is True


def test_purchase_skin_fails_and_leaves_balance_untouched_when_insufficient(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=0, gems=5)

    assert db.purchase_skin("Alice", "Mask Dude", price=10) is False

    assert db.get_gem_balance("Alice") == 5
    assert db.is_skin_owned("Alice", "Mask Dude") is False


def test_purchase_skin_is_idempotent_on_double_tap(monkeypatch, tmp_path):
    """Two purchase attempts in a row (simulated double-tap) must deduct the
    price exactly once — atomicity, not a UI debounce, is the guarantee."""
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=0, gems=10)

    first = db.purchase_skin("Alice", "Mask Dude", price=10)
    second = db.purchase_skin("Alice", "Mask Dude", price=10)

    assert first is True
    assert second is True
    assert db.get_gem_balance("Alice") == 0


def test_purchase_skin_never_drives_balance_negative(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session("Alice", distance=0, gems=3)

    db.purchase_skin("Alice", "Mask Dude", price=10)

    assert db.get_gem_balance("Alice") >= 0


def test_set_equipped_skin_rejects_unowned_skin(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.get_or_create_player("Alice")

    assert db.set_equipped_skin("Alice", "Mask Dude") is False
    assert db.get_equipped_skin("Alice") != "Mask Dude"


def test_set_equipped_skin_persists_for_owned_skin(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.add_owned_skin("Alice", "Mask Dude")

    assert db.set_equipped_skin("Alice", "Mask Dude") is True
    assert db.get_equipped_skin("Alice") == "Mask Dude"


def test_ensure_default_skin_is_idempotent_and_grants_ownership(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)

    db.ensure_default_skin("Alice", "Ninja Frog")
    db.ensure_default_skin("Alice", "Ninja Frog")

    assert db.is_skin_owned("Alice", "Ninja Frog") is True


def test_equipped_skin_round_trips_across_a_fresh_connection(monkeypatch, tmp_path):
    """Simulates app restart: equip, close the connection, reconnect, and the
    equipped skin must still be there — this is the persistence contract."""
    db = _fresh_db(monkeypatch, tmp_path)
    db.add_owned_skin("Alice", "Mask Dude")
    db.set_equipped_skin("Alice", "Mask Dude")
    db.close()

    db2 = DatabaseManager()
    db2.connect()

    assert db2.get_equipped_skin("Alice") == "Mask Dude"
