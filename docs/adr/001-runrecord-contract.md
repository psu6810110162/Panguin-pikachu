# ADR-001: RunRecord เป็น contract กลาง + schema_version + event log

## Context

เกม (Kivy, ฝั่งเพื่อน) กับ backend (Flask, ฝั่งคุณ) ต้องแลกเปลี่ยนข้อมูลรอบเล่นเดียวกัน (การตัดสินใจ, ระยะทาง, meters, คะแนน quiz) โดยพัฒนาแยกกันคนละ CLI ไม่รอกัน ถ้าไม่มี contract ตายตัวตั้งแต่ต้น สอง codebase จะแตกโครงสร้างข้อมูลกันแน่นอน

## Decision

- `core/schema.py` นิยาม `RunRecord`: `{schema_version, run_id, player_id, events: list[GameEvent], state: RunState, result: RunResult | None}`
- **Event = source of truth, result = projection** — ห้ามปนกัน ทุกการกระทำ (Collect/Respawn/Policy/Mission/Boss) เป็น typed event ที่ append เข้า `events`, ไม่มีที่ไหนแก้ state หรือ score ตรง ๆ
- `RunState` เป็น state machine (`LOBBY → RUNNING → RESPAWNING → BOSS → FINISHED → SYNCED`) พร้อม transition validation ใน `core/state.py` — `transition(RUNNING, BOSS)` ต้องผ่านเงื่อนไข (เช่น distance ≥ 1000) ห้าม set state ตรง ๆ จากที่ไหนก็ได้
- `schema_version` เริ่มที่ `"1.0"` ตั้งแต่วันแรก
- Freeze schema ในเช้าวันที่ 1 ก่อนงานอื่นเริ่ม — ใครอยากแก้ทีหลังต้องเปิด PR คุยกัน

## Consequences

- ได้: debug ง่าย (replay จาก event log ได้เสมอ), คำนวณผลใหม่ได้โดยไม่ต้องเชื่อ state ที่บันทึกไว้, versioning กันเกมเก่าพังเมื่อ schema เปลี่ยนทีหลัง, สอง codebase พัฒนาขนานกันได้จริงเพราะรู้ contract ล่วงหน้า
- เสีย: ต้องเขียน events ให้ครบทุกจุดที่ RunRecord เปลี่ยน (มีวินัยมากกว่าการ mutate field ตรง ๆ)
- Future work: DAG-based evaluation (ดู [ADR-003](003-rule-based-evaluation.md)) จะอ่านจาก event log เดียวกันได้โดยไม่ต้องเปลี่ยน schema
