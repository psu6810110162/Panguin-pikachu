# ADR-003: Rule-based evaluation แทน DAG (DAG = future work)

**Status:** Accepted — DAG (future work ที่ระบุไว้) ถูกเปิดใช้แล้วใน [ADR-011](011-learning-evaluation-pipeline.md) โดยอ่าน event log เดิมตามที่ ADR นี้คาดไว้ (rule-based ยังใช้เป็น Gameplay Score)

## Context

PDF ต้นฉบับ (flowchart NSC2026) ระบุ "DAG Evaluation Phase" — แปลงการตัดสินใจของผู้เล่นเป็น Directed Acyclic Graph แล้ว map เข้า learning objectives ก่อนคำนวณ rubric score แนวทางนี้ทรงพลังแต่ implementation ใช้เวลามาก และในบริบทเดโม 3 วัน กรรมการจะไม่เห็นความแตกต่างระหว่าง DAG evaluation กับกติกาที่อธิบายได้ตรงไปตรงมา — DAG "ดูซับซ้อน" แต่ผลลัพธ์ที่โชว์ได้จริงเหมือนกัน

## Decision

ใช้ **Rule-based Evaluation** แทน DAG ในเวอร์ชันเดโม:

```
Policy ดี + Heat ต่ำ + Mission ผ่าน = Environmental Score
```

กติกาแบบนี้อธิบายได้ในหน้าจอเดียว ตรวจสอบได้ (explainable) และ implement ได้เร็วกว่ามาก อยู่ใน `core/scoring/rules.py` แยกจาก `evaluator.py` (orchestration) และ `hake.py` (Hake Gain calculation: `(post − pre) / (100 − pre)`)

DAG-based evaluation เก็บไว้เป็น **future work** — โครงสร้าง event log ใน [ADR-001](001-runrecord-contract.md) ออกแบบมาให้รองรับได้โดยไม่ต้องเปลี่ยน schema (DAG สามารถอ่านจาก event log เดียวกัน)

## Consequences

- ได้: ส่งมอบได้ทันตาม timeline 3 วัน, คะแนนที่คำนวณออกมาอธิบายให้กรรมการฟังได้ตรงไปตรงมา, unit test ง่าย (pure function ไม่มี graph traversal ให้ debug)
- เสีย: ไม่ได้ modeling ความสัมพันธ์เชิงเหตุ-ผลที่ซับซ้อนระหว่างการตัดสินใจหลายจุด (สิ่งที่ DAG ทำได้) — scoring แบบ rule-based เป็นเส้นตรงกว่า
- Revisit เมื่อไหร่: ถ้าโปรเจกต์ไปต่อหลัง NSC และต้องการ scoring ที่ nuanced ขึ้น (เช่น weight การตัดสินใจตามลำดับเวลา หรือผลสะสมข้าม module) ค่อยพิจารณา DAG โดยอ้างอิง event log ที่มีอยู่แล้ว
