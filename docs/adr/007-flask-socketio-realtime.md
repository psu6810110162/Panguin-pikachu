# ADR-007: Flask-SocketIO สำหรับ real-time dashboard (threading mode, ไม่ใช้ eventlet/gevent)

## Context

`docs/ENGINEERING_PLAN.md` ระบุ Flask-SocketIO ไว้ตั้งแต่ต้นสำหรับ push อัปเดตคะแนน/สถานะผู้เล่นขึ้น Teacher Dashboard แบบ real-time ระหว่างพัฒนา D9 มีทางเลือกที่ง่ายกว่าคือ REST polling ธรรมดา (dashboard JS เรียก `GET /leaderboard` ทุก 2-3 วินาที) ซึ่งไม่ต้องเพิ่ม dependency และ test ง่ายกว่า แต่เบี่ยงไปจากแผนที่ตกลงกันไว้แล้ว

## Decision

ใช้ **Flask-SocketIO จริงตามแผนเดิม** — server emit `leaderboard_update` เข้า room ของแต่ละ session ทุกครั้งที่มี run ใหม่เข้ามา ไม่ใช้ REST polling

เพื่อลดความซับซ้อนของ dependency ใช้ **`async_mode="threading"`** (ของ Flask-SocketIO) แทน `eventlet`/`gevent`:
- ไม่ต้องเพิ่ม dependency หนัก (eventlet/gevent) — ใช้ Werkzeug dev server + threading เฉย ๆ
- เพียงพอสำหรับ scale ที่ต้องการ (30-50 คนต่อห้องเรียน ตาม `docs/ENGINEERING_PLAN.md`)
- Test ได้จริงโดยไม่ต้องจำลอง network ผ่าน `flask_socketio.SocketIOTestClient` ซึ่งมากับ Flask-SocketIO อยู่แล้ว — ข้อกังวลเรื่อง "test ยาก" ไม่ใช่ปัญหาจริงอย่างที่คิดตอนแรก

## Consequences

- ได้: ตรงตามแผนเดิมที่ตกลงกันไว้ ครูเห็นคะแนนอัปเดตทันทีไม่ต้องรอ poll, test integration ได้ครบผ่าน `SocketIOTestClient` ไม่ต้องมี infra พิเศษ
- เสีย: เพิ่ม dependency (`flask-socketio`, `python-socketio`, `python-engineio`, `simple-websocket`) เข้า `server/requirements.txt` — แยกจาก `requirements.txt` ของเกม Kivy เพื่อไม่ให้ client build พ่วง dependency ฝั่งเว็บ
- `threading` mode ไม่เหมาะกับ production scale ใหญ่ (หลักพัน concurrent connections) — ถ้าต้อง scale เกินขนาดห้องเรียนเดียวจริง ๆ ค่อย revisit เป็น eventlet/gevent ตอนนั้น
