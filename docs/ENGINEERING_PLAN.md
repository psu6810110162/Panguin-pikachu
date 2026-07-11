# Engineering Plan — Penguin Dash (NSC2026)

ทีม 2 คน: **เพื่อน (Antigravity CLI)** และ **คุณ (Claude Code)**. ฐานโค้ด: `main` หลัง merge [#22](https://github.com/psu6810110162/Panguin-pikachu/pull/22) (rewrite ทั้งหมดของเพื่อน) บวก [#23](https://github.com/psu6810110162/Panguin-pikachu/pull/23) (foundation: tooling/CI/tests/docs)

ดู [OVERVIEW.md](OVERVIEW.md) สำหรับภาพรวมเกมและสารบัญหน้าจอ, [TIMELINE.md](TIMELINE.md) สำหรับตารางงานละเอียด

## Gap Analysis — มีแล้ว vs ต้องสร้างเพิ่ม

| ใน PDF (NSC2026 Penguin dash.pdf) | สถานะ |
|---|---|
| วิ่งเก็บของ + หลบสิ่งกีดขวาง + score/animation | ✅ มีแล้ว |
| SQLite เก็บ high score/gems, shop, audio | ✅ มีแล้ว |
| Meters real-time, checkpoint+policy, 3 modules, boss 2 เฟส | ❌ ต้องสร้าง (D1–D4) |
| Pre/Post-test + Hake Gain | ❌ ต้องสร้างใหม่ (D5) |
| DAG evaluation + rubric scoring | ↳ ปรับเป็น Rule-based scoring (D7b, ดู ADR-003) |
| Final Report screen | ❌ ต้องสร้าง (D6) |
| HMAC + REST sync | ❌ ต้องสร้าง (D8) |
| Backend + WebSockets + Teacher Dashboard | ❌ ต้องสร้างทั้งหมด (D9) |
| CI, tests, lint, type check, pre-commit | ✅ เสร็จใน #23 |

## Module Ownership

**หลักการแบ่ง:** เพื่อนรู้โค้ดเกม (เจ้าของ PR #22) → รับฝั่งเกมทั้งหมด (D1–D6) / คุณรับฝั่ง Systems + Backend (D7–D9) ซึ่งแยกจากโค้ดเกมเกือบสนิท → ไม่ block กัน

**Contract กันชนจุดเดียว:** `core/schema.py` (RunRecord) — freeze ก่อนงานอื่นเริ่ม ดู [ADR-001](adr/001-runrecord-contract.md)

### 🟦 เพื่อน — Gameplay & Learning Content

| Module | งานหลัก | เหตุผล |
|---|---|---|
| **D1 Meters & HUD** | `game/meters.py` Heat + dual meters (state/decay/clamp) + HUD ใน style.kv | feedback loop real-time ตาม PDF |
| **D2 Checkpoint, Policy & Respawn** | checkpoint ทุก 100m, policy popup (JSON data-driven), ระบบ HP+Respawn (3s, −10%, นับ respawn_count) | จุดตัดสินใจ + จุดเกิดใหม่ ดู ADR-002 |
| **D3 Learning Modules & Missions** | แบ่ง 3 modules ตามระยะ, mission ย่อยต่อ module, เส้นชัย 1000m → Boss | เปลี่ยน endless เป็น Mission Runner |
| **D4 Boss 2 เฟส** | `game/boss.py` Dodge/Heal + Debunk misconceptions ผูก quiz | จุดวัดความเข้าใจที่เล่นสนุก |
| **D5 Quiz Pre/Post-test** | `game/quiz_bank.py` + JSON คำถาม, screen pre/post-test | หลักฐาน Hake Gain |
| **D6 Final Report Screen** | สรุปผล, Hake Gain, Conceptual Shift, Run Again | "Impact Evidence" ตาม PDF |

### 🟩 คุณ — Systems, Scoring & Backend

| Module | งานหลัก | เหตุผล |
|---|---|---|
| **D7a Schema & Events** | `core/schema.py`+`core/events.py`+`core/state.py` — RunRecord (event=source of truth, result=projection), state machine พร้อม transition validation | contract กลาง ดู ADR-001 |
| **D7b Scoring (Rule-based)** | `core/scoring/` (evaluator/rules/hake) — **ไม่ใช่** `game/` เพราะ server ต้อง import ได้โดยไม่ลาก Kivy | ดู ADR-003 |
| **D8 Sync Client** | `core/sync.py` HMAC-SHA256(timestamp+nonce+payload) บน HTTPS, offline queue, retry/backoff/idempotency | ดู ADR-004 |
| **D9 Backend + Teacher Dashboard** | `server/{api,services,models,dashboard}/` Flask+SocketIO, session model, dashboard MVP (ตาราง+End Session+Export CSV), server-authoritative scoring | ดู ADR-005, ADR-006 |

## โครงสร้าง Directory เป้าหมาย

```
Panguin-pikachu/
├── main.py, style.kv
├── core/                  # ห้าม import kivy (ยกเว้น audio.py) — server ใช้ร่วมได้
│   ├── schema.py  events.py  state.py  sync.py
│   ├── scoring/ (evaluator.py, rules.py, hake.py)
│   └── config.py  database.py  logger.py  audio.py
├── game/                  # gameplay logic (import kivy ได้)
├── screens/  ui/  assets/
├── server/                # Flask — import ได้เฉพาะ core/
│   ├── __init__.py  __main__.py  config.py  extensions.py
│   ├── api.py  services.py  models.py  dashboard.py
│   ├── static/ (dashboard.css, dashboard.js)  templates/
│   ├── Dockerfile
│   └── requirements.txt  # แยกจาก requirements.txt ของเกม — ไม่พ่วง Flask เข้า client build
├── scripts/ (run_game.sh, run_server.sh)
├── tests/
├── docs/ (OVERVIEW.md, ENGINEERING_PLAN.md, TIMELINE.md, adr/ + TEMPLATE.md)
├── docker-compose.yml, .env.example, Makefile
└── pyproject.toml, .pre-commit-config.yaml, .github/
```

## Rules (บังคับด้วยเครื่องมือ ไม่ใช่ความจำ)

1. Branch naming: `feat/ fix/ chore/ test/ docs/ ci/` — ห้าม push ตรง `main`
2. [Conventional Commits](https://www.conventionalcommits.org/)
3. **Types:** `core/` + `game/` + `server/` ต้องมี type hints ครบ (mypy `disallow_untyped_defs` ใน CI) / `screens/`+`ui/` ผ่อนปรน (Kivy ไม่มี type stubs)
4. Quality gate: pre-commit (ruff ทุก commit, pytest+mypy ทุก push) — `pre-commit install -t pre-commit -t pre-push`
5. ทุก PR: CI เขียว + review 1 คน (CODEOWNERS auto-request) + checklist ใน PR template
6. **Assets/UI:** ใช้จาก itch.io ได้ ต้อง license CC0/CC-BY บันทึกใน `assets/CREDITS.md` + `assets/asset_manifest.json`, ไฟล์ >1.5MB ถูก hook กัน
7. ข้อมูล quiz/policy เป็น JSON data files — แก้เนื้อหาไม่ต้องแตะโค้ด
8. `core/` ห้าม import kivy เด็ดขาด — บังคับด้วย test/import-linter

## Changing หรือเพิ่ม ADR (สมมติอีกคนอยากแก้/เพิ่มการตัดสินใจ)

ใช้ [`docs/adr/TEMPLATE.md`](adr/TEMPLATE.md) เป็นจุดเริ่ม — numbering: `NNN-kebab-title.md` เลขถัดจาก ADR ล่าสุด (ปัจจุบันไปถึง [008](adr/008-docker-compose-backend.md))

- **ADR เป็น immutable record** — ห้ามแก้ Decision ของ ADR เก่าย้อนหลัง ถ้าการตัดสินใจเปลี่ยน ให้เขียน ADR **ใหม่** ที่ supersede อันเดิม แล้ว cross-link ทั้งสองทาง (`**Status:** Superseded by ADR-00X` ใน ADR เก่า, อ้างอิงกลับใน ADR ใหม่)
- **เขียน ADR เมื่อ:** เพิ่ม/ลบ dependency, เปลี่ยน data model/contract (RunRecord/events/state machine), เปลี่ยน security model, หรือ reverse การตัดสินใจเดิม — ตรงกับ pattern ของ ADR-001 ถึง 008 ที่มีอยู่แล้ว
- **PR process เดียวกับโค้ด:** ผ่าน Rules ข้อ 5 ด้านบน (CI เขียว + review 1 คน) — PR ที่แก้แค่ docs ก็ยังต้องให้อีกคน sign-off เพราะ architecture decision กระทบงานทั้งสองฝั่ง

## Online Architecture & Deployment

```
Player 1..N (Kivy .exe) ──HTTPS + Socket.IO──▶ Flask API + Flask-SocketIO ──▶ PostgreSQL
                                                        │
                                              Teacher Dashboard (Jinja + Socket.IO)
```

**Stack:** Game = Kivy (.exe build) / Backend = Flask + Flask-SocketIO / DB = SQLite (dev) → PostgreSQL (deploy, ผ่าน SQLAlchemy — ดู ADR-005) / **Container = Docker Compose (`server/` เท่านั้น — SQLite default, `--profile postgres` เปิด Postgres จริง, ดู ADR-008)** / Deploy = Railway (auto-deploy จาก GitHub, build จาก `server/Dockerfile` เดียวกัน, **หลัง demo เสถียรแล้วเท่านั้น**) / Dashboard = HTML/Jinja + Socket.IO

1. **Session flow:** อาจารย์กด Create Session บน dashboard → Room Code → นักเรียนเปิด `.exe` → กรอก Room Code + ชื่อ → server ตอบ `player_id`
2. **Client เป็นแค่ client:** แสดงผล, รับ input, physics ฝั่งตัวเอง — ส่ง telemetry ทุก 2-5 วิ: `{player_id, name, distance, score, hp, module, respawn_count, status}`
3. **Server-authoritative scoring:** server คำนวณ final score จาก event log ผ่าน `core/scoring/` ตัวเดียวกับ client (import core เท่านั้น) — กัน `.exe` ถูกแก้ไขโกงคะแนน ดู ADR-006
4. **เน็ตหลุด:** offline queue ใน client + Socket.IO auto-reconnect
5. **Scale:** 30-50 คนต่อห้อง, JSON เล็ก ๆ ทุก 2-5 วิ — Flask-SocketIO พอสำหรับเดโม (ไม่ทำ MMO)
6. **API versioning:** REST endpoints อยู่ใต้ `/api/v1/` (ไม่ใช่ `/api/` เฉย ๆ) — ใส่ตั้งแต่ตอนนี้เพราะยังไม่มี client จริงเชื่อมอยู่ (D1-D6 ฝั่งเพื่อนยังไม่เริ่ม) เป็นจุดที่เปลี่ยนได้ถูกที่สุดแล้ว ไม่ต้อง breaking change ทีหลัง — `/healthz` ไม่ใส่ version เพราะเป็น infra probe ไม่ใช่ application contract
7. **Rate limiting:** `/api/v1/` ทั้ง blueprint จำกัด 60 requests/นาที (Flask-Limiter, in-memory store) กัน client bug/loop ยิงรัว ๆ ใส่ server โดยไม่ตั้งใจ — ไม่ใช่ DDoS protection จริงจัง (สมมติฐาน trusted LAN ยังอยู่)
8. **Schema migrations (Flask-Migrate/Alembic):** `server/migrations/` เก็บ migration script — **DB ใหม่เอี่ยม** (dev, test, deploy ครั้งแรก) ยังใช้ `db.create_all()` อัตโนมัติเหมือนเดิม (เร็ว ไม่ต้องคิดอะไร) แต่ **DB ที่มีข้อมูลจริงอยู่แล้ว** (เช่น deploy ทับของเดิมหลัง demo ครั้งแรก) ต้องรัน `flask db upgrade` (หรือ `make upgrade`) แทน ห้ามรัน `python -m server`/`db.create_all()` ทับ เพราะจะไม่มีทาง apply schema change ใหม่ — แก้ `server/models.py` แล้วต้อง `make migrate msg="..."` (หรือ `flask db migrate -m "..."`) ทุกครั้งหลัง deploy ครั้งแรกไปแล้ว

## เส้นตัด (ตัดจากบนลงล่างเมื่อเวลาบีบ)

1. ✂️ ตัดทันที: Railway deploy ก่อน demo (ใช้ localhost+ngrok/LAN), replay timeline บน dashboard, asset_manifest.json, telemetry ทุก 1 วิ (ใช้ 2-5 วิ)
2. ✂️ ตัดได้ถ้าจำเป็น: asset ใหม่จาก itch.io (ใช้ของเดิม), Conceptual Shift animation (ภาพนิ่ง), PostgreSQL (SQLite พอ), leaderboard ข้ามห้อง
3. ⚠️ ตัดไม่ได้ (คือตัว demo slice): Respawn+Checkpoint, Mission+เส้นชัย+Boss, quiz pre/post + Hake Gain, sync → dashboard → End Session → Export CSV

## Definition of Done

ไม่ใช่ "สร้างระบบครบ PDF" แต่คือ **vertical slice ที่กรรมการกดแล้วเห็น flow ครบ**:

> เปิด `.exe` → Join Room → เล่น → ตาย/Respawn → Boss → Score → ขึ้นจออาจารย์ → Export CSV
