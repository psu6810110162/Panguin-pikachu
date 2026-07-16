import sqlite3

import pytest

from infrastructure.database import (
    DATABASE_SCHEMA_VERSION,
    SAVE_VERSION,
    DatabaseManager,
    UnsupportedSchemaVersionError,
)


def _fresh_db(monkeypatch, tmp_path):
    """Use an isolated writable database for every test."""
    db_file = tmp_path / "test_game.db"
    DatabaseManager.reset_for_tests()
    db = DatabaseManager(db_file)
    db.connect()
    return db


def test_database_versions_are_recorded(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    assert db.conn is not None
    assert db.conn.execute("PRAGMA user_version").fetchone()[0] == DATABASE_SCHEMA_VERSION
    row = db.conn.execute("SELECT value FROM app_metadata WHERE key = 'save_version'").fetchone()
    assert row[0] == str(SAVE_VERSION)


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


def test_corrupted_database_is_renamed_and_recovered(monkeypatch, tmp_path):
    db_file = tmp_path / "game.db"
    db_file.write_bytes(b"not a sqlite database")
    DatabaseManager.reset_for_tests()

    db = DatabaseManager(db_file)
    db.connect()

    assert db.recovery_notice is not None
    assert db.get_history("Nobody") == []
    assert list(tmp_path.glob("game.db.corrupt-*"))


def test_newer_schema_is_not_renamed_or_recovered(tmp_path):
    db_file = tmp_path / "future.db"
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA user_version=999")
    conn.commit()
    conn.close()

    DatabaseManager.reset_for_tests()
    db = DatabaseManager(db_file)
    with pytest.raises(UnsupportedSchemaVersionError, match="newer"):
        db.connect()

    assert db.recovery_notice is not None
    assert "newer game version" in db.recovery_notice
    assert db_file.exists()
    assert not list(tmp_path.glob("future.db.corrupt-*"))


def test_terminal_reason_and_state_are_persisted(monkeypatch, tmp_path):
    db = _fresh_db(monkeypatch, tmp_path)
    db.save_game_session(
        "Alice", distance=42, gems=1, run_state="FINISHED", terminal_reason="hearts"
    )

    history = db.get_history("Alice")

    assert history[0]["run_state"] == "FINISHED"
    assert history[0]["terminal_reason"] == "hearts"
