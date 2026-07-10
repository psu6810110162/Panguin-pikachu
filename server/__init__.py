"""Flask app factory — server/ import ได้เฉพาะ core/ (ห้าม import game/ เพราะลาก Kivy)
ดู docs/ENGINEERING_PLAN.md และ docs/adr/006-server-authoritative-scoring.md
"""

from flask import Flask

from core.sync import InMemoryNonceStore
from server.extensions import db, socketio

# TODO(D9 deploy): เปลี่ยนเป็นอ่านจาก env var ก่อน deploy จริง — ค่านี้ใช้ได้แค่ dev/demo
DEV_SYNC_SECRET = b"dev-secret-change-me"


def create_app(
    db_uri: str = "sqlite:///penguin_dash_server.db",
    sync_secret: bytes = DEV_SYNC_SECRET,
) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SYNC_SECRET"] = sync_secret
    app.config["NONCE_STORE"] = InMemoryNonceStore()

    db.init_app(app)
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")

    from server.api import api
    from server.dashboard import dashboard

    app.register_blueprint(api)
    app.register_blueprint(dashboard)

    with app.app_context():
        db.create_all()

    return app
