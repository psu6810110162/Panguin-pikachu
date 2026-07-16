"""Local SQLite Player Profile repository with migration and recovery."""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from infrastructure.paths import RuntimePaths

DATABASE_SCHEMA_VERSION = 1
SAVE_VERSION = 1


class DatabaseManager:
    _instance: DatabaseManager | None = None

    def __new__(cls, db_path: str | Path | None = None) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = None
            cls._instance.recovery_notice = None
            cls._instance._explicit_path = db_path is not None
            cls._instance.db_path = (
                Path(db_path) if db_path is not None else RuntimePaths.discover().data / "game.db"
            )
        elif db_path is not None and Path(db_path) != cls._instance.db_path:
            cls._instance.close()
            cls._instance._explicit_path = True
            cls._instance.db_path = Path(db_path)
        return cls._instance

    conn: sqlite3.Connection | None
    db_path: Path
    recovery_notice: str | None
    _explicit_path: bool

    @classmethod
    def reset_for_tests(cls) -> None:
        if cls._instance is not None:
            cls._instance.close()
        cls._instance = None

    def connect(self) -> None:
        if self.conn is not None:
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._explicit_path:
            self._migrate_legacy_database()
        try:
            self.conn = self._open_connection()
            self._verify_integrity()
            self._migrate_schema()
        except sqlite3.DatabaseError as error:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
            self._recover_corrupt_database(error)
            self.conn = self._open_connection()
            self._migrate_schema()

    def _open_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _verify_integrity(self) -> None:
        assert self.conn is not None
        row = self.conn.execute("PRAGMA quick_check").fetchone()
        if row is None or row[0] != "ok":
            detail = row[0] if row else "no result"
            raise sqlite3.DatabaseError(f"SQLite quick_check failed: {detail}")

    def _migrate_legacy_database(self) -> None:
        legacy = Path.cwd() / "game.db"
        if (
            not self.db_path.exists()
            and legacy.exists()
            and legacy.resolve() != self.db_path.resolve()
        ):
            shutil.copy2(legacy, self.db_path)

    def _backup_before_migration(self, old_version: int) -> None:
        assert self.conn is not None
        if not self.db_path.exists() or self.db_path.stat().st_size == 0:
            return
        has_user_schema = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'index') "
            "AND name NOT LIKE 'sqlite_%' LIMIT 1"
        ).fetchone()
        if has_user_schema is None:
            return
        backup_path = self.db_path.with_suffix(f".v{old_version}.backup.db")
        backup_tmp = backup_path.with_suffix(backup_path.suffix + ".tmp")
        backup = sqlite3.connect(backup_tmp)
        try:
            self.conn.backup(backup)
            backup.commit()
        finally:
            backup.close()
        os.replace(backup_tmp, backup_path)

    def _migrate_schema(self) -> None:
        assert self.conn is not None
        current = int(self.conn.execute("PRAGMA user_version").fetchone()[0])
        if current > DATABASE_SCHEMA_VERSION:
            raise sqlite3.DatabaseError(
                f"database schema {current} is newer than supported {DATABASE_SCHEMA_VERSION}"
            )
        if current < DATABASE_SCHEMA_VERSION:
            self._backup_before_migration(current)
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    gem_balance INTEGER DEFAULT 0,
                    equipped_skin TEXT DEFAULT 'default',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER REFERENCES players(id),
                    played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    duration_s REAL DEFAULT 0.0
                );
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER REFERENCES sessions(id),
                    distance_m INTEGER NOT NULL,
                    gems_collected INTEGER DEFAULT 0,
                    obstacles_cleared INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS player_skins (
                    player_id INTEGER REFERENCES players(id),
                    skin_id TEXT NOT NULL,
                    purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (player_id, skin_id)
                );
                CREATE TABLE IF NOT EXISTS app_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO app_metadata(key, value) VALUES ('save_version', ?)",
                (str(SAVE_VERSION),),
            )
            self.conn.execute(f"PRAGMA user_version={DATABASE_SCHEMA_VERSION}")

    def _recover_corrupt_database(self, error: sqlite3.DatabaseError) -> None:
        if self.db_path.exists():
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            corrupt = self.db_path.with_name(f"game.db.corrupt-{timestamp}")
            os.replace(self.db_path, corrupt)
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{self.db_path}{suffix}")
                if sidecar.exists():
                    os.replace(sidecar, Path(f"{corrupt}{suffix}"))
            self.recovery_notice = f"Recovered local save; corrupt copy: {corrupt.name}"
        else:
            self.recovery_notice = f"Created a new local save after error: {error}"

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def init_db(self) -> None:
        self.connect()

    def get_or_create_player(self, name: str) -> int:
        self.connect()
        assert self.conn is not None
        row = self.conn.execute("SELECT id FROM players WHERE name = ?", (name,)).fetchone()
        if row:
            return int(row["id"])
        with self.conn:
            cursor = self.conn.execute("INSERT INTO players (name) VALUES (?)", (name,))
        assert cursor.lastrowid is not None
        return int(cursor.lastrowid)

    def save_game_session(
        self, player_name: str, distance: int, gems: int, duration: float = 0.0
    ) -> None:
        player_id = self.get_or_create_player(player_name)
        assert self.conn is not None
        with self.conn:
            self.conn.execute(
                "UPDATE players SET gem_balance = gem_balance + ? WHERE id = ?",
                (gems, player_id),
            )
            cursor = self.conn.execute(
                "INSERT INTO sessions (player_id, duration_s) VALUES (?, ?)",
                (player_id, duration),
            )
            self.conn.execute(
                "INSERT INTO scores (session_id, distance_m, gems_collected) VALUES (?, ?, ?)",
                (cursor.lastrowid, distance, gems),
            )

    def get_gem_balance(self, player_name: str) -> int:
        self.connect()
        assert self.conn is not None
        row = self.conn.execute(
            "SELECT gem_balance FROM players WHERE name = ?", (player_name,)
        ).fetchone()
        return int(row["gem_balance"]) if row else 0

    def deduct_gems(self, player_name: str, amount: int) -> bool:
        if self.get_gem_balance(player_name) < amount:
            return False
        assert self.conn is not None
        with self.conn:
            self.conn.execute(
                "UPDATE players SET gem_balance = gem_balance - ? WHERE name = ?",
                (amount, player_name),
            )
        return True

    def get_personal_best(self, player_name: str) -> int:
        self.connect()
        assert self.conn is not None
        row = self.conn.execute(
            """
            SELECT MAX(s.distance_m) AS pb FROM scores s
            JOIN sessions ss ON s.session_id = ss.id
            JOIN players p ON ss.player_id = p.id WHERE p.name = ?
            """,
            (player_name,),
        ).fetchone()
        return int(row["pb"]) if row and row["pb"] else 0

    def get_history(self, player_name: str, limit: int = 100) -> list[dict[str, Any]]:
        self.connect()
        assert self.conn is not None
        rows = self.conn.execute(
            """
            SELECT ss.played_at, s.distance_m, s.gems_collected FROM scores s
            JOIN sessions ss ON s.session_id = ss.id
            JOIN players p ON ss.player_id = p.id WHERE p.name = ?
            ORDER BY s.distance_m DESC, ss.played_at DESC LIMIT ?
            """,
            (player_name, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_last_player_name(self) -> str:
        self.connect()
        assert self.conn is not None
        row = self.conn.execute(
            """
            SELECT p.name FROM players p JOIN sessions s ON p.id = s.player_id
            ORDER BY s.played_at DESC LIMIT 1
            """
        ).fetchone()
        return str(row["name"]) if row else "Penguin"

    def is_skin_owned(self, player_name: str, skin_id: str) -> bool:
        self.connect()
        assert self.conn is not None
        row = self.conn.execute(
            """
            SELECT 1 FROM player_skins ps JOIN players p ON ps.player_id = p.id
            WHERE p.name = ? AND ps.skin_id = ?
            """,
            (player_name, skin_id),
        ).fetchone()
        return row is not None

    def add_owned_skin(self, player_name: str, skin_id: str) -> None:
        player_id = self.get_or_create_player(player_name)
        assert self.conn is not None
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO player_skins (player_id, skin_id) VALUES (?, ?)",
                (player_id, skin_id),
            )
