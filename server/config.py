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
# 60/min กัน client bug/loop ยิงรัว ๆ ใส่ server โดยไม่ตั้งใจ — ไม่ใช่ DDoS protection จริงจัง
# (สมมติฐาน trusted LAN, ดู docs/ENGINEERING_PLAN.md)
#
# Known limitation: limit นับต่อ IP (get_remote_address) — ถ้า client หลายคนอยู่หลัง
# NAT/egress IP เดียวกัน (เช่นทั้งห้อง 30+ คนผ่าน router โรงเรียนตัวเดียว หรือ deploy
# บน cloud ที่มี proxy คั่น) ทุกคนจะแชร์โควตาเดียวกัน นักเรียนคนหนึ่งยิงรัวทำเพื่อน
# โดน 429 ได้ — ใน LAN ห้องเรียนที่ต่อตรง (ต่าง IP กัน) ไม่มีปัญหานี้ ถ้า deploy จริง
# ต้อง scale ค่านี้ตามขนาดห้อง หรือเปลี่ยน key function เป็นต่อ player/session
DEFAULT_RATE_LIMIT = "60 per minute"


@dataclass(frozen=True)
class Config:
    database_uri: str
    sync_secret: bytes
    port: int
    rate_limit: str
    debug: bool
    stealth_assessment_enabled: bool


def load_config() -> Config:
    """อ่านค่าจาก env var: DATABASE_URL, SYNC_SECRET, PORT, RATE_LIMIT, FLASK_DEBUG,
    STEALTH_ASSESSMENT_ENABLED — ไม่มีก็ใช้ default ของ dev

    Raises:
        RuntimeError: FLASK_DEBUG ไม่เปิดแต่ SYNC_SECRET ยังเป็นค่า default — ค่า default
            อยู่ใน public repo ใครก็ forge signed payload ได้ ทำลาย server-authoritative
            scoring ทั้งระบบ (ADR-006) guard นี้กัน "ลืมเปลี่ยนก่อนเปิดผ่าน ngrok/deploy"
            ซึ่งเป็นความผิดพลาดที่เงียบและเกิดง่ายที่สุด
    """
    database_uri = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URI)

    sync_secret_raw = os.environ.get("SYNC_SECRET")
    sync_secret = sync_secret_raw.encode() if sync_secret_raw else DEFAULT_SYNC_SECRET

    port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    rate_limit = os.environ.get("RATE_LIMIT", DEFAULT_RATE_LIMIT)

    # debug ต้อง opt-in เสมอ (FLASK_DEBUG=1) — ค่า default ปลอดภัยไว้ก่อน เพราะ Werkzeug
    # debugger รันโค้ดจาก browser ได้ ถ้าเผลอเปิดผ่าน ngrok/LAN คือช่อง RCE ตรง ๆ
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}

    # คุมแค่ persist/API/dashboard ของ Stealth Assessment fields (net_impact_score/
    # cognitive_score/rank) — evaluator ยัง derive ค่าพวกนี้เสมอไม่ว่า flag จะเป็นอะไร
    # (ดู core/scoring/evaluator.py, docs/adr/012) ปิดโดย default จนกว่าทีมจะพร้อมโชว์
    stealth_assessment_enabled = os.environ.get("STEALTH_ASSESSMENT_ENABLED", "0").lower() in {
        "1",
        "true",
        "yes",
    }

    if not debug and sync_secret == DEFAULT_SYNC_SECRET:
        raise RuntimeError(
            "SYNC_SECRET is still the public dev default while FLASK_DEBUG is off — "
            "set SYNC_SECRET to a real secret (e.g. `export SYNC_SECRET=$(python -c "
            "'import secrets; print(secrets.token_hex(32))')`) or set FLASK_DEBUG=1 "
            "for local development"
        )

    return Config(
        database_uri=database_uri,
        sync_secret=sync_secret,
        port=port,
        rate_limit=rate_limit,
        debug=debug,
        stealth_assessment_enabled=stealth_assessment_enabled,
    )
