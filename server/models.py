"""SQLAlchemy models — SQLite สำหรับ dev, PostgreSQL สำหรับ deploy (ดู docs/adr/005-sqlite-dev-postgres-deploy.md)

Teacher -> Session -> Players -> Runs -> (Reports คือ query/aggregate จาก Runs ไม่ใช่ table แยก)
"""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_code: Mapped[str] = mapped_column(unique=True, index=True)
    # secret ประจำ session สำหรับสิทธิ์ครู (end/export/dashboard) — room_code เดาง่าย
    # (9000 ค่า) จึงใช้เป็น identifier เท่านั้น ห้ามใช้แทนสิทธิ์
    teacher_token: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    ended_at: Mapped[datetime | None] = mapped_column(default=None)

    players: Mapped[list["PlayerModel"]] = relationship(back_populates="session")
    runs: Mapped[list["RunModel"]] = relationship(back_populates="session")

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


class PlayerModel(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    player_id: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    joined_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    session: Mapped[SessionModel] = relationship(back_populates="players")


class RunModel(Base):
    """ผล run ล่าสุดของผู้เล่นหนึ่งคนในหนึ่ง session — upsert ทับด้วย run_id เดียวกัน
    (idempotent ตาม docs/adr/006-server-authoritative-scoring.md)
    """

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    run_id: Mapped[str] = mapped_column(index=True)
    player_id: Mapped[str] = mapped_column(index=True)

    __table_args__ = (UniqueConstraint("session_id", "run_id"),)
    player_name: Mapped[str]

    status: Mapped[str] = mapped_column(default="ACTIVE")  # ACTIVE / RESPAWNING / FINISHED
    distance_m: Mapped[int] = mapped_column(default=0)
    respawn_count: Mapped[int] = mapped_column(default=0)
    environmental_score: Mapped[float | None] = mapped_column(default=None)
    mission_score: Mapped[float | None] = mapped_column(default=None)
    quiz_score: Mapped[float | None] = mapped_column(default=None)
    hake_gain: Mapped[float | None] = mapped_column(default=None)
    heat_controlled_pct: Mapped[float | None] = mapped_column(default=None)

    # Stealth Assessment (docs/adr/011, docs/adr/012) — nullable เสมอ: run เก่าไม่มีค่า
    # ไม่พัง, และ server/config.py::STEALTH_ASSESSMENT_ENABLED ปิดอยู่ก็ยังเว้นว่างได้
    # (evaluator derive เสมอ แต่ flag คุมว่า _apply_result จะเขียนลง column พวกนี้ไหม)
    net_impact_score: Mapped[float | None] = mapped_column(default=None)
    cognitive_score: Mapped[float | None] = mapped_column(default=None)
    rank: Mapped[str | None] = mapped_column(default=None)
    # balance content version ที่ run นี้อ้างอิง (core/schema.py::RunRecord.balance_version)
    balance_version: Mapped[str | None] = mapped_column(default=None)

    events_json: Mapped[str] = mapped_column(
        default="{}"
    )  # RunRecord.to_dict(), เก็บไว้เผื่อ debug/replay ทีหลัง
    synced_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    session: Mapped[SessionModel] = relationship(back_populates="runs")
