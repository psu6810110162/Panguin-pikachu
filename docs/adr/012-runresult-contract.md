# ADR-012: RunResult field ใหม่เป็น projection (denormalized read-model)

**Status:** Accepted (extends [ADR-001](001-runrecord-contract.md), [ADR-006](006-server-authoritative-scoring.md))

## Context

Stealth Assessment (ADR-011) ต้องการค่าใหม่: `net_impact_score`, `rank`, `temp_reduced_c`, `cognitive_score` คำถามแรกที่ต้องตอบ **ก่อน** เพิ่ม column: *ต้อง persist จริงไหม?* — ค่าเหล่านี้ทั้งหมด **derive จาก event log ได้** ([ADR-001](001-runrecord-contract.md): events = source of truth, `result` = projection ที่ recompute ได้; `events_json` ถูกเก็บใน `RunModel` อยู่แล้ว)

## Decision

- **RunResult คือ projection ไม่ใช่ source of truth** — field ใหม่เก็บเป็น **denormalized read-model** เพื่อ query/leaderboard/CSV เร็วเท่านั้น server **re-derive จาก `events_json` เสมอ** (ADR-006) ไม่เชื่อค่าที่ client ส่งมา
- **Invariant — projection ต้อง deterministic:** event log เดียวกัน → RunResult เดิม 100% (หัวใจของ replay + server re-score) — บังคับด้วย property test (`evaluate()` ซ้ำ 2 รอบ = ผลเท่ากัน)
- ใช้ `RunRecord.schema_version` (มีอยู่แล้วในโค้ด) เป็น guard สำหรับ future event migration
- **เพิ่ม field:** ที่ `RunResult` (`core/schema.py`) + column ที่ `server/models.py::RunModel` — **nullable** ทั้งหมด (backward compatible, run เก่าไม่มีค่าไม่พัง) + Alembic migration ที่มีทั้ง `upgrade()`/`downgrade()`
- **Feature flag** `STEALTH_ASSESSMENT_ENABLED` (env) — เปิด/ปิด field+score ใหม่แบบ toggle; rollback = `make downgrade` + ปิด flag (ไม่ต้อง restore DB)
- แตะ contract (RunResult) จึงต้องมี ADR นี้ตาม Rule 6 — ADR-001 ไม่ถูก "แก้" แต่ **ขยาย** (result เป็น projection ที่โตได้, events ไม่เปลี่ยน)

## Consequences

- ได้: leaderboard/CSV query เร็ว (ไม่ต้อง replay ทุกครั้ง), rollback ปลอดภัย (nullable + flag), replay ยังตรงเพราะ projection deterministic
- เสีย: มี denormalized data ที่ต้อง regenerate ถ้าสูตรเปลี่ยน — ยอมรับได้เพราะ server re-derive จาก events เสมอ (regenerate = re-run evaluate)
- Revisit เมื่อ: ถ้า projection เริ่มไม่ deterministic (เช่น พึ่ง timestamp/random) — ผิด invariant, ต้องแก้ให้ pure หรือ seed ให้ทันที
