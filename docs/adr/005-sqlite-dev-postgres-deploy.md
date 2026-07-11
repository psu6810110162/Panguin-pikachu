# ADR-005: SQLite (SQLAlchemy) สำหรับ dev local, PostgreSQL สำหรับ deploy

**Status:** Accepted

## Context

Backend ต้องเก็บ session/player/run/report data ที่ dashboard อ่านมาแสดง leaderboard, สถานะ real-time, และ export CSV โจทย์คือเลือก database ที่ (1) ไม่เพิ่ม friction ให้ dev local ระหว่าง 3 วัน (2) รองรับ deploy จริงบน Railway สำหรับเดโมวันแข่ง

พิจารณา MongoDB ด้วย — เหมาะกับการเก็บ event log เป็น document ตรงตัวไม่ต้อง normalize (RunRecord เป็น nested structure อยู่แล้วตาม [ADR-001](001-runrecord-contract.md))

## Decision

ใช้ **SQL ผ่าน SQLAlchemy**: SQLite สำหรับ dev local, PostgreSQL สำหรับ deploy บน Railway — โค้ดเดียวกัน สลับแค่ connection string

เหตุผลที่เลือก SQL แทน MongoDB:

- งานหลักของ dashboard คือ relational: ranking (ORDER BY score), aggregate (COUNT respawns, AVG scores), join (session → students → runs) — SQL ทำเรื่องพวกนี้ตรงไปตรงมากว่า
- Export CSV คือ SQL query ธรรมดา ไม่ต้อง flatten document structure
- SQLite = ไฟล์เดียว ไม่ต้องติดตั้ง service แยกสำหรับ dev — zero friction ตรงกับ requirement (1)
- Railway รองรับ PostgreSQL เป็น managed service พร้อม deploy ตรงกับ requirement (2)
- Event log ของ RunRecord (nested) เก็บเป็น JSON column ใน PostgreSQL/SQLite ได้อยู่แล้ว (ทั้งสองรองรับ JSON column) — ไม่เสียจุดแข็งของ document-style ที่ MongoDB จะให้

## Consequences

- ได้: dev setup เร็ว (`pip install` ไม่ต้องรัน DB service แยก), production path ชัดเจนผ่าน SQLAlchemy โดยไม่ต้อง rewrite query, ranking/CSV export ทำง่าย
- เสีย: schema migration ต้อง manage ผ่าน SQLAlchemy models (เทียบกับ MongoDB ที่ schema-less) — ยอมรับได้เพราะ schema ของโปรเจกต์นี้นิ่งตั้งแต่ freeze RunRecord แล้ว
