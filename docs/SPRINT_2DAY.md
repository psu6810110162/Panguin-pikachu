# Sprint Plan 2 วัน — Penguin Dash NSC 2026 Update

> แปลงจาก `penguin_dash_2day_plan.pdf` และจัดใหม่เป็น **Sprint → Story → Task** เพื่อ estimate + review ได้จริง
> ทีม Dev 2 คน · P0 = ต้องเสร็จ (blocking demo) / P1 = ควรมีถ้าเวลาเหลือ / P2 = ตัดได้
> ดีไซน์เกมดู [GAME_DESIGN.md](GAME_DESIGN.md) · ลำดับ dependency + PR slicing ดู [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md)

**ความสัมพันธ์กับ [TIMELINE.md](TIMELINE.md) (3 วันเดิม):** sprint 2 วันนี้คือการ re-scope งาน module D1–D9 ให้กระชับสำหรับรอบ update — ไม่ได้ทิ้ง TIMELINE เดิม แต่เป็น view ที่เน้น "งานที่เหลือเพื่อขึ้น GDD V.2"

**Label สำหรับ GitHub Projects:** `dev-a` / `dev-b` · `p0` / `p1` / `p2` · `day-1` / `day-2` · `core` / `game` / `ui` / `data` / `server`

---

## DAY 1 — Core Loop & Content Data

### 🟦 Dev A — Gameplay Mechanics (`core/`, `game/`)

**Story D1-A1 · Dual-Meter State System** `p0` `core`
เพิ่ม HeatMeter + CapitalistAnger (ฐาน 100, `+`=แย่ลง / `−`=ดีขึ้น), trigger Game Over เมื่อหลอดใดแตะ 100
- Task: meter model (`core/meters.py`, pure) · unit test ปรับ stat → game-over · wire เข้า RunRecord event
- ✅ Acceptance: unit test ปรับค่า stat แล้ว trigger game-over ถูกต้อง

**Story D1-A2 · Zone-Based Spawning** `p0` `game`
แบ่ง 1,000m เป็น 10 โซน×100m, สุ่ม Y-Junction 1 ครั้ง/โซน, ผูก category ตามโซน (ดึง data จาก D1-B1)
- Task: zone metadata บน GridManager · seeded RNG · junction placement
- ✅ Acceptance: log แสดงตำแหน่งเกิด junction ครบ 10 จุด ไม่ซ้ำโซน

**Story D1-A3 · Y-Junction Interaction** `p0` `game`
บล็อกกระโดดยืน (หยุดละลายชั่วคราว), input ←/→ เลือกนโยบาย, apply stat delta, กลับ endless-run
- Task: reuse fork/merge primitive · choice UI · emit `PolicyChoiceEvent`
- ✅ Acceptance: เลือกแล้ว stat เปลี่ยนตรง data, gameplay resume ไม่ค้าง

**Story D1-A4 · Hearts System (5 HP)** `p0` `core` `game`
หัวใจ 5, ตกเหว −1 + respawn checkpoint, เก็บเพิ่มได้ (pickup logic เดียวกับ item)
- Task: HP บน `penguin.py` · hearts state machine · respawn wiring
- ✅ Acceptance: หัวใจหมด → trigger game over

**Story D1-A5 · Visual Scaffolding (Basic)** `p1` `game`
Neon pivot tiles จุดหักศอก, chevron warning 3 บล็อกล่วงหน้า *(Holographic guide line = P2)*

### 🟩 Dev B — Content Data & Systems (`core/`, `game/`)

**Story D1-B1 · Y-Junction Content Dataset** `p0` `data`
สร้าง `balance/v1/junctions.json` — 10 ทางแยกครบ: สถานการณ์, ตัวเลือกซ้าย/ขวา, stat delta, category, systemic-flag
- Task: schema + data · `core/junction_data.py` loader · content validation test
- ✅ Acceptance: `get_junction(zone_id)` โหลดครบ 10 index

**Story D1-B2 · Evidence-to-Stats Item System** `p0` `game`
Item pickup (Albedo/Methane/Eco-Seed), inventory UI 3 ช่อง, Eco-Seed (Spacebar) ลด Heat + ซ่อมบล็อก
- Task: extend pickup รองรับ `scientific_item` · inventory model · Eco-Seed action
- ✅ Acceptance: เก็บ item ขึ้น inventory, ใช้ Eco-Seed แล้ว Heat ลดจริง

**Story D1-B3 · Decision Logging** `p0` `core`
Log ทุก Y-Junction (decision 1–10): zone, choice, correct/systemic flag → เตรียม data ให้ D2-B2 (DAG)
- Task: `GamePlayScreen` ถือ RunRecord (single-writer) · emit events
- ✅ Acceptance: จบ 10 โซน ได้ log array ยาว 10 ครบ field

**Story D1-B4 · Dual-Meter UI Bars** `p0` `ui`
วาด Heat + Capitalist bar, sync realtime, warning flash เมื่อ >80
- Task: meter bar component ใหม่ใน `ui/components.py`
- ✅ Acceptance: bar เคลื่อนไหวตรง state real-time

> **🔄 End of Day 1 — Sync Point (ทั้งคู่):** merge branch, playtest 0–1000m (ไม่รวมบอส) ให้ครบ loop: run → 10 junctions → reach 1000m, แก้ blocking bug ก่อนแยกงาน Day 2

---

## DAY 2 — Boss Phase, Scoring & Polish

### 🟦 Dev A — Boss Phase Mechanics (`game/`, `screens/`)

**Story D2-A1 · Boss Scene Transition** `p0` `game`
980–990m warning banner "CARBON BARON DETECTED"; 1000m เปลี่ยนฉาก + spawn Carbon Baron (ใช้ `RunState.BOSS` gate)
- ✅ Acceptance: transition trigger แม่นยำที่ระยะ, ไม่ค้างระหว่าง state

**Story D2-A2 · Problem Wall + Y-Junction Split** `p0` `game`
รียูส junction component ทำ 2-lane item select, แสดง Fake News บนกำแพงตาม wave data (D2-B1)
- Task: emit `BossPhaseEvent`
- ✅ Acceptance: เลือก lane ถูก/ผิดตาม data, ผลกระทบ (บอส/หัวใจ) ถูกต้อง

**Story D2-A3 · 3-Wave Progression & Win/Loss** `p0` `game`
เกราะ 3 ขีด, ตอบถูก 3 เวฟ = ชนะ; หัวใจหมด = Game Over; Victory → world restore → ส่งต่อ D2-B3
- Task: emit `BossVictoryEvent`
- ✅ Acceptance: เล่นจบบอสได้ทั้ง win/lose path ครบ

### 🟩 Dev B — Scoring, DAG & Report Card (`core/`, `screens/`, `server/`)

**Story D2-B1 · Boss Wave Content Data** `p0` `data`
`balance/v1/boss.json` — 3 เวฟ: ข้อความกำแพง, item ถูก/ผิด, stat effect
- ✅ Acceptance: Dev A ดึงใช้ใน D2-A2 ได้ตรง schema

**Story D2-B2 · Stealth Assessment Score Engine** `p0` `core`
`core/scoring/stealth.py` — Impact Score (Σ ΔTemp + Boss Bonus), Cognitive Score (บอสถูก wave ละ +0.1°C, ≤0.5°C), Net Impact + rank (S/A)
- ✅ Acceptance: unit test คำนวณจาก mock log ตรงสูตร + **projection deterministic**

**Story D2-B3 · Auto-Generated DAG + Report Card Screen** `p0` `ui`
`core/scoring/dag.py` (projection) + `screens/report.py` (renderer): วาด node/edge ทีละเส้น, เขียว=ถูก แดง=ผิด + tooltip, แสดง Grade + "อุณหภูมิที่กอบกู้ได้"
- ✅ Acceptance: จบเกมเห็น DAG ครบ 13 edge + คะแนนสรุป

**Story D2-B4 · Backend Sync Integration** `p1` `server`
ส่ง Net Impact Score + rank ผ่าน `core/sync.py` (HMAC) → `POST /api/v1/sessions/<code>/runs` เดิม
- Task: feature flag + migration (nullable columns)
- 💡 ถ้าเวลาไม่พอ → local-only (P2 fallback)

> **🏁 End of Day 2 — Final Integration (ทั้งคู่, 2 ชม.สุดท้าย):** full playthrough (1000m → boss 3 wave → report card) · **Balance pass** (golden path เล่นดี = รอดจริง / evil path เล่นผิด = แพ้จริง ไม่ dead-end) · bug bash + demo build freeze

---

## Milestones (GitHub)

- **Milestone 1: Core Loop (Day 1)** — Stories D1-A1 → D1-B4
- **Milestone 2: Boss + Scoring (Day 2)** — Stories D2-A1 → D2-B4
