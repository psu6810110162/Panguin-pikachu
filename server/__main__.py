"""รันด้วย `python -m server` — เปิด dev server ที่ http://localhost:5000 (ตั้งค่า PORT
env var เพื่อเปลี่ยน port เช่นตอนที่ 5000 ชนกับ AirPlay Receiver ของ macOS)

allow_unsafe_werkzeug=True เพราะนี่คือ dev/demo server เท่านั้น (ตาม
docs/ENGINEERING_PLAN.md: localhost + ngrok/LAN สำหรับ demo — ไม่ deploy จริงจนกว่า
เสถียรแล้ว) ห้ามใช้ค่านี้ถ้า deploy ขึ้น production จริง
"""

import os

from server import create_app
from server.extensions import socketio

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app = create_app()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=port)
