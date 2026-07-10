# Penguin Dash — Overview (NSC2026)

10-นาทีอ่านจบ: นี่คือเกมอะไร เล่นยังไง มีกี่หน้าจอ แต่ละหน้าทำอะไร

## แนวเกม

**Mission Runner เชิงการศึกษา** — ลูกผสมระหว่าง Kahoot (แข่งพร้อมกันทั้งห้อง, วัดความเข้าใจ) กับ Endless Runner (วิ่งเก็บของ หลบสิ่งกีดขวาง) แต่ **มีจุดจบ**: ไม่ใช่วิ่งไม่มีที่สิ้นสุด — มีต้น กลาง จบ มี Boss มี Mission Complete เพื่อให้กรรมการเห็นโครงสร้างเกมครบในเวลาสั้น ๆ และทั้งห้องเรียนจบ session พร้อมกันได้

**ธีม:** The Great Melt — ผู้เล่นควบคุมโดรน **P.E.N.G.U.I.N** วิ่งผ่านพื้นน้ำแข็งที่กำลังละลาย เก็บข้อมูลวิทยาศาสตร์ ตัดสินใจเชิงนโยบายด้านสิ่งแวดล้อม และต้องเข้าใจกลไกจริงของภาวะโลกร้อนเพื่อ "หักล้าง" ความเข้าใจผิด (misconceptions) ในบอสไฟต์

## Game Loop และกติกาหลัก

1. **Pre-test** — วัดความรู้ก่อนเล่น (ใช้คำนวณ Hake Gain ทีหลัง)
2. **วิ่ง 3 Modules** (0–333 / 334–666 / 667–1000 ม.) — แต่ละ module มี mission ย่อย (เช่น เก็บ Solar Cell 10 อัน, ช่วย Penguin 5 ตัว, ลด Heat <30%) และเปลี่ยน visual/สิ่งกีดขวาง
3. **Checkpoint ทุก 100 ม.** — pause ให้เลือก **policy** (ตัวเลือกเชิงนโยบาย) → ส่งผลต่อ **dual meters** (เช่น Heat / Ice Stability) → เห็น narrative consequence ทันที → checkpoint เป็นจุดบันทึกตำแหน่ง respawn ด้วย
4. **HP + Respawn (ไม่มี Game Over ถาวร)** — ชนสิ่งกีดขวาง = เสีย HP, HP หมด = เข้าสถานะ Respawn (รอ 3 วินาที + คะแนน −10%) แล้วเกิดใหม่ที่ checkpoint ล่าสุด เล่นต่อ คะแนนสะสมต่อได้ ธีมในเกม: โดรน "ถูกซ่อม/รีชาร์จ" แล้วกลับมาปฏิบัติภารกิจ
   - **ทำไม:** เล่นพร้อมกันทั้งห้อง คนพลาดช่วงต้นต้องไม่ถูกตัดออกจากเกม ทุกคนต้องมีส่วนร่วมจนจบ session — ดู [ADR-002](adr/002-respawn-checkpoint.md)
5. **เส้นชัย 1,000 ม. → Boss (2 เฟส)**
   - เฟส 1 Dodge/Heal — หลบท่าโจมตี เก็บของฮีล
   - เฟส 2 Debunk Misconceptions — ตอบคำถามหักล้างความเข้าใจผิด ตอบถูกลด HP บอส
   - ชนะ = Mission Complete
6. **Post-test** — คำนวณ **Hake Gain** = (post − pre) / (100 − pre) วัดว่าเกมเปลี่ยนความเข้าใจผู้เล่นได้จริงแค่ไหน
7. **Final Report (Impact Evidence)** — สรุประยะทาง, Heat controlled %, Mission/Quiz/Environmental Score, Hake Gain, Conceptual Shift (Old Model "Simple Melt" → New Model "Self-reinforcing Melt")
8. **Sync ไปเซิร์ฟเวอร์** — ข้อมูลรอบเล่นถูกเซ็นด้วย HMAC-SHA256 ส่งผ่าน HTTPS ไปหา Teacher Dashboard
9. **Teacher Dashboard (real-time)** — อาจารย์เห็นทุกคนในห้อง, กด End Session เมื่อจบ, export CSV ให้เกรด

## สารบัญหน้าจอ (Screen Inventory)

| # | หน้า | ทำอะไรได้ | ไปต่อที่ไหน | ข้อมูลเข้า/ออก |
|---|---|---|---|---|
| 1 | **Menu** | เริ่มเกม / join session / Shop / History / ตั้งค่าเสียง | Lobby, Shop, History | อ่าน last player name จาก SQLite |
| 2 | **Lobby + Pre-test** | กรอก Room Code เข้า session ของอาจารย์, ทำแบบทดสอบก่อนวิ่ง | Gameplay | ส่ง join request, บันทึกคะแนน pre-test ลง RunRecord |
| 3 | **Gameplay (HUD)** | วิ่ง-เก็บของ-หลบสิ่งกีดขวาง, Heat + dual meters, mission tracker, ระยะ/คะแนน real-time, overlay "Respawning..." 3 วิ | Policy popup, Boss, Post-test | อ่าน grid/meters state, เขียน event ทุกการกระทำ |
| 4 | **Policy Checkpoint (popup)** | หยุดเกมชั่วคราว เลือก policy เห็นผลต่อ meters + narrative consequence | กลับ Gameplay | เขียน policy-choice event ลง RunRecord |
| 5 | **Boss (ในหน้า Gameplay)** | เฟส 1 Dodge/Heal, เฟส 2 ตอบคำถาม Debunk | Post-test | เขียน boss-event, quiz answers |
| 6 | **Post-test** | ทำแบบทดสอบหลังชนะบอส | Final Report | บันทึกคะแนน post-test → คำนวณ Hake Gain |
| 7 | **Final Report (Impact Evidence)** | สรุประยะ, Heat %, Scores, Hake Gain, Conceptual Shift, ปุ่ม Run Again | Menu หรือ Gameplay ใหม่ | อ่านผลจาก `core/scoring/`, trigger sync ไป server |
| 8 | **Shop** | ใช้ Gems ปลดล็อกสกินตัวละคร | Menu | อ่าน/เขียน SQLite (gem_balance, player_skins) |
| 9 | **History** | ดูสถิติรอบก่อน ๆ | Menu | อ่าน SQLite (sessions, scores) |
| 10 | **Teacher Dashboard (เว็บ)** | ดู leaderboard สด, สถานะ ACTIVE/RESPAWNING/FINISHED ของทุกคน, กด End Session, Export CSV | — | รับข้อมูลผ่าน Socket.IO, อ่าน/เขียน server DB |

## Flow Diagram

```
Menu → Lobby + Pre-test
         │
         ▼
   ┌─────────────────────────────────────┐
   │  Gameplay: วิ่ง 3 modules            │
   │  ┌─────────────────────────────┐     │
   │  │ checkpoint 100m → policy     │◀──┐ │
   │  │       │                      │   │ │
   │  │       ▼                      │   │ │
   │  │  ชนสิ่งกีดขวาง → HP หมด?      │   │ │
   │  │       │ ใช่                  │   │ │
   │  │       ▼                      │   │ │
   │  │  Respawn (3s, −10%) ─────────┼───┘ │
   │  └─────────────────────────────┘     │
   └──────────────┬────────────────────────┘
                  ▼ เส้นชัย 1000m
              Boss (2 เฟส)
                  │ ชนะ
                  ▼
              Post-test
                  │
                  ▼
          Final Report (Impact Evidence)
                  │
                  ▼ sync (HMAC + HTTPS)
          Teacher Dashboard (real-time)
                  │ End Session
                  ▼
              Export CSV
```

## เอกสารที่เกี่ยวข้อง

- [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md) — แผนวิศวกรรม โครงสร้าง, module ownership, กติกา
- [TIMELINE.md](TIMELINE.md) — ตาราง 3 วันแบบละเอียด
- [adr/](adr/) — เหตุผลเบื้องหลังการตัดสินใจสถาปัตยกรรมแต่ละอัน
