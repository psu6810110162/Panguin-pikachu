# CLAUDE.md — Penguin Dash (The Great Melt)

เกม Kivy offline-first สำหรับ NSC 2026 — endless runner isometric สอนประเด็นภูมิอากาศ
Game Release scope และสถานะจริงอยู่ที่ `docs/GAME_FIRST_PLAN.md`; Flask/SocketIO เป็น P2
ที่ไม่ block และไม่อยู่ใน client bundle. คำศัพท์กลางอยู่ใน `CONTEXT.md`.

## เลเยอร์และขอบเขต
- `core/` — domain/scoring **ห้าม import Kivy, SQLite หรือ server**
- `game/controller.py` — mutation boundary + immutable ViewState; ห้าม import UI/persistence/server
- `game/`, `screens/`, `ui/` — Kivy rendering/input ระหว่าง incremental extraction
- `infrastructure/` — SQLite, runtime paths, audio, logs, telemetry, resources, crash reports
- `server/` — P2 Flask/SocketIO; optional/manual CI เท่านั้น
- `balance/v1/*.json` — ค่า tuning/content ทั้งหมด (ไม่ hardcode ในโค้ด)

## กติกาที่ห้ามพลาด (load-bearing invariants)
1. **Event-sourced** (ADR-001): `RunRecord.events` = source of truth, `RunResult` = projection
   ที่ recompute ได้เสมอ. แก้ `RunResult` ได้ที่เดียวคือ `core/scoring/evaluator.py`
2. **Single writer** (ADR-016): `GameSession` เป็น writer เดียวของ `RunRecord.events` และ
   `GameplayController` เป็น mutation boundary ของ live gameplay
3. **Determinism** (ADR-012): event log เดียวกัน → `RunResult` เดิม 100%
4. **policy_id contract**: producer (`core/interaction.py`) ต้องสร้าง policy_id ผ่าน
   `Junction.policy_id(side)` = `f"zone{zone}-{side}"` **เท่านั้น** — ห้ามส่งค่าดิบ `"left"/"right"`
   หรือประกอบ string เอง. consumer (`core/scoring/stealth.py`, `dag.py`) parse ด้วย
   `parse_policy_id`/`option_for_policy_id` ซึ่ง **raise `ValueError`** กับค่าดิบ →
   server ingest 500 หรือ Stealth Assessment/DAG อ่าน systemic ได้ 0 เงียบ ๆ.
   seam นี้ตรึงด้วย `tests/test_policy_id_contract.py` + `tests/test_interaction.py` — แก้
   producer/consumer ต้องอัปเดตเทสต์คู่กัน
5. **Balance เป็น data**: อ่านค่าจาก `balance/v1/*.json` — เห็น magic number ที่ควรมาจาก JSON = แก้
6. **Cross-lane typing — ห้าม `Any` + `hasattr`**: เมื่อต้องเรียกของอีกเลนที่ยังไม่ถูก merge
   เข้า branch อย่า type เป็น `Any` แล้ว `hasattr` guard (ปิด mypy + กลืน integration failure
   เงียบ ๆ). ใช้ **`Protocol`** ประกาศรูปร่างเมธอด — ตัวอย่าง `PolicyChoiceSink` ใน
   `core/interaction.py`

## ก่อนเปิด PR (ต้องผ่านทุกอัน)
```bash
env KIVY_NO_ARGS=1 KIVY_WINDOW=mock pytest -q
ruff check . && ruff format --check .
mypy
python -m scripts.validate_resources
python main.py --self-test
```
- **ทุก feature/logic ใหม่ต้องมี unit test** (ผูกกับ acceptance criteria ใน issue)
- **แก้ contract/dependency/security → เพิ่ม ADR ใหม่** ใน `docs/adr/` (ห้ามแก้ ADR เก่าย้อนหลัง)
- **Migration**: มี `upgrade()`+`downgrade()`, column ใหม่ nullable, chain เป็น head เดียว
- Commit ตาม Conventional Commits; รัน `pre-commit` (ต้อง activate venv ให้ `mypy` อยู่ใน PATH ก่อน push)

## รีวิวโค้ด
ใช้ `/code-review` (`.claude/commands/code-review.md`) — สรุปมาตรฐานทั้งหมดข้างบนเป็น checklist
