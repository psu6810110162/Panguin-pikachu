# ADR-011: Learning Evaluation Pipeline — แยก 3 concern + เปิดใช้ DAG

**Status:** Accepted (relates to [ADR-003](003-rule-based-evaluation.md) — DAG ที่เคย defer)

## Context

[ADR-003](003-rule-based-evaluation.md) เลือก rule-based scoring และ **เลื่อน DAG เป็น future work** โดยระบุไว้ว่า "DAG อ่านจาก event log เดียวกันได้ไม่ต้องเปลี่ยน schema" GDD V.2 ([GAME_DESIGN.md §5, §7](../GAME_DESIGN.md)) ตอนนี้ต้องการ **DAG report card จริง** (13 edge เขียว/แดง + tooltip) และ **Stealth Assessment แบบคะแนนอุณหภูมิ** (Impact + Cognitive → Net + rank S/A) ปัญหา: ถ้าโยนทุกอย่างกองใน `evaluator` เดียว dashboard/report อนาคตจะแยก "คะแนนเกม" ออกจาก "ผลการเรียนรู้" ไม่ได้

## Decision

แยก evaluation เป็น **3 concern อิสระ** (ทั้งหมด pure, `core/scoring/`, ห้าม kivy):

| Concern | อ่านจาก | ผลลัพธ์ | ไฟล์ |
|---|---|---|---|
| **Gameplay Score** (survival) | distance, meter balance, respawn | รอด/ระยะ/สมดุล | `rules.py` (มีอยู่) + rule `capitalist` ใหม่ |
| **Educational Score** (cognitive) | boss correctness + systemic-solution choices | °C ที่ลดได้ + rank | `scoring/stealth.py` ใหม่ |
| **Learning Analytics** (DAG) | decision log 13 จุด | graph projection (เขียว/แดง + tooltip) | `scoring/dag.py` ใหม่ |

- **DAG เป็น domain pipeline ไม่ใช่ UI:** `Decision Graph → Evaluation → Projection (serializable) → Renderer` — `scoring/dag.py` สร้าง projection ได้โดยไม่พึ่ง kivy; `screens/report.py` เป็นแค่ renderer หนึ่ง (server render projection เดียวกันได้)
- relationship (node/edge, เฉลย tooltip) เป็น data ที่ `balance/v1/dag.json` — แก้เนื้อหาไม่แตะโค้ด (Rule 7)
- Hake Gain เดิม (`hake.py`) + pre/post-test **ยังอยู่** ในกลุ่ม Educational Score (merge ไม่ทิ้ง)

## Consequences

- ได้: dashboard แยกแสดง "เก่งเล่นเกม" vs "เข้าใจเนื้อหา" ได้, DAG มาโดยไม่แตะ RunRecord (ตามที่ ADR-003 คาดไว้), server render report ได้เพราะ projection เป็น pure data
- เสีย: มี module scoring เพิ่ม 2 ไฟล์ + ต้อง maintain `dag.json` — แต่ทดสอบแยกได้ (edge count = 13, projection deterministic)
- Revisit เมื่อ: ถ้าต้องการ weight เชิงเวลา/ผลสะสมข้าม decision (สิ่งที่ ADR-003 บอกว่า DAG เต็มรูปจะทำได้) — ต่อยอดใน `dag.py` โดยใช้ event log เดิม
