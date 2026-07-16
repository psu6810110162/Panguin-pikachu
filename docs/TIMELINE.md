# Timeline

> **Historical reference:** สถานะและ timeline ปัจจุบันย้ายไป [GAME_FIRST_PLAN.md](GAME_FIRST_PLAN.md#status) เพื่อไม่ให้ checklist หลายไฟล์ขัดกัน

สถานะปัจจุบัน (PR-based, GDD V.2) อยู่ด้านบน — แผน 3 วันดั้งเดิม (D1–D9, foundation) เก็บไว้ด้านล่างเป็น historical reference

---

## Timeline ปัจจุบัน — PR Roadmap (GDD V.2)

Checklist นี้ติ๊กตามจริงระหว่างทำ — ลำดับ PR ตาม dependency graph ใน [ENGINEERING_PLAN.md § Dependency Graph & PR Strategy](ENGINEERING_PLAN.md#dependency-graph--pr-strategy-gdd-v2) ไม่ใช่ตามวันปฏิทิน (render รอ state, scoring รอ event schema นิ่ง) รายละเอียด Story/Task ต่อ PR ดู [SPRINT_2DAY.md](SPRINT_2DAY.md)

| PR | Scope | Layer | สถานะ |
|---|---|---|---|
| PR1 | Docs + ADR-009..012 + PDF→md + `state-machines.md` | Docs | ✅ เสร็จ |
| PR2 | `balance/v1/*.json` + `test_balance.py` + BALANCE.md generator | L0 Content | ✅ เสร็จ |
| PR3 | `GameSession`/RunRecord ownership + event emission (single-writer) | L1 Infra | ⬜ ถัดไป |
| PR4 | `core/meters.py` + hearts state machine + inventory + `capitalist` rule | L2 State | ⬜ |
| PR5 | Zone spawning + Y-Junction interaction + item/Eco-Seed + boss 3-wave | L3 Logic | ⬜ |
| PR6 | Meter/heart/inventory HUD + junction/boss lane UI | L4 Render | ⬜ |
| PR7 | `scoring/stealth.py` + `scoring/dag.py` (projection) | L5 Scoring | ⬜ |
| PR8 | Report Card screen (render DAG) + Sync wire + migration | L6 Report+Sync | ⬜ |

**จุดพึ่งพา:** PR3 ต้องเสร็จก่อน PR4/PR7 เริ่ม (event schema นิ่ง); PR4 ต้องเสร็จก่อน PR5/PR6; PR8 รอทั้ง PR5+PR7 — ดู dependency graph เต็มใน ENGINEERING_PLAN.md

**Suggested session mapping** (ถ้าทำแบบ sprint 2 วันตาม [SPRINT_2DAY.md](SPRINT_2DAY.md)):

- **Day 1:** PR3 (เช้า, blocking ทุกอย่าง) → PR4 (บ่าย) → PR5 เริ่ม (ค่ำ, ขนานกับ PR7 ถ้ามีคนที่สอง) — ตรง Stories D1-A1..D1-B4
- **Day 2:** PR5 จบ + PR6 → PR7 (ถ้ายังไม่เสร็จ Day 1) → PR8 — ตรง Stories D2-A1..D2-B4, จบด้วย full playthrough + balance pass

---

## Timeline ดั้งเดิม — 3 วัน (Foundation, ก่อน GDD V.2 — historical reference)

Checklist ติ๊กได้ระหว่างทำ ดูเหตุผล/รายละเอียดของแต่ละ module ใน [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md)

จุดพึ่งพาเดียวระหว่างสองคนคือ **RunRecord schema (D7a) — freeze ภายในเช้าวันที่ 1** หลังจากนั้นสองสายไม่รอกัน ทุก module = 1 branch = 1 PR, review กันท้ายวัน

## วันที่ 1 — Foundation + Core Loop

**Must:** Schema+Events+State Machine / CI+pytest+ruff / Meters+Checkpoint+Respawn

### 🟩 คุณ
- [x] เช้า — F0: merge #22 → main, ลบ branch ค้าง, branch protection, PR contract (pyproject+gitignore+configs) *(เสร็จแล้วใน PR #23)*
- [x] เช้า — D7a: `core/schema.py` + `core/events.py` + `core/state.py` — schema v1.0 + events + state machine + **freeze** *(PR #24 — ตามด้วย boundary/malformed tests จากรอบ review)*
- [x] เช้า — เขียน `docs/OVERVIEW.md`, `docs/ENGINEERING_PLAN.md`, `docs/TIMELINE.md`, `docs/adr/*.md` *(PR #23)*
- [x] บ่าย — F1: requirements, pre-commit, ruff ทั้ง repo *(เสร็จแล้วใน PR #23)* — type hints เอาแค่ `core/` ก่อน
- [x] ค่ำ — F2: ci.yml (lint+test, env `KIVY_NO_ARGS=1 KIVY_WINDOW=mock SDL_VIDEODRIVER=dummy` + SDL2 deps) *(เสร็จแล้วใน PR #23)*

### 🟦 เพื่อน
- [ ] เช้า — D1: `game/meters.py` (Heat + dual meters) + HUD ใน style.kv
- [ ] บ่าย — D2 (ครึ่งแรก): checkpoint 100m + HP + Respawn (3s, −10%, นับ respawn_count)
- [ ] ค่ำ — Review PR ของกันและกัน / เล่นทดสอบ respawn จริง

**✅ Demo จบวัน:** เกมเล่น → ชน → ตาย → เกิดใหม่ → ทุกอย่างถูกเก็บเป็น event

---

## วันที่ 2 — เนื้อเกมครบ + Scoring

**Must:** Mission / Boss / Quiz / Evaluation / Sync client

### 🟩 คุณ
- [x] เช้า — F3: conftest + unit tests (grid, pool, config, smoke) *(เสร็จแล้วใน PR #23)*
- [x] บ่าย — D7b: `core/scoring/` (evaluator, rules, hake) + tests + กติกา core ห้าม import kivy *(PR #25 — quiz averaging bug ถูกแก้ตามหลังใน PR #31)*
- [x] ค่ำ — D8: `core/sync.py` — HMAC + offline queue + retry/backoff/idempotency + tests *(PR #26 — scheme อัปเกรดเป็น canonical JSON envelope รวม run_id จากรอบ review)*

### 🟦 เพื่อน
- [ ] เช้า — D2 (จบ): policy popup (JSON) + consequence → event ลง RunRecord
- [ ] บ่าย — D3: 3 modules + missions + tracker HUD + เส้นชัย 1,000 ม.
- [ ] ค่ำ — D5: quiz JSON bank + pre/post-test screens → event ลง RunRecord

**✅ Demo จบวัน:** เล่นจนจบ → ได้ score → ได้ Hake Gain

---

## วันที่ 3 — Backend + Integration

**Must:** API / Dashboard basic / Export CSV / Final Report

### 🟩 คุณ
- [x] เช้า — D9 (ครึ่งแรก): Flask `api/` + `models/` (SQLite) — รับ RunRecord, verify HMAC+nonce, server-authoritative score ผ่าน `core/scoring` *(PR #27)*
- [x] บ่าย — D9 (จบ): SocketIO + Dashboard: ตารางผู้เล่น + End Session + Export CSV *(PR #27 ขั้นต่ำ → PR #28 redesign เต็ม: projector-legible, real-time diff ต่อแถว, XSS-safe)*
- [x] ค่ำ — Integration: end-to-end จริงบนเครื่องเดียวผ่านแล้ว (create session → sync ผ่าน HttpTransport → dashboard real-time → End → Export) / F4: README verification *(PR #34)* — **ค้าง: ทดสอบหลายเครื่องผ่าน LAN จริงก่อน demo**

### 🟦 เพื่อน
- [ ] เช้า — D4: Boss 2 เฟส (Dodge/Heal → Debunk ผูก quiz) → Mission Complete
- [ ] บ่าย — D6: Final Report screen (ระยะ, Heat %, Scores, Hake Gain, Conceptual Shift, Run Again)
- [ ] ค่ำ — Integration + ต่อ Final Report เข้าผล scoring + UI polish เท่าที่ทัน

**✅ Demo จบวัน:** Player → Server → Teacher → Report ครบ slice

---

## งานเพิ่มเติมนอกแผน 3 วัน — Hardening, Review, DevX (10–11 ก.ค. 2026)

งานฝั่ง 🟩 ที่เกิดขึ้นหลังแผนหลักเสร็จ — ทั้งหมด merge เข้า `main` แล้ว:

- [x] **DevX + Docker** *(PR #29)* — Dockerfile (backend เท่านั้น, non-root) + docker-compose (SQLite default / profile postgres), Makefile + run scripts, ADR-008, README How to Play/How to Use
- [x] **Review follow-ups รอบแรก** *(PR #31)* — แก้ quiz score averaging, HttpTransport retry 4xx, room code collision, `/api/v1` versioning, rate limiting (Flask-Limiter), Alembic migrations (Flask-Migrate)
- [x] **Dashboard a11y + design tokens** *(PR #32)* — `:focus-visible` states, spacing/type-scale tokens, projector legibility
- [x] **รีวิวไขว้ทั้ง 8 PR + แก้ตามรีวิวทั้ง stack** — ประเด็นหลักที่ปิดไป:
  - Security: HMAC เปลี่ยนเป็น canonical JSON envelope รวม `run_id` (ปิด delimiter confusion + relabel attack), teacher token auth ต่อ session (end/export/dashboard), `FLASK_DEBUG` guard ปฏิเสธ default secret นอกโหมด debug
  - Correctness: 429 ต้อง retry ไม่ใช่ทิ้ง (กัน data loss เงียบ), `create_all` ข้าม DB ที่ managed ด้วย migrations, ingest race → converge แบบ idempotent, player lookup scope ตาม session, เช็ค session ended ก่อน join/ingest
  - Tests: boundary/malformed/auth/multi-phase quiz/HttpTransport — suite โตจาก ~77 เป็น 112 tests
- [x] **กู้ stack ที่ merge พลาด** *(PR #33)* — ทีม merge 8 PR รวดเดียวโดยไม่รอ retarget ทำให้มีแค่ #24 ถึง main; กู้ด้วย PR เดียวจาก branch ที่มีโค้ดครบ + ลบ branch ค้างทั้งหมดหลังตรวจ ancestry
- [x] **README refresh ให้ตรงโค้ด** *(PR #34)* — ตาราง env vars / API endpoints (จาก route จริง) / Security Model, แก้คำสั่งที่ตกยุค — ทุกคำสั่งใน README รันทดสอบจริงก่อนเขียน

---

## เส้นตัด (ตัดจากบนลงล่างเมื่อเวลาบีบ)

1. ✂️ ตัดทันทีโดยไม่ต้องคิด: Railway deploy ก่อน demo, replay timeline บน dashboard, asset_manifest.json, Shop/History (มีแล้วจาก #22 — ห้ามแตะ), telemetry 1 วิ (ใช้ 2-5 วิ)
2. ✂️ ตัดได้ถ้าจำเป็น: asset ใหม่จาก itch.io, Conceptual Shift animation (ภาพนิ่ง), PostgreSQL, leaderboard ข้ามห้อง
3. ⚠️ ตัดไม่ได้: Respawn+Checkpoint, Mission+เส้นชัย+Boss, quiz pre/post + Hake Gain, sync → dashboard → End Session → Export CSV
