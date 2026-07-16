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

**Story D1-A3 · Y-Junction Interaction** `p0` `game` — ✅ **เสร็จ (PR #71)**
บล็อกกระโดดยืน (หยุดละลายชั่วคราว), input ←/→ เลือกนโยบาย, apply stat delta, กลับ endless-run
- Task: reuse fork/merge primitive · ~~choice UI~~ ✅ (junction banner, ขึ้นก่อน commit tile 4 tile ล่วงหน้า) · ~~emit `PolicyChoiceEvent`~~ ✅
- ✅ Acceptance: เลือกแล้ว stat เปลี่ยนตรง data, gameplay resume ไม่ค้าง — **verify แล้ว: 10/10 zone, เล่นซ้ำ 2 รอบให้ผลเหมือนกัน**

**Story D1-A4 · Hearts System (5 HP)** `p0` `core` `game` — ✅ **เสร็จ (PR #71)**
หัวใจ 5, ตกเหว −1 + respawn checkpoint, เก็บเพิ่มได้ (pickup logic เดียวกับ item)
- Task: HP บน `RunMetrics` (`core/state.py`) · hearts state machine · respawn wiring (RESPAWNING → RUNNING ตาม state machine, invincible frame ไม่ค้างข้ามรอบแล้ว)
- ✅ Acceptance: หัวใจหมด → trigger game over

**Story D1-A5 · Visual Scaffolding (Basic)** `p1` `game` — ✅ **เสร็จ (PR #71, `87af8d9`)**
Neon pivot tiles จุดหักศอก, chevron warning 3 บล็อกล่วงหน้า *(Holographic guide line = P2)*
- Task: renderer อ่าน `grid.turn_points` ที่มีอยู่แล้ว ไม่ต้องเพิ่ม data ใหม่ — neon tint ที่จุดเลี้ยว + chevron tint บน 3 tile ก่อนเลี้ยวถัดไป

### 🟩 Dev B — Content Data & Systems (`core/`, `game/`)

> **สถานะจริงในโค้ด ณ ตอนนี้ (หลัง #56/#58 pushed, รอ merge):** `balance/v1/*.json` มีคนอ่านอยู่แล้วตั้งแต่ PR2 (`tests/test_balance.py` คุม invariant, `scripts/gen_balance_md.py` generate เอกสาร) — ที่ยังไม่มีคือ**ฝั่ง application/gameplay** ที่ดึงไปใช้จริง `core/junction_data.py`, `core/scoring/stealth.py`, `core/scoring/dag.py`, `screens/report.py` เขียนแล้วใน #58 (รอ merge) `core/meters.py` (**meter state model** — ไม่ใช่ UI, ยังเป็นของ Dev A D1-A1) กับ bar UI ใน `ui/components.py` **ยังไม่มี**

**Story D1-B1 · Y-Junction Content Dataset** `p0` `data` — ✅ **เสร็จ (data จาก PR2, loader จาก #58)**
สร้าง `balance/v1/junctions.json` — 10 ทางแยกครบ: สถานการณ์, ตัวเลือกซ้าย/ขวา, stat delta, category, systemic-flag
- Task: ~~schema + data~~ ✅ · ~~`core/junction_data.py` loader~~ ✅ (#58) · ~~content validation test~~ ✅ (`tests/test_balance.py`)
- ✅ Acceptance: `get_junction(zone_id)` โหลดครบ 10 index — **ผ่านแล้ว** (`tests/test_junction_data.py`)

**Story D1-B2 · Evidence-to-Stats Item System** `p0` `game` — ✅ **เสร็จ (PR #71)**
Item pickup (Albedo/Methane/Eco-Seed), inventory UI 3 ช่อง, Eco-Seed (Spacebar) ลด Heat + ซ่อมบล็อก
- Task: ~~inventory model~~ ✅ (`core/items.py::Inventory`, 3-slot, `tests/test_items.py`) · ~~extend pickup รองรับ `scientific_item`~~ ✅ (spawn บน centreline, rate จาก `difficulty.json.items.spawn_chance`) · ~~Eco-Seed action~~ ✅ (Spacebar, `heat_reduction`/`repairs_blocks` จาก `difficulty.json`) · ~~inventory UI~~ ✅ (HUD text, ไม่ gate บอส — ตัดสินใจแล้วว่า inventory เป็น progress display ไม่ใช่ requirement สู้บอส, อัปเดต `GAME_DESIGN.md` แล้ว)
- ✅ Acceptance: เก็บ item ขึ้น inventory, ใช้ Eco-Seed แล้ว Heat ลดจริง

**Story D1-B3 · Decision Logging** `p0` `core` — ✅ **เสร็จ (#56)**
Log ทุก Y-Junction (decision 1–10) **และเวฟบอส (decision 11–13)**: zone/wave, choice, correct/systemic flag → เตรียม data ให้ D2-B2/D2-B3 (Stealth Score + DAG ต้องการครบทั้ง 13 decision ไม่ใช่แค่ 10)
- Task: ~~`GamePlayScreen` ถือ RunRecord (single-writer) · emit events~~ ✅ — **= PR3 ใน [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md#dependency-graph--pr-strategy-gdd-v2)** (`core/session.py::GameSession`)
- ✅ Acceptance: จบ 10 โซน ได้ log array ยาว 10 ครบ field — **ผ่านแล้วสำหรับ 10 โซน** (`tests/test_session.py`); ส่วน decision 11–13 (boss) รอ D2-A2/A3 (Dev A) เรียก `GameSession.boss_phase()` จริงจากฉากบอสที่ยังไม่มี

**Story D1-B4 · Dual-Meter UI Bars** `p0` `ui` — ✅ **เสร็จ (PR #71, `87af8d9`)**
วาด Heat + Capitalist bar, sync realtime, warning flash เมื่อ >80
- Task: `ui/components.py::MeterBar` — canvas-drawn (ไม่ใช้ asset), fill ตาม value/max_value, กะพริบเมื่อ ≥80% ของ `RunMetrics.max_meter`
- ✅ Acceptance: bar เคลื่อนไหวตรง state real-time

> **🔄 End of Day 1 — Sync Point (ทั้งคู่):** merge branch, playtest 0–1000m (ไม่รวมบอส) ให้ครบ loop: run → 10 junctions → reach 1000m, แก้ blocking bug ก่อนแยกงาน Day 2

---

## DAY 2 — Boss Phase, Scoring & Polish

### 🟦 Dev A — Boss Phase Mechanics (`game/`, `screens/`)

> **สถานะ (2026-07-16):** ทั้ง 3 story เขียนไว้ครบใน PR #71 แต่เรขาคณิตเดิมมีบั๊กบล็อกจริง — `_build_boss_wave` แยก/merge เลนด้วย `-= perp` ซึ่งต้องเดินถอย ขณะที่ผู้เล่นเดินได้แค่ `(+1,0)`/`(0,+1)` เท่านั้น BFS พิสูจน์: เข้าถึงได้แค่ 1/6 ไอเทม, merge point ทุกจุดเข้าไม่ถึง → เข้า boss phase แล้วชนะไม่ได้เลยตั้งแต่รอบแรก แก้แล้ว (commit `ddae561`) ด้วยเรขาคณิตที่ทุก tile เข้าถึงได้ด้วย move set จริงโดยโครงสร้าง — verify แล้ว 6/6 reachable, เล่นจบ 2 รอบติดไม่ค้าง

**Story D2-A1 · Boss Scene Transition** `p0` `game` — ✅ **เสร็จ (PR #71)**
980–990m warning banner "CARBON BARON DETECTED"; 1000m เปลี่ยนฉาก + spawn Carbon Baron (ใช้ `RunState.BOSS` gate)
- ✅ Acceptance: transition trigger แม่นยำที่ระยะ, ไม่ค้างระหว่าง state — เปลี่ยนจาก `== 1000` เป็น `>= BOSS_DISTANCE_M` แล้ว (fork-lane tile มี path index -1 ทำให้ข้าม threshold ได้ระหว่างไม่อยู่บน centerline)

**Story D2-A2 · Problem Wall + Y-Junction Split** `p0` `game` — ✅ **เสร็จ (PR #71)**
รียูส junction component ทำ 2-lane item select, แสดง Fake News บนกำแพงตาม wave data (D2-B1)
- Task: ~~emit `BossPhaseEvent`~~ ✅
- ✅ Acceptance: เลือก lane ถูก/ผิดตาม data, ผลกระทบ (บอส/หัวใจ) ถูกต้อง — `BossItemPlacement(wave, item_id, side)` แก้ wave-counter desync/stale-sibling/LEFT-RIGHT-flip ที่เคยเจอพร้อมกันด้วยต้นเหตุเดียว

**Story D2-A3 · 3-Wave Progression & Win/Loss** `p0` `game` — ✅ **เสร็จ (PR #71)**
เกราะ 3 ขีด, ตอบถูก 3 เวฟ = ชนะ; หัวใจหมด = Game Over; Victory → world restore → ส่งต่อ D2-B3
- Task: ~~emit `BossVictoryEvent`~~ ✅
- ✅ Acceptance: เล่นจบบอสได้ทั้ง win/lose path ครบ — `boss_armor` อ่านจาก `boss.json` จริงแล้ว (เดิม hardcode `-1` แม้ data มีค่าอยู่)
- 📝 **เปิดคำถามค้าง (ไม่ใช่บั๊ก):** แพ้บอสตอนนี้ยัง route ไปหน้า gameover ไม่ใช่ Report Card แม้ session จะ `finish()` แล้วก็ตาม — Dev A ทิ้ง comment ไว้ในโค้ดว่า "flag ไว้คุยกับ Dev B แล้ว ห้ามแก้ฝั่งเดียว" ตรงกับที่ Dev B เสนอเปิดเป็น issue แยกต่างหาก ยังไม่ตัดสินใจ

### 🟩 Dev B — Scoring, DAG & Report Card (`core/`, `screens/`, `server/`)

**Story D2-B1 · Boss Wave Content Data** `p0` `data` — ✅ **data เสร็จ (PR2, `balance/v1/boss.json`)**
`balance/v1/boss.json` — 3 เวฟ: ข้อความกำแพง, item ถูก/ผิด, stat effect
- ✅ Acceptance: Dev A ดึงใช้ใน D2-A2 ได้ตรง schema

**Story D2-B2 · Stealth Assessment Score Engine** `p0` `core` — ✅ **เสร็จ (#58)**
`core/scoring/stealth.py` — Educational Score เท่านั้น (ดู ADR-011, ไม่ใช่ raw Impact Score ที่อยู่ใน `rules.py` เดิม): `run_reduction_c`, `cognitive_score_c`, `net_impact_score_c`, `rank_for`
- ✅ Acceptance: unit test คำนวณจาก mock log ตรงสูตร + **projection deterministic** — **ผ่านแล้ว** (`tests/test_scoring_stealth.py`, 14 tests)
- หมายเหตุ: ค่าตัวเลข (systemic_point_c, boss_bonus_per_wave_c ฯลฯ) โหลดจาก `balance/v1/difficulty.json` จริง ไม่ hardcode

**Story D2-B3 · Auto-Generated DAG + Report Card Screen** `p0` `ui` — ✅ **เสร็จ (#58)**
`core/scoring/dag.py` (projection) + `screens/report.py` (renderer): วาด node/edge ทีละเส้น, เขียว=ถูก แดง=ผิด + tooltip, แสดง Grade + "อุณหภูมิที่กอบกู้ได้"
- ✅ Acceptance: จบเกมเห็น DAG ครบ 13 edge + คะแนนสรุป — **ผ่านแล้ว** (`tests/test_scoring_dag.py`, 10 tests) — รอ integration จริงกับ boss gameplay (D2-A2/A3) เพื่อดู decision 11–13 ไม่ใช่ "unplayed" ตลอด
- 📌 `balance/v1/dag.json` (13 edge, node/tooltip) เสร็จจาก PR2, `dag.py`+`report.py` เสร็จจาก #58

**Story D2-B4 · Backend Sync Integration** `p1` `server` — 🟡 **RunResult ฝั่ง schema/server เสร็จแล้ว (รอ merge PR #66), ฝั่ง Kivy client ยังไม่ต่อสาย**
ส่ง Net Impact Score + rank ผ่าน `core/sync.py` (HMAC) → `POST /api/v1/sessions/<code>/runs` เดิม
- Task: ~~feature flag + migration (nullable columns)~~ ✅ — `RunResult.net_impact_score/cognitive_score/rank`, `RunRecord.balance_version`, `evaluator.py` wiring, `server/` flag `STEALTH_ASSESSMENT_ENABLED` default off (branch `feat/stealth-assessment-schema-migration`, PR #66 open)
- ⬜ **ที่เหลือ: ไม่มีใครเรียก `core/sync.py` จากเกม Kivy จริง** (`SyncClient(` เจอแค่ใน `tests/test_sync.py`) — ไม่มี join-session screen, ไม่มี server URL config ที่ไหนในเกม, ไม่มี `Clock.schedule_interval` เรียก `flush()` — ดู design doc ที่กำลังจะเปิด issue ด้านล่าง
- 💡 ถ้าเวลาไม่พอ → local-only (P2 fallback) ยังใช้ได้ เพราะ local SQLite save ไม่ผูกกับ sync

**Story D2-B5 · History Screen Fix** `p2` `ui` — ✅ **เสร็จ (PR #73, merged)**
`screens/history.py:20` query ด้วยชื่อ hardcode `"Penguin"` แทนผู้เล่นจริง; `core/database.py::get_history` เรียงตามวันที่ไม่ใช่คะแนน; ไม่มี `tests/test_database.py` คุม `get_history`/`get_personal_best`
- Task: ~~`db.get_last_player_name()` แทน hardcode~~ ✅ · ~~`ORDER BY distance_m DESC, played_at DESC`~~ ✅ · ~~เพิ่มเทสต์~~ ✅ (`tests/test_database.py`, 6 tests)

**Story D2-B6 · Classroom Session Join + Offline Sync (design doc)** `p1` `docs` — ✅ **เสร็จ (PR #74, merged)**
เปิด GitHub issue ใหม่สเปก contract สำหรับ Dev A ต่อ join-screen เข้ากับ `core/sync.py` ที่มีอยู่แล้ว (เหมือน #46) — ไม่มี story ไหนคลุมเรื่องนี้มาก่อน เพราะ sprint เดิมสมมติว่า sync จะถูกต่อสายไปพร้อมกับ D2-B4 แต่ในทางปฏิบัติ D2-B4 ทำแค่ schema/server ฝั่งเดียว
- Task: `docs/design/classroom-session-client-sync.md` — แยก Part A (sync wiring, ผูกกับ #53) กับ Part B (join UX, Dev A — เปิดเป็น [#75](https://github.com/psu6810110162/Panguin-pikachu/issues/75))

> **🏁 End of Day 2 — Final Integration (ทั้งคู่, 2 ชม.สุดท้าย):** full playthrough (1000m → boss 3 wave → report card) · **Balance pass** (golden path เล่นดี = รอดจริง / evil path เล่นผิด = แพ้จริง ไม่ dead-end) · bug bash + demo build freeze
> **สถานะ (2026-07-16):** full playthrough **verify แล้วด้วยโปรแกรม** (headless walker เล่นจบ 2 รอบติด, 10/10 decision + 3 boss wave + Report Card) — เหลือ manual playtest จริงในแอป Kivy ก่อน freeze

---

## Milestones (GitHub)

- **Milestone 1: Core Loop (Day 1)** — Stories D1-A1 → D1-B4 — **ครบทุก story แล้ว** (รอ merge PR #71)
- **Milestone 2: Boss + Scoring (Day 2)** — Stories D2-A1 → D2-B6 — **ครบทุก story แล้ว** (รอ merge PR #71, #66)

## สถานะล่าสุด (2026-07-16, สรุปสั้นสำหรับ Dev B)

- **เพิ่งเสร็จ:** PR #71 ปิด release blocker สุดท้าย (บอสเดินไปไม่ถึง — เรขาคณิตต้องเดินถอย) + ทำ junction banner, wire D1-B2 (item/Eco-Seed), D1-B4 (meter bars), D1-A5 (neon/chevron) ครบ — เล่นจบ 2 รอบติดพิสูจน์แล้วด้วยโปรแกรม
- **PR ค้าง review:** #66, #67, #68, #69, #70, #71 (ตอนนี้เป็น PR หลักที่ปิด Core Loop + Boss Phase ทั้งหมด), #74
- **งานถัดไป:** รอ merge #71 เข้า main → manual playtest จริงในแอป → ตัดสินใจเรื่อง "แพ้บอสควร routing ไป Report Card ไหม" (ค้างเป็น cross-team decision) → D2-B4 ที่เหลือ (ต่อสาย `SyncClient` เข้าเกมจริง ตาม design doc #74)
- อ้างอิงแผนละเอียด: `~/.claude/plans/tender-doodling-sloth.md`
