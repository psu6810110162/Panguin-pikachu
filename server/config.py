"""Config ของ server/ — ศูนย์กลางเดียวที่อ่าน environment variable

server/__main__.py เป็นแค่ bootstrap (สร้าง app แล้วรัน) ไม่ควรอ่าน os.environ เอง —
ที่นี่คือที่เดียวที่ทำหน้าที่นั้น เพื่อแยก "โหลด config" ออกจาก "เริ่ม process"
"""

import os
from dataclasses import dataclass

# ค่า default สำหรับ dev เท่านั้น — ต้อง override ด้วย env var จริงก่อน deploy ขึ้น production
DEFAULT_DATABASE_URI = "sqlite:///penguin_dash_server.db"
DEFAULT_SYNC_SECRET = b"dev-secret-change-me"
DEFAULT_PORT = 5000


@dataclass(frozen=True)
class Config:
    database_uri: str
    sync_secret: bytes
    port: int


def load_config() -> Config:
    """อ่านค่าจาก env var: DATABASE_URL, SYNC_SECRET, PORT — ไม่มีก็ใช้ default ของ dev"""
    database_uri = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URI)

    sync_secret_raw = os.environ.get("SYNC_SECRET")
    sync_secret = sync_secret_raw.encode() if sync_secret_raw else DEFAULT_SYNC_SECRET

    port = int(os.environ.get("PORT", str(DEFAULT_PORT)))

    return Config(database_uri=database_uri, sync_secret=sync_secret, port=port)
