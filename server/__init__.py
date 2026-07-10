"""Flask app factory — server/ import ได้เฉพาะ core/ (ห้าม import game/ เพราะลาก Kivy)
ดู docs/ENGINEERING_PLAN.md และ docs/adr/006-server-authoritative-scoring.md
"""

from flask import Flask

from core.sync import InMemoryNonceStore
from server.config import DEFAULT_DATABASE_URI, DEFAULT_SYNC_SECRET
from server.extensions import db, socketio


def create_app(
    db_uri: str = DEFAULT_DATABASE_URI,
    sync_secret: bytes = DEFAULT_SYNC_SECRET,
) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SYNC_SECRET"] = sync_secret
    app.config["NONCE_STORE"] = InMemoryNonceStore()

    db.init_app(app)
    # cors_allowed_origins="*" เป็น trade-off ที่ตั้งใจ: ตอน bind 127.0.0.1 ค่านี้แทบไม่มี
    # ผล แต่ตอนนี้ server bind 0.0.0.0 (LAN ห้องเรียน/Docker) แปลว่า "ทุก origin จากทุก
    # เครื่องในเน็ตเดียวกัน" จริง ๆ — ยอมรับได้เพราะ socket ปล่อยแค่ public scoreboard
    # (ดู server/dashboard.py) และไม่มี cookie-based auth ให้ CSRF ได้ ถ้า deploy จริง
    # ควรระบุ origin ของหน้า dashboard แทน "*"
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")

    from server.api import api, health
    from server.dashboard import dashboard

    app.register_blueprint(api)
    app.register_blueprint(health)
    app.register_blueprint(dashboard)

    with app.app_context():
        db.create_all()

    return app
