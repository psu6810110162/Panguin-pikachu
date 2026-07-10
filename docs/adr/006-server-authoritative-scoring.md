# ADR-006: Server-authoritative scoring

**Status:** Accepted

## Context

เกมเป็น Kivy `.exe` ที่รันบนเครื่องผู้เล่นแต่ละคน แล้วเชื่อมต่อไปหา server กลางแบบ Kahoot-style (หลายเครื่องพร้อมกันในห้องเรียน) ถ้าปล่อยให้ client เป็นคนตัดสินคะแนนสุดท้ายและส่งแค่ final score ไปให้ server เก็บ ผู้เล่นที่แก้ไฟล์ `.exe` หรือ intercept การส่งข้อมูลสามารถปลอมคะแนนได้ตรง ๆ (เช่นแก้ `score += 999999` ก่อนส่ง) ซึ่งทำลายความน่าเชื่อถือของ leaderboard ในห้องเรียน

## Decision

**Client ส่ง events ดิบ (raw telemetry: distance, items collected, policy choices, respawn events) — server เป็นผู้คำนวณ final score จริง** ผ่าน `core/scoring/` module เดียวกับที่ client ใช้ preview คะแนนระหว่างเล่น (import `core/` เท่านั้น ไม่ import `game/` เพราะ server ไม่มี Kivy)

Server เพิ่ม validation เบื้องต้นบนข้อมูลที่รับมา (เช่น distance กระโดดผิดปกติในเวลาสั้นเกินไป = ปฏิเสธ/flag) ก่อนคำนวณคะแนนเป็นทางการ

## Consequences

- ได้: leaderboard ที่แสดงบน Teacher Dashboard เชื่อถือได้ — คะแนนที่ผิดปกติจาก client ที่ถูกแก้ไขจะไม่ผ่านเข้าสู่คะแนนจริง, `core/scoring/` reuse ได้ทั้งสองฝั่งจึงไม่มี logic ซ้ำซ้อนให้ out-of-sync
- เสีย: server ต้องรับ-ประมวลผล event stream แทนที่จะรับแค่ final number (payload ใหญ่กว่าเล็กน้อย) — ยอมรับได้เพราะ event ต่อคนต่อ 2-5 วินาทีมีขนาดเล็ก (ไม่กี่ร้อยไบต์) ตามที่ระบุใน [ENGINEERING_PLAN.md](../ENGINEERING_PLAN.md)
- Client-side score ที่แสดงระหว่างเล่น (Final Report screen ก่อน sync) ถือเป็น **preview เท่านั้น** ค่าที่เป็นทางการคือค่าที่ server คำนวณและซิงก์กลับมา
