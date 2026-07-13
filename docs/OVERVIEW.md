# Penguin Dash — Overview (NSC2026)

10-นาทีอ่านจบ: นี่คือเกมอะไร เล่นยังไง มีกี่หน้าจอ แต่ละหน้าทำอะไร

## แนวเกม

**Mission Runner เชิงการศึกษา** — ลูกผสมระหว่าง Kahoot (แข่งพร้อมกันทั้งห้อง, วัดความเข้าใจ) กับ Endless Runner (วิ่งเก็บของ หลบสิ่งกีดขวาง) แต่ **มีจุดจบ**: ไม่ใช่วิ่งไม่มีที่สิ้นสุด — มีต้น กลาง จบ มี Boss มี Mission Complete เพื่อให้กรรมการเห็นโครงสร้างเกมครบในเวลาสั้น ๆ และทั้งห้องเรียนจบ session พร้อมกันได้

**ธีม:** The Great Melt — ผู้เล่นควบคุมโดรน **P.E.N.G.U.I.N** วิ่งผ่านพื้นน้ำแข็งที่กำลังละลาย เก็บข้อมูลวิทยาศาสตร์ ตัดสินใจเชิงนโยบายด้านสิ่งแวดล้อม และต้องเข้าใจกลไกจริงของภาวะโลกร้อนเพื่อ "หักล้าง" ความเข้าใจผิด (misconceptions) ในบอสไฟต์

## Game Loop และกติกาหลัก

1. **Pre-test** — วัดความรู้ก่อนเล่น (ใช้คำนวณ Hake Gain ทีหลัง)
2. **วิ่ง 10 โซน** (Zone-Based Spawning, โซนละ 100 ม.) — โซน 1–3 หมวดสาเหตุ / 4–6 ผลกระทบ / 7–10 การแก้ปัญหา (framing "3 modules" เดิม map ลงบนหมวดนี้) เก็บ **ไอเทมวิทยาศาสตร์** (Albedo Data, Methane Core, Eco-Seed) ใส่ inventory 3 ช่อง
3. **Y-Junction ทุกโซน (1 ครั้ง/โซน)** — กระโดดขึ้นบล็อก (หยุดละลายชั่วคราว) เลือก **policy** ด้วยลูกศรซ้าย/ขวา → ส่งผลต่อ **dual meters: Heat Meter + Capitalist Anger** (ฐาน 100, หลอดใดแตะ 100 = Game Over) → เห็น narrative consequence → กลับ endless-run
4. **หัวใจ 5 ดวง + Checkpoint/Respawn** — ตกเหว = −1 หัวใจ + respawn ที่ checkpoint ล่าสุด (reuse ADR-002); **หัวใจหมด หรือ หลอดแตะ 100 = Game Over จริง** (GDD V.2). Eco-Seed (Spacebar) ลด Heat + ซ่อมบล็อก
   - **ทำไมเปลี่ยนเป็นมี Game Over:** GDD V.2 เน้น stakes จริงหนุน Stealth Assessment — ดู [ADR-010](adr/010-health-respawn-state-model.md) (checkpoint/respawn/`respawn_count` เดิมยัง reuse ครบ)
5. **เส้นชัย 1,000 ม. → Boss: Carbon Baron (3 เวฟ)** — 980–990m warning banner; แต่ละเวฟยิง Problem Wall (Fake News) + แยก 2 เลนไอเทม ผู้เล่นเลือกไอเทมที่แก้ได้ถูก (Wave1 Albedo / Wave2 Methane / Wave3 Eco-Seed) เกราะ 3 ขีด ตอบถูกครบ = ชนะ; ตอบผิด −1 หัวใจ
6. **Post-test** — คำนวณ **Hake Gain** = (post − pre) / (100 − pre)
7. **Final Report + Systemic Report Card (DAG)** — สรุประยะ, Heat controlled %, Mission/Quiz/Environmental Score, Hake Gain, Conceptual Shift **บวก** Auto-Generated DAG (13 edge เขียว/แดง + tooltip เฉลย) และ **"อุณหภูมิที่กอบกู้ได้" + rank (S/A)** ตาม Stealth Assessment — ดู [GAME_DESIGN.md](GAME_DESIGN.md), [ADR-011](adr/011-learning-evaluation-pipeline.md)
8. **Sync ไปเซิร์ฟเวอร์** — ข้อมูลรอบเล่นถูกเซ็นด้วย HMAC-SHA256 ส่งผ่าน HTTPS ไปหา Teacher Dashboard
9. **Teacher Dashboard (real-time)** — อาจารย์เห็นทุกคนในห้อง, กด End Session เมื่อจบ, export CSV ให้เกรด

## สารบัญหน้าจอ (Screen Inventory)

| # | หน้า | ทำอะไรได้ | ไปต่อที่ไหน | ข้อมูลเข้า/ออก |
|---|---|---|---|---|
| 1 | **Menu** | เริ่มเกม / join session / Shop / History / ตั้งค่าเสียง | Lobby, Shop, History | อ่าน last player name จาก SQLite |
| 2 | **Lobby + Pre-test** | กรอก Room Code เข้า session ของอาจารย์, ทำแบบทดสอบก่อนวิ่ง | Gameplay | ส่ง join request, บันทึกคะแนน pre-test ลง RunRecord |
| 3 | **Gameplay (HUD)** | วิ่ง-เก็บของ-หลบสิ่งกีดขวาง, **Heat Meter + Capitalist Anger** bars, **หัวใจ 5 ดวง**, inventory 3 ช่อง, ระยะ/คะแนน real-time, overlay "Respawning..." | Y-Junction, Boss, Post-test | อ่าน grid/meters/hearts state, เขียน event ทุกการกระทำ |
| 4 | **Y-Junction (บล็อก + popup)** | กระโดดขึ้นบล็อก, เลือก policy ←/→ เห็นผลต่อหลอดคู่ + narrative | กลับ Gameplay | เขียน `PolicyChoiceEvent` (meter_deltas) ลง RunRecord |
| 5 | **Boss: Carbon Baron (ในหน้า Gameplay)** | 3 เวฟ, Problem Wall + เลือกเลนไอเทม (Albedo/Methane/Eco-Seed), เกราะ 3 ขีด | Post-test | เขียน `BossPhaseEvent` × 3 (decision 11–13) |
| 6 | **Post-test** | ทำแบบทดสอบหลังชนะบอส | Report Card | บันทึกคะแนน post-test → คำนวณ Hake Gain |
| 7 | **Report Card + Final Report (Impact Evidence)** | สรุประยะ, Heat %, Scores, Hake Gain, Conceptual Shift, **DAG 13 edge + tooltip**, **อุณหภูมิที่กอบกู้ได้ + rank S/A**, ปุ่ม Run Again | Menu หรือ Gameplay ใหม่ | อ่านผลจาก `core/scoring/` (rules+stealth+dag), trigger sync |
| 8 | **Shop** | ใช้ Gems ปลดล็อกสกินตัวละคร | Menu | อ่าน/เขียน SQLite (gem_balance, player_skins) |
| 9 | **History** | ดูสถิติรอบก่อน ๆ | Menu | อ่าน SQLite (sessions, scores) |
| 10 | **Teacher Dashboard (เว็บ)** | ดู leaderboard สด, สถานะ ACTIVE/RESPAWNING/FINISHED ของทุกคน, กด End Session, Export CSV | — | รับข้อมูลผ่าน Socket.IO, อ่าน/เขียน server DB |

## Flow Diagram

```
Menu → Lobby + Pre-test
         │
         ▼
   ┌──────────────────────────────────────────┐
   │  Gameplay: วิ่ง 10 โซน × 100m             │
   │  ┌────────────────────────────────┐       │
   │  │ Y-Junction (1/โซน) → policy ←/→ │◀──┐   │
   │  │       │ meter_deltas            │   │   │
   │  │       ▼                         │   │   │
   │  │  ตกเหว → −1 หัวใจ → Respawn ─────┼───┘   │
   │  │       │                         │       │
   │  │  หัวใจ=0 / หลอด≥100 → GAME OVER  │       │
   │  └────────────────────────────────┘       │
   └──────────────┬─────────────────────────────┘
                  ▼ เส้นชัย 1000m
        Boss: Carbon Baron (3 เวฟ)
                  │ ชนะ (แพ้ → Game Over)
                  ▼
              Post-test
                  │
                  ▼
   Report Card + Final Report (DAG 13 edge + rank S/A)
                  │
                  ▼ sync (HMAC + HTTPS)
          Teacher Dashboard (real-time)
                  │ End Session
                  ▼
              Export CSV
```

## เอกสารที่เกี่ยวข้อง

- [GAME_DESIGN.md](GAME_DESIGN.md) — **GDD V.2** เต็ม: 10 ทางแยกครบตัวเลข, boss 3 เวฟ, Stealth Assessment (แหล่งความจริงด้านดีไซน์)
- [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md) — แผนวิศวกรรม โครงสร้าง, module ownership, กติกา
- [SPRINT_2DAY.md](SPRINT_2DAY.md) — sprint 2 วัน (Dev A/B, P0/P1/P2) · [TIMELINE.md](TIMELINE.md) — ตาราง 3 วันเดิม
- [state-machines.md](state-machines.md) — Run/Meter/Heart/Boss state machine รวมจุดเดียว
- [BALANCE.md](BALANCE.md) — สรุปค่า balance (generate จาก [../balance/](../balance/))
- [adr/](adr/) — เหตุผลเบื้องหลังการตัดสินใจสถาปัตยกรรมแต่ละอัน (ล่าสุด 012)
