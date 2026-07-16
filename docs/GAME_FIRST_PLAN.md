# Penguin Dash Game-First Release Plan v3

> Source of truth ของ Game Release ปัจจุบัน เอกสาร roadmap อื่นเป็น historical reference และต้องชี้กลับมาที่ไฟล์นี้

## Engineering Principles

1. Gameplay First
2. Offline First
3. Deterministic Core
4. Single Writer
5. Immutable ViewState
6. UI Reads, Domain Writes
7. Release over Features
8. Tests before Refactor
9. Recover Safely, Never Hide Failure
10. P2 Work Must Not Block the Game

---

## PLAN

### Product goal

ส่งเกม Local Single-player สำหรับ Windows 10/11 x64 เป็น ZIP ซึ่งแตกแล้วเปิด
`PenguinDash.exe` ได้โดยไม่ต้องติดตั้ง Python ข้อมูลผู้เล่นต้องอยู่หลังปิด–เปิดเกม และ build
ต้องวินิจฉัยตัวเองได้ด้วย `PenguinDash.exe --self-test`

### Priority และ scope boundary

- **P0 — Game:** gameplay, application architecture, UI/UX, local save และ tests
- **P1 — Release:** Windows ZIP, self-test, resource validation และ release artifacts
- **P2 — Optional:** Teacher Dashboard, Flask/Socket.IO, Sync, Docker, PostgreSQL, Railway,
  installer และ online features

P2 code ไม่ถูกลบ แต่ freeze ไว้: ไม่พัฒนาเพิ่ม, ไม่อยู่ใน client bundle, workflow เป็น manual และ
ห้าม block Game Release. Installer เป็น P2; P1 ส่ง ZIP แบบ onedir

### Ownership — 30 points ต่อคน

| Owner | Workstream | Points |
|---|---|---:|
| Architecture/Platform | ADR, architecture rules, RFC และ release workflow | 4 |
| Architecture/Platform | Controller extraction, error boundary และ single writer | 8 |
| Architecture/Platform | Runtime paths, SQLite migration/recovery, logging/telemetry | 7 |
| Architecture/Platform | Replay, golden, long-run และ performance tests | 6 |
| Architecture/Platform | Windows build, CI matrix และ security scan | 5 |
| UI/UX + Kivy | UX state map, principles และ UI spec | 4 |
| UI/UX + Kivy | HUD/Decision/Boss/Respawn components | 8 |
| UI/UX + Kivy | Menu/Gameplay/Game Over/Report integration | 6 |
| UI/UX + Kivy | Resource manifest และ asset/license validation | 5 |
| UI/UX + Kivy | Visual/performance playtest และ release documentation | 7 |

### Timeline, freeze และ dependencies

| Day | Milestone | Dependency / exit condition |
|---:|---|---|
| 1 | Baseline, principles, UX state map, ADR/RFC draft | Existing regression suite green |
| 2 | Controller/ViewState contract 80% freeze | Dev ทั้งสองคน review contract |
| 3–4 | Controller extraction + UI integration spike | Headless controller tests + one screen path |
| 4 | Hard contract freeze | Integration spike ผ่าน; breaking change ใช้ RFC |
| 5–6 | Runtime/save/resource/log hardening | Recovery และ startup validation ผ่าน |
| 7 | Replay, long-run, visual/performance gates | Regression และ budget มีหลักฐาน |
| 8 | Cut `release/0.1`; feature freeze | P0/P1 feature-complete |
| 9 | RC1 → fixes → RC2 | Clean Windows verification |
| 10 | GA `v0.1.0` | Definition of Done ผ่านทั้งหมด |

Dependency หลัก: Controller contract มาก่อน screen integration; manifest/license มาก่อน GA;
runtime paths มาก่อน packaged self-test; RC2 มาก่อน GA

### Branch และ release strategy

```text
main
 ├─ feat/gameplay-controller
 ├─ feat/ui-components
 ├─ test/game-regression
 └─ build/windows-package
          ↓ reviewed PRs
        main
          ↓ Day 8
     release/0.1
          ↓ bugfix only
 v0.1.0-rc.1 → v0.1.0-rc.2 → v0.1.0
          ↓
       main
```

- ไม่มี long-lived `develop`; ถ้าจะเปลี่ยนเป็น Gitflow ต้องมี process RFC
- Feature branch อายุสั้น, PR เล็ก, CI ผ่านและ review ไขว้
- หลัง cut `release/0.1` ห้าม feature ใหม่ทั้ง release branch และ main
- RC รับเฉพาะ P0/P1 bug fix; fix หลัง RC2 ต้องออก RC3 ห้ามข้ามไป GA
- GA merge กลับ main, tag `v0.1.0` แล้วลบ release branch

### Daily handoff

- วันนี้ทำอะไร:
- Contract เปลี่ยนหรือไม่ / RFC ใด:
- Blocker หรือ release risk:
- จุดที่ต้องการ review จากอีกคน:

---

## SPEC

### Dependency direction

```text
Kivy Input / Screen
        ↓ commands
GameplayController
        ↓
Core Domain
        ↓ completed result
Local Repository

GameplayController
        ↓ new frozen snapshot
GameplayViewState
        ↓
Renderer / HUD / Overlay
```

กฎบังคับ:

- Core/controller ห้าม import Kivy, SQLite, filesystem adapter หรือ server
- Renderer/UI ห้ามเข้าถึง mutable domain objects
- `GameplayController` เป็น mutation boundary ของ live gameplay
- `GameSession` เป็น writer เดียวของ RunRecord/event log
- Persistence รับ completed result ผ่าน repository port
- Client entry point ห้าม import `server/`
- Architecture tests ตรวจ dependency และ single-writer rules

### Interface stability

Day 2 เป็น 80% contract freeze:

```text
start_run()
tick(dt)
move(side)
use_eco_seed()
pause()
resume()
restart()
view_state() -> GameplayViewState
take_terminal_result() -> TerminalResult | None
```

Additive change ที่ไม่กระทบผู้ใช้ interface ทำได้. Breaking change ต้องเพิ่ม mini-RFC ใน RFC LOG
พร้อมเหตุผล, alternatives, UI/test impact และ migration; ทั้งสองคน approve ก่อน merge. Hard freeze
หลัง controller/UI integration spike ผ่านใน Day 4

### Immutable ViewState

`GameplayViewState` เป็น frozen dataclass และสร้าง object ใหม่ทุก update/render cycle โดยครอบคลุม:

- Run/decision state
- Distance, gems, hearts, heat/anger meters
- Inventory
- Junction/boss presentation
- Countdown, overlay, feedback
- Terminal reason
- Recoverable error notice

Snapshot เก่าต้องไม่เปลี่ยนเมื่อ controller เดินต่อ

### Error boundary

- **Recoverable:** save fail, optional audio fail หรือ corrupted save ที่ recover แล้ว — เล่นต่อ,
  แสดง notice และเขียน error log
- **Fatal startup:** required resource หาย, balance schema ผิด, manifest fail — ไม่เริ่ม gameplay,
  แสดง safe error screen และตำแหน่ง crash report
- **Invariant violation:** state/domain contract ผิด — tests fail; release app boundary สร้าง crash report

ห้ามใช้ broad `except Exception` ภายใน domain เพื่อกลืน error; อนุญาตเฉพาะ app boundary ที่ log และ
สร้าง crash report ก่อนแสดง safe screen

### SQLite, atomic files และ recovery

- Player data ใช้ SQLite; transaction ทุก write
- `journal_mode=WAL`, `synchronous=FULL`, `foreign_keys=ON`
- `PRAGMA user_version` เป็น DB schema version; `save_version` แยกเป็น 1
- ใช้ SQLite backup API ก่อน migration และ `PRAGMA quick_check` ตอน startup
- DB เสียถูก rename เป็น `game.db.corrupt-<UTC>` แล้วสร้างใหม่พร้อม recoverable notice
- `tmp → flush → fsync → os.replace` ใช้เฉพาะ JSON/settings, telemetry summary และ crash report;
  ห้ามใช้แทน SQLite database ที่เปิดอยู่

### Runtime path และ local operations

Bundle resources เป็น read-only; user data อยู่ `%LOCALAPPDATA%/PenguinDash/`:

```text
data/game.db
settings/
logs/runtime.log
logs/error.log
crash/crash-<UTC>.json
telemetry/metrics.jsonl
```

Runtime/error log หมุนไฟล์ละ 5 MiB เก็บ 3 รุ่น; telemetry ไฟล์ละ 1 MiB เก็บ 3 รุ่น

Offline telemetry เก็บได้เฉพาะ build version, play duration, terminal reason, average/p95 FPS,
crash count และ save-recovery count. ห้ามเก็บชื่อผู้เล่น, event choices, secret หรือส่งออกจากเครื่อง

### Resource manifest

`resource_manifest.json` schema version 1 ระบุ ID, kind, source, bundle destination,
required/optional, SHA-256, image dimensions/frame contract, font family/loadability,
audio format/playback requirement, balance JSON contract, license และ credit reference

Validate ใน CI, packaged self-test และ startup. Required resource/schema/checksum fail เป็น fatal startup;
license pending block GA

### Versioning และ build metadata

| Contract | Version |
|---|---|
| App semantic version | `0.1.0` |
| RunRecord schema | ค่า `core.schema.SCHEMA_VERSION` |
| Save version | `1` |
| Balance | `v1` |
| Resource manifest | `1` |
| Protocol | contract เดิม, dormant P2 |

CI สร้าง `build_info.json` พร้อม Git SHA, UTC build time, Python/Kivy/PyInstaller versions และ
feature flags ที่ปิด online/classroom

### Test และ performance gates

Required Game Release jobs:

- Ubuntu: lint, format, mypy, architecture และ game/core tests
- Windows: game/core/path tests, onedir build, packaged self-test และ bundle scan
- Server/Docker: optional/manual, ไม่ block

Golden replay:

```text
RunRecord event log → evaluator → canonical RunResult JSON → SHA-256 → expected hash
```

- ทุก field ต้องเหมือนเดิม; JSON ใช้ sorted keys และ canonical separators
- เปลี่ยน golden เฉพาะ PR label `scoring-change`, อธิบายใน changelog และ approve ทั้งสองคน
- Full input/visual replay เป็น P2 เพราะ schema ยังไม่มี input timeline ครบ

Performance:

- Design target 60 FPS
- Controller `tick()` target p95 < 4 ms; automated CI guard ≤ 8 ms
- Physical Windows playtest 10 นาที: p95 frame ≤ 20 ms, 99% frames ≤ 33 ms, ไม่มี stall ต่อเนื่อง
  ที่ junction/respawn/boss
- 100-run headless: callback/reference กลับ baseline; retained heap หลัง warm-upเพิ่ม ≤ 5 MiB

Additional automated/manual gates:

- Corrupted/truncated DB recover ได้
- Resource dimensions/font/audio/balance schema ผ่าน
- UI snapshot 1280×720 และ 1920×1080 ผ่าน visual review
- `PenguinDash.exe --self-test` exit 0
- ไม่มี TODO/FIXME/HACK/XXX ใน `main.py`, `core/`, `game/`, `screens/`, `ui/`

### Security และ release artifacts

ก่อน ZIP ต้องไม่มี `.env`, secrets, debug endpoint/console, sample credentials, development DB,
server module/dependency, report/temp/cache artifact หรือ absolute developer path

ZIP ประกอบด้วย:

- `PenguinDash.exe` และ `_internal/`
- `README.txt`, `CHANGELOG.md`, `KNOWN_ISSUES.md`
- `LICENSES.md`, `THIRD_PARTY_NOTICES.md`
- `build_info.json` และ ZIP SHA-256 checksum

Release flow:

1. **RC1:** feature-complete build + bug discovery
2. **RC2:** RC1 fixes + clean-machine verification
3. **GA:** CI, packaged self-test, two-run playthrough, save recovery, performance, visual,
   security และ license gates ผ่านทั้งหมด

### Definition of Done

- P0/P1 ครบ; P2 ไม่ block และไม่อยู่ใน client ZIP
- Game loop เล่นครบสองรอบติด
- Windows clean machine เปิดได้โดยไม่มี Python
- Save/history/gems อยู่หลังปิด–เปิด
- Golden replay/deterministic tests และ performance budgets ผ่าน
- ไม่มี P0/P1 bug หรือ debt markers ใน game code
- STATUS ตรงกับสิ่งที่ merge/verify จริง; ADR index และ ADR-016 เสร็จ
- RC1 และ RC2 ผ่านก่อน GA

---

## STATUS

ส่วนนี้บันทึกเฉพาะสิ่งที่ merge หรือ verify แล้ว ไม่ใช่ backlog. งาน local ที่ยังไม่มี PR ใช้ `PR —`
และต้องระบุหลักฐาน command/test; ห้ามเขียนว่า release-ready จากการมีโค้ดเพียงอย่างเดียว

| Date | Owner | PR | Verified reality | Evidence |
|---|---|---|---|---|
| 2026-07-16 | Team | — | Baseline ก่อน Game-First ผ่าน 261 tests | `pytest -q` |
| 2026-07-16 | Team | — | Teacher Dashboard/Docker เป็น P2 และแยกจาก required CI | workflow + bundle exclude rules |
| 2026-07-16 | Architecture/Platform | — | Game/core/infrastructure regression ผ่าน 287 tests | `pytest -q` |
| 2026-07-16 | Architecture/Platform | — | Lint/format และ typed core/server/infrastructure ผ่าน | scoped `ruff` + `mypy` |
| 2026-07-16 | Architecture/Platform | — | Source-tree self-test และ resource validation ผ่าน 47 entries | `python main.py --self-test` |
| 2026-07-16 | Architecture/Platform | — | Golden replay, controller p95 guard, 100-run retention, corruption recovery และ architecture gates ผ่าน | automated suite |

### Open release blockers (ไม่ใช่สถานะเสร็จ)

- ต้อง review provenance/license ของ BGM และ Jump SFX ก่อน GA
- ต้องทำ physical Windows visual/performance playtest และ clean-machine two-run playthrough
- Controller/UI migration ยังเป็น integration seam; hard contract freeze ต้องเกิดหลัง Day 4 spike
- ยังไม่ได้ cut `release/0.1`, RC1 หรือ RC2

---

## RFC LOG

ใช้เมื่อเปลี่ยน frozen interface หรือ P0/P1 scope หลังเริ่มงาน

### Mini-RFC template

- **Date / owners:**
- **Proposed breaking change:**
- **Why now:**
- **Alternatives considered:**
- **UI and test impact:**
- **Migration:**
- **Approvals:**

ยังไม่มี breaking RFC
