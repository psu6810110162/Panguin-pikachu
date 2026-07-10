"""Flask extension instances — สร้างครั้งเดียวที่นี่ แล้ว init_app() ใน create_app()
(pattern มาตรฐานของ Flask-SQLAlchemy/Flask-SocketIO เพื่อเลี่ยง circular import)
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base ทั่วไปของ SQLAlchemy — ใช้แทน db.Model เฉยๆ เพราะ mypy resolve
    type ของ db.Model (สร้างแบบ dynamic โดย Flask-SQLAlchemy) ไม่ได้"""


db = SQLAlchemy(model_class=Base)
socketio = SocketIO()

# in-memory storage (ไม่ใช่ redis/db) — พอสำหรับ single-process server (ADR-007) และ
# trusted-LAN classroom deployment เดียวกับที่ InMemoryNonceStore (core/sync.py) ใช้อยู่แล้ว
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
