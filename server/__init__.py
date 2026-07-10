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
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")

    from server.api import api, health
    from server.dashboard import dashboard

    app.register_blueprint(api)
    app.register_blueprint(health)
    app.register_blueprint(dashboard)

    with app.app_context():
        db.create_all()

    return app
