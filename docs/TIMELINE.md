# Timeline — 3 วัน

Checklist ติ๊กได้ระหว่างทำ ดูเหตุผล/รายละเอียดของแต่ละ module ใน [ENGINEERING_PLAN.md](ENGINEERING_PLAN.md)

จุดพึ่งพาเดียวระหว่างสองคนคือ **RunRecord schema (D7a) — freeze ภายในเช้าวันที่ 1** หลังจากนั้นสองสายไม่รอกัน ทุก module = 1 branch = 1 PR, review กันท้ายวัน

## วันที่ 1 — Foundation + Core Loop

**Must:** Schema+Events+State Machine / CI+pytest+ruff / Meters+Checkpoint+Respawn

### 🟩 คุณ
- [ ] เช้า — F0: merge #22 → main, ลบ branch ค้าง, branch protection, PR contract (pyproject+gitignore+configs) *(เสร็จแล้วใน PR #23)*
- [ ] เช้า — D7a: `core/schema.py` + `core/events.py` + `core/state.py` — schema v1.0 + events + state machine + **freeze**
- [ ] เช้า — เขียน `docs/OVERVIEW.md`, `docs/ENGINEERING_PLAN.md`, `docs/TIMELINE.md`, `docs/adr/*.md`
- [ ] บ่าย — F1: requirements, pre-commit, ruff ทั้ง repo *(เสร็จแล้วใน PR #23)* — type hints เอาแค่ `core/` ก่อน
- [ ] ค่ำ — F2: ci.yml (lint+test, env `KIVY_NO_ARGS=1 KIVY_WINDOW=mock SDL_VIDEODRIVER=dummy` + SDL2 deps) *(เสร็จแล้วใน PR #23)*

### 🟦 เพื่อน
- [ ] เช้า — D1: `game/meters.py` (Heat + dual meters) + HUD ใน style.kv
- [ ] บ่าย — D2 (ครึ่งแรก): checkpoint 100m + HP + Respawn (3s, −10%, นับ respawn_count)
- [ ] ค่ำ — Review PR ของกันและกัน / เล่นทดสอบ respawn จริง

**✅ Demo จบวัน:** เกมเล่น → ชน → ตาย → เกิดใหม่ → ทุกอย่างถูกเก็บเป็น event

---

## วันที่ 2 — เนื้อเกมครบ + Scoring

**Must:** Mission / Boss / Quiz / Evaluation / Sync client

### 🟩 คุณ
- [ ] เช้า — F3: conftest + unit tests (grid, pool, config, smoke) *(เสร็จแล้วใน PR #23)*
- [ ] บ่าย — D7b: `core/scoring/` (evaluator, rules, hake) + tests + กติกา core ห้าม import kivy
- [ ] ค่ำ — D8: `core/sync.py` — HMAC(timestamp+nonce+payload) + offline queue + retry/backoff/idempotency + tests

### 🟦 เพื่อน
- [ ] เช้า — D2 (จบ): policy popup (JSON) + consequence → event ลง RunRecord
- [ ] บ่าย — D3: 3 modules + missions + tracker HUD + เส้นชัย 1,000 ม.
- [ ] ค่ำ — D5: quiz JSON bank + pre/post-test screens → event ลง RunRecord

**✅ Demo จบวัน:** เล่นจนจบ → ได้ score → ได้ Hake Gain

---

## วันที่ 3 — Backend + Integration

**Must:** API / Dashboard basic / Export CSV / Final Report

### 🟩 คุณ
- [ ] เช้า — D9 (ครึ่งแรก): Flask `api/` + `models/` (SQLite) — รับ RunRecord, verify HMAC+nonce, server-authoritative score ผ่าน `core/scoring`
- [ ] บ่าย — D9 (จบ): SocketIO (ทุก 2-5 วิ) + Dashboard ขั้นต่ำ: ตารางผู้เล่น + End Session + Export CSV (localhost + ngrok/LAN — ไม่ deploy Railway ก่อน demo)
- [ ] ค่ำ — Integration ร่วมกัน: หลายเครื่อง → Join Room → เล่น → dashboard → End Session → Export / F4: README verification สุดท้าย

### 🟦 เพื่อน
- [ ] เช้า — D4: Boss 2 เฟส (Dodge/Heal → Debunk ผูก quiz) → Mission Complete
- [ ] บ่าย — D6: Final Report screen (ระยะ, Heat %, Scores, Hake Gain, Conceptual Shift, Run Again)
- [ ] ค่ำ — Integration + ต่อ Final Report เข้าผล scoring + UI polish เท่าที่ทัน

**✅ Demo จบวัน:** Player → Server → Teacher → Report ครบ slice

---

## เส้นตัด (ตัดจากบนลงล่างเมื่อเวลาบีบ)

1. ✂️ ตัดทันทีโดยไม่ต้องคิด: Railway deploy ก่อน demo, replay timeline บน dashboard, asset_manifest.json, Shop/History (มีแล้วจาก #22 — ห้ามแตะ), telemetry 1 วิ (ใช้ 2-5 วิ)
2. ✂️ ตัดได้ถ้าจำเป็น: asset ใหม่จาก itch.io, Conceptual Shift animation (ภาพนิ่ง), PostgreSQL, leaderboard ข้ามห้อง
3. ⚠️ ตัดไม่ได้: Respawn+Checkpoint, Mission+เส้นชัย+Boss, quiz pre/post + Hake Gain, sync → dashboard → End Session → Export CSV
