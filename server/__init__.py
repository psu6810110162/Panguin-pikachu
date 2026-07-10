"""Flask app factory — server/ import ได้เฉพาะ core/ (ห้าม import game/ เพราะลาก Kivy)
ดู docs/ENGINEERING_PLAN.md และ docs/adr/006-server-authoritative-scoring.md
"""

from flask import Flask

from core.sync import InMemoryNonceStore
from server.config import load_config
from server.extensions import db, limiter, migrate, socketio


def create_app(
    db_uri: str | None = None,
    sync_secret: bytes | None = None,
    rate_limit: str | None = None,
) -> Flask:
    """db_uri/sync_secret/rate_limit ที่ไม่ระบุ (None) จะ fallback ไปอ่านจาก env var ผ่าน
    load_config() — จำเป็นเพราะ `flask db migrate`/`upgrade` (Alembic CLI ผ่าน FLASK_APP=server)
    เรียก create_app() แบบไม่มี argument เลย ถ้า default เป็นค่า SQLite ตายตัวจะทำให้คำสั่งพวกนี้
    มองไม่เห็น DATABASE_URL ที่ตั้งไว้ (เช่นตอนรันใส่ Postgres จริงใน container) เลย
    """
    config = load_config()
    db_uri = db_uri if db_uri is not None else config.database_uri
    sync_secret = sync_secret if sync_secret is not None else config.sync_secret
    rate_limit = rate_limit if rate_limit is not None else config.rate_limit

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SYNC_SECRET"] = sync_secret
    app.config["NONCE_STORE"] = InMemoryNonceStore()
    app.config["RATELIMIT_DEFAULT"] = rate_limit

    db.init_app(app)
    # directory เป็น path relative จาก cwd ตอนรัน `flask db ...` (ไม่ใช่ relative จาก
    # app.root_path) — fix ไว้ที่ server/migrations/ เพื่อให้รันจาก repo root ได้ตรงๆ
    # โดยไม่ต้องพิมพ์ --directory ทุกครั้ง
    migrate.init_app(app, db, directory="server/migrations")
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
    """
    with app.app_context():
        db.create_all()
