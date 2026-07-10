"""รันด้วย `python -m server` — เปิด dev server ที่ http://localhost:5000 (ตั้งค่า PORT
env var เพื่อเปลี่ยน port เช่นตอนที่ 5000 ชนกับ AirPlay Receiver ของ macOS)

host="0.0.0.0" (bind ทุก interface ไม่ใช่แค่ 127.0.0.1) จำเป็นทั้งสองกรณี: (1) ให้เครื่อง
อื่นในห้องเรียนต่อผ่าน LAN เข้ามาได้ตาม docs/ENGINEERING_PLAN.md, (2) ให้ Docker port
mapping (host -> container) เข้าถึงได้ — ถ้า bind แค่ 127.0.0.1 ภายใน container จะเข้าจาก
ข้างนอก container ไม่ได้เลยแม้ port จะ map ถูกต้องแล้วก็ตาม

allow_unsafe_werkzeug=True เพราะนี่คือ dev/demo server เท่านั้น (ตาม
docs/ENGINEERING_PLAN.md: localhost + ngrok/LAN สำหรับ demo — ไม่ deploy จริงจนกว่า
เสถียรแล้ว) ห้ามใช้ค่านี้ถ้า deploy ขึ้น production จริง
"""

from server import create_app
from server.config import load_config
from server.extensions import socketio

if __name__ == "__main__":
    config = load_config()
    app = create_app(
        db_uri=config.database_uri, sync_secret=config.sync_secret, rate_limit=config.rate_limit
    )
    socketio.run(
        app,
        host="0.0.0.0",
        port=config.port,
        debug=True,
        allow_unsafe_werkzeug=True,
    )
