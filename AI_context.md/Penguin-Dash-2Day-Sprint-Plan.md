# Penguin Dash — NSC 2026 Update — 2-Day Sprint Plan

Sprint Plan สำหรับทีม Dev 2 คน · แบ่งงานตาม module `core/` / `game/` / `screens/` / `server/` · จัดกลุ่มเป็น Milestone สำหรับ GitHub Projects

**Priority:** `P0` = ต้องเสร็จ (blocking demo) · `P1` = ควรมีถ้าเวลาเหลือ · `P2` = ตัดได้ถ้าเวลาไม่พอ

---

## DAY 1 — Core Loop & Content Data

### Dev A — Gameplay Mechanics (`core/`, `game/`)

#### D1-A1 · Dual-Meter State System `P0`
เพิ่ม `HeatMeter` และ `CapitalistAnger` ใน `core/state.py` (ฐาน 100, + = แย่ลง / - = ดีขึ้น) trigger Game Over เมื่อหลอดใดหลอดหนึ่งแตะ 0 หรือ 100

- **Acceptance:** unit test ปรับค่า stat แล้ว trigger game-over ถูกต้อง
- **Labels:** `dev-a` `p0` `day-1` `core`

#### D1-A2 · Zone-Based Spawning System `P0`
แบ่งระยะ 1,000m เป็น 10 โซน x 100m สุ่มจุดเกิด Y-Junction ภายในแต่ละโซน (1 ครั้ง/โซน) ผูก zone content category (1-3 สาเหตุ, 4-6 ผลกระทบ, 7-10 การแก้ปัญหา) ตาม data จาก Dev B (D1-B1)

- **Acceptance:** log แสดงตำแหน่งเกิด junction ครบ 10 จุด ไม่ซ้ำโซน
- **Labels:** `dev-a` `p0` `day-1` `game`

#### D1-A3 · Y-Junction Interaction `P0`
Block ให้กระโดดขึ้นยืน หยุดการละลายน้ำแข็งชั่วคราว · Input: ลูกศรซ้าย/ขวา เลือกนโยบาย → apply stat delta จาก data แล้วกลับเข้าสู่ endless-run mode ปกติ

- **Acceptance:** เลือกแล้ว stat เปลี่ยนตรงตาม data, gameplay resume ไม่ค้าง
- **Labels:** `dev-a` `p0` `day-1` `game`

#### D1-A4 · Hearts System (5 HP) `P0`
แสดงหัวใจ 5 ดวง ตกเหว = -1 หัวใจ + respawn จุดล่าสุด เก็บหัวใจเพิ่มได้ระหว่างทาง (ใช้ pickup logic เดียวกับ item)

- **Acceptance:** หัวใจหมด → trigger game over
- **Labels:** `dev-a` `p0` `day-1` `core/game`

#### D1-A5 · Visual Scaffolding (Basic) `P1`
Neon pivot tiles ที่จุดหักศอก, chevron warning สัญญาณล่วงหน้า 3 บล็อก · Holographic guide line ตัดเป็น `P2` ถ้าเวลาไม่พอ

- **Labels:** `dev-a` `p1` `day-1` `game`

### Dev B — Content Data & Systems (`core/`, `game/`)

#### D1-B1 · Y-Junction Content Dataset `P0`
สร้าง `core/junction_data.py` (หรือ JSON) บรรจุ 10 ทางแยกครบ: สถานการณ์, ตัวเลือกซ้าย/ขวา, stat delta (Heat/Capitalist), category tag · Schema พร้อมให้ Dev A ดึงใช้ใน D1-A2/A3

- **Acceptance:** โหลด data ผ่าน `get_junction(zone_id)` ได้ครบ 10 index
- **Labels:** `dev-b` `p0` `day-1` `data`

#### D1-B2 · Evidence-to-Stats Item System `P0`
Item pickup: Albedo Data, Methane Core, Eco-Seed · Inventory UI (แสดง 3 slot มุมจอ) · Eco-Seed ใช้ Spacebar ลด Heat Meter + ซ่อมบล็อก

- **Acceptance:** เก็บ item แล้วขึ้น inventory, ใช้ Eco-Seed แล้ว Heat Meter ลดจริง
- **Labels:** `dev-b` `p0` `day-1` `game`

#### D1-B3 · Decision Logging (Client-side Memory) `P0`
Log การตัดสินใจทุกจุด Y-Junction (decision 1-10): zone, choice, correct/systemic flag · เตรียม data structure ให้ D2-B2 (DAG) ใช้ต่อ

- **Acceptance:** จบ 10 โซน ได้ log array ยาว 10 รายการ ครบ field
- **Labels:** `dev-b` `p0` `day-1` `core`

#### D1-B4 · Dual-Meter UI Bars `P0`
วาด Heat Meter + Capitalist Anger bar, sync กับ state realtime · Warning flash เมื่อหลอดใกล้เต็ม (>80)

- **Acceptance:** bar เคลื่อนไหวตรงกับ state เปลี่ยนแบบ real-time
- **Labels:** `dev-b` `p0` `day-1` `ui`

### 🔄 End of Day 1 — Sync Point (ทั้งคู่)
Merge branch, playtest ระยะ 0-1000m (ไม่รวม boss) ให้ครบ loop: run 10 junctions → reach 1000m · แก้ blocking bug ก่อนแยกงาน Day 2

---

## DAY 2 — Boss Phase, Scoring & Polish

### Dev A — Boss Phase Mechanics (`game/`, `screens/`)

#### D2-A1 · Boss Scene Transition `P0`
980-990m: warning banner "CARBON BARON DETECTED" · 1000m: เปลี่ยนฉาก (sky, smog, music), spawn Carbon Baron entity

- **Acceptance:** transition trigger แม่นยำที่ระยะ, ไม่ค้างระหว่าง state
- **Labels:** `dev-a` `p0` `day-2` `game`

#### D2-A2 · Problem Wall + Y-Junction Split (Boss) `P0`
รียูส Y-Junction component จาก D1-A3 มาทำ 2-lane item select · แสดงข้อความ Fake News บนกำแพงตาม wave data (จาก D2-B1)

- **Acceptance:** เลือก lane ถูก/ผิดตาม data, ผลกระทบ (บอสเสียเลือด/hero เสียหัวใจ) ถูกต้อง
- **Labels:** `dev-a` `p0` `day-2` `game`

#### D2-A3 · 3-Wave Progression & Win/Loss `P0`
Boss armor 3 ขีด, ตอบถูกครบ 3 wave = ชนะ · Loss condition: หัวใจหมด → Game Over screen · Victory: world restore animation → ส่งต่อ D2-B3 (report card)

- **Acceptance:** เล่นจบ boss ได้ทั้ง win/lose path ครบ
- **Labels:** `dev-a` `p0` `day-2` `game`

### Dev B — Scoring, DAG & Report Card (`core/`, `screens/`, `server/`)

#### D2-B1 · Boss Wave Content Data `P0`
ข้อมูล 3 wave: ข้อความกำแพง, item ที่ถูก/ผิด, stat effect ต่อ wave

- **Acceptance:** Dev A ดึง data ใช้ใน D2-A2 ได้ตรง schema เดียวกับ D1-B1
- **Labels:** `dev-b` `p0` `day-2` `data`

#### D2-B2 · Stealth Assessment Score Engine `P0`
Impact Score: Σ(Temp_i, i=1..10) + Boss Bonus · Cognitive Score: boss ตอบถูก wave ละ +0.1°C (สูงสุด 0.5°C รวม perfect) · Net Impact Score + rank mapping (S/A/... ตามช่วง °C)

- **Acceptance:** unit test คำนวณคะแนนจาก mock log ตรงตามสูตร
- **Labels:** `dev-b` `p0` `day-2` `core`

#### D2-B3 · Auto-Generated DAG + Report Card Screen `P0`
วาด node/edge จาก decision log (D1-B3) ทีละเส้น, เขียว = ถูก แดง = ผิด (พร้อม tooltip เฉลย) · แสดง Grade + "อุณหภูมิที่กอบกู้ได้" ตอนจบเกม

- **Acceptance:** จบเกมแล้วเห็น DAG ครบ 13 edge พร้อมคะแนนสรุป
- **Labels:** `dev-b` `p0` `day-2` `ui`

#### D2-B4 · Backend Sync Integration `P1`
ส่งผล Net Impact Score + rank ผ่าน `core/sync.py` (HMAC) ไปยัง `/api/v1/sessions/<code>/runs` เดิม · ถ้าเวลาไม่พอ ตัดเป็น local-only ก่อน (`P2` fallback)

- **Labels:** `dev-b` `p1` `day-2` `server`

### 🏁 End of Day 2 — Final Integration (ทั้งคู่, 2 ชม.สุดท้าย)
Full playthrough test: run 1000m → boss 3 wave → report card · Balance pass: เช็คว่าค่า stat delta ทำให้เกม "รอดได้จริงถ้าเล่นดี" ไม่ dead-end ตาย · Bug bash + demo build freeze

---

## สรุปสำหรับตั้งเป็น GitHub Milestone

- **Milestone 1: Core Loop (Day 1)** — issues D1-A1 ถึง D1-B4
- **Milestone 2: Boss + Scoring (Day 2)** — issues D2-A1 ถึง D2-B4

**แนะนำ label เพิ่ม:** `dev-a` / `dev-b`, `p0` / `p1` / `p2`, `day-1` / `day-2` เพื่อ filter ใน GitHub Project board
