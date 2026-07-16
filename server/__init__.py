"""Flask app factory — server/ import ได้เฉพาะ core/ (ห้าม import game/ เพราะลาก Kivy)
ดู docs/ENGINEERING_PLAN.md และ docs/adr/006-server-authoritative-scoring.md
"""

import sqlalchemy as sa
from flask import Flask

from core.sync import InMemoryNonceStore
from server.config import load_config
from server.extensions import db, limiter, migrate, socketio


def create_app(
    db_uri: str | None = None,
    sync_secret: bytes | None = None,
    rate_limit: str | None = None,
    stealth_assessment_enabled: bool | None = None,
) -> Flask:
    """db_uri/sync_secret/rate_limit/stealth_assessment_enabled ที่ไม่ระบุ (None) จะ fallback
    ไปอ่านจาก env var ผ่าน load_config() — จำเป็นเพราะ `flask db migrate`/`upgrade`
    (Alembic CLI ผ่าน FLASK_APP=server) เรียก create_app() แบบไม่มี argument เลย ถ้า default
    เป็นค่า SQLite ตายตัวจะทำให้คำสั่งพวกนี้มองไม่เห็น DATABASE_URL ที่ตั้งไว้ (เช่นตอนรันใส่
    Postgres จริงใน container) เลย
    """
    config = load_config()
    db_uri = db_uri if db_uri is not None else config.database_uri
    sync_secret = sync_secret if sync_secret is not None else config.sync_secret
    rate_limit = rate_limit if rate_limit is not None else config.rate_limit
    stealth_assessment_enabled = (
        stealth_assessment_enabled
        if stealth_assessment_enabled is not None
        else config.stealth_assessment_enabled
    )

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SYNC_SECRET"] = sync_secret
    app.config["NONCE_STORE"] = InMemoryNonceStore()
    app.config["RATELIMIT_DEFAULT"] = rate_limit
    app.config["STEALTH_ASSESSMENT_ENABLED"] = stealth_assessment_enabled

    db.init_app(app)
    # directory เป็น path relative จาก cwd ตอนรัน `flask db ...` (ไม่ใช่ relative จาก
    # app.root_path) — fix ไว้ที่ server/migrations/ เพื่อให้รันจาก repo root ได้ตรงๆ
    # โดยไม่ต้องพิมพ์ --directory ทุกครั้ง
    migrate.init_app(app, db, directory="server/migrations")
    # cors_allowed_origins="*" เป็น trade-off ที่ตั้งใจ: ตอน bind 127.0.0.1 ค่านี้แทบไม่มี
    # ผล แต่ตอนนี้ server bind 0.0.0.0 (LAN ห้องเรียน/Docker) แปลว่า "ทุก origin จากทุก
    # เครื่องในเน็ตเดียวกัน" จริง ๆ — ยอมรับได้เพราะ socket ปล่อยแค่ public scoreboard
    # (ดู server/dashboard.py) และไม่มี cookie-based auth ให้ CSRF ได้ ถ้า deploy จริง
    # ควรระบุ origin ของหน้า dashboard แทน "*"
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")
    limiter.init_app(app)

    from server.api import api, health
    from server.dashboard import dashboard

    app.register_blueprint(api)
    app.register_blueprint(health)
    app.register_blueprint(dashboard)

    return app


def create_all_tables(app: Flask) -> None:
    """Bootstrap เฉพาะ DB ใหม่เอี่ยม (dev/test) — ไม่เรียกใน create_app() เอง เพราะ
    `flask db ...` (Alembic CLI) ก็ import create_app() ผ่าน FLASK_APP=server เหมือนกัน
    ถ้า create_all() ทำงานอัตโนมัติทุกครั้งที่สร้าง app จะสร้างตารางตาม model ปัจจุบันไปก่อน
    เสมอ ทำให้ `flask db migrate`/`upgrade` เจอ DB ที่ตรงกับ model อยู่แล้วตลอด (autogenerate
    ไม่เจอ diff, upgrade ชน "table already exists") — caller ที่ต้องการ auto-bootstrap จริง ๆ
    (server/__main__.py, tests/test_server.py) เรียกฟังก์ชันนี้เอง ส่วน production/Postgres
    ใช้ `flask db upgrade` แทน

    DB ที่ managed ด้วย migrations แล้ว (มีตาราง alembic_version) จะถูก skip ทั้งก้อน —
    ไม่งั้น container restart จะสร้างตารางใหม่ตาม model ปัจจุบันก่อน operator ได้รัน
    `flask db upgrade` แล้ว upgrade ตัวจริงจะชน "table already exists" ทีหลัง

    Assumption ที่รู้อยู่: การมี alembic_version ไม่การันตีว่า schema สมบูรณ์ (migration
    ล้มกลางทาง/stamp ผิดยังหลุดผ่านได้) — การเช็ค revision เทียบ head เต็มรูปแบบเกิน
    scope ตอนนี้ จดเป็น follow-up ลำดับ deploy ที่ถูกต้องดูใน README "Schema migrations"
    """
    with app.app_context():
        if sa.inspect(db.engine).has_table("alembic_version"):
            app.logger.info(
                "create_all_tables: skipped — DB is migration-managed "
                "(alembic_version exists); use `flask db upgrade` for schema changes"
            )
            return
        db.create_all()
