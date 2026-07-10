"""รันด้วย `python -m server` — เปิด dev server ที่ http://localhost:5000 (ตั้งค่า PORT
env var เพื่อเปลี่ยน port เช่นตอนที่ 5000 ชนกับ AirPlay Receiver ของ macOS)

host="0.0.0.0" (bind ทุก interface ไม่ใช่แค่ 127.0.0.1) จำเป็นทั้งสองกรณี: (1) ให้เครื่อง
อื่นในห้องเรียนต่อผ่าน LAN เข้ามาได้ตาม docs/ENGINEERING_PLAN.md, (2) ให้ Docker port
mapping (host -> container) เข้าถึงได้ — ถ้า bind แค่ 127.0.0.1 ภายใน container จะเข้าจาก
ข้างนอก container ไม่ได้เลยแม้ port จะ map ถูกต้องแล้วก็ตาม

debug/allow_unsafe_werkzeug ผูกกับ FLASK_DEBUG (default ปิด) — development only:
Werkzeug debugger เปิด RCE ผ่าน browser ได้ถ้ามี exception ห้าม copy pattern นี้ไป
production เด็ดขาด production ต้องใช้ WSGI server จริง (เช่น gunicorn + eventlet)
และ load_config() จะ refuse ที่จะ start ถ้า FLASK_DEBUG ปิดแต่ SYNC_SECRET ยังเป็น
ค่า default (กันลืมเปลี่ยนก่อนเปิดผ่าน ngrok/deploy)
"""

from server import create_app
from server.config import load_config
from server.extensions import socketio

if __name__ == "__main__":
    config = load_config()
    app = create_app(db_uri=config.database_uri, sync_secret=config.sync_secret)
    socketio.run(
        app,
        host="0.0.0.0",
        port=config.port,
        debug=config.debug,
        allow_unsafe_werkzeug=config.debug,  # dev only — ดู docstring ด้านบน
    )
