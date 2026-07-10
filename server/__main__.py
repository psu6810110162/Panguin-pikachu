"""รันด้วย `python -m server` — เปิด dev server ที่ http://localhost:5000

allow_unsafe_werkzeug=True เพราะนี่คือ dev/demo server เท่านั้น (ตาม
docs/ENGINEERING_PLAN.md: localhost + ngrok/LAN สำหรับ demo — ไม่ deploy จริงจนกว่า
เสถียรแล้ว) ห้ามใช้ค่านี้ถ้า deploy ขึ้น production จริง
"""

from server import create_app
from server.extensions import socketio

if __name__ == "__main__":
    app = create_app()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
