---
description: รีวิว PR หรือ diff ของโปรเจกต์ Penguin Dash ตามมาตรฐานทีม (security, correctness, สถาปัตยกรรม, เทสต์)
argument-hint: <PR number | PR URL | ว่างไว้เพื่อรีวิว diff ปัจจุบัน>
---

คุณกำลังรีวิวโค้ดของโปรเจกต์ **Penguin Dash (The Great Melt)** — เกม Kivy + Flask backend
รีวิวเป้าหมาย: **$ARGUMENTS** (ถ้าว่าง ให้รีวิว `git diff` ของ working tree / branch ปัจจุบัน)

## วิธีดึงโค้ดมารีวิว
- ถ้าเป็นเลข/URL ของ PR: `gh pr view <n>` (ดูรายละเอียด) + `gh pr diff <n>` (diff) + `gh pr diff <n> --name-only`
- ถ้าว่าง: `git diff main...HEAD` หรือ `git diff` แล้วแต่บริบท
- **รันเทสต์จริงเสมอ** ก่อนสรุป: `env KIVY_NO_ARGS=1 KIVY_WINDOW=mock pytest -q` + `ruff check .` + `mypy core/ server/`
- ยืนยันสมมติฐานด้วยการรัน/อ่านโค้ดจริง อย่าเดา — ถ้าอ้างว่า "จะ crash" ให้รันพิสูจน์

## มาตรฐานเฉพาะของโปรเจกต์นี้ (ตรวจทุกครั้ง)
1. **core/ ห้าม import kivy** (ยกเว้น `core/audio.py`) — บังคับด้วย `tests/test_no_kivy_in_core.py` เพราะ server re-import ตรรกะ
2. **Event-sourced contract** (ADR-001): `events` = source of truth, `RunResult` = projection ที่ recompute ได้เสมอ — ห้ามแก้ `RunResult` นอก `core/scoring/evaluator.py`
3. **Server-authoritative scoring** (ADR-006): `evaluate()` ประมวลผล event log จาก **client ที่เชื่อไม่ได้** → ต้องทนต่อ input เสีย (ห้าม crash จาก field ผิดรูป เช่น `policy_id`)
4. **policy_id contract**: game/ ต้อง emit `f"zone{zone}-{side}"` (`core/junction_data.py`) — scoring/dag ใช้ย้อนหา systemic flag; ตรวจว่า producer/consumer ตรงกัน
5. **Balance เป็น data** (`balance/v1/*.json`) ไม่ใช่ค่า hardcode ในโค้ด — ถ้าเห็น magic number ที่ควรมาจาก JSON ให้ flag
6. **Determinism** (ADR-012): event log เดียวกัน → RunResult เดิม 100% (replay/re-score)
7. **type hints ครบ** ใน core/game/server (mypy `disallow_untyped_defs`)
8. **ทุก feature มี unit test** (acceptance criteria ใน issue) — PR ที่เพิ่ม logic แต่ไม่เพิ่มเทสต์ = ขอแก้
9. **แก้ contract/dependency/security ต้องมี ADR** ใหม่ (`docs/adr/`) — ห้ามแก้ ADR เก่าย้อนหลัง
10. **Migrations**: มี `upgrade()`+`downgrade()`, column ใหม่ nullable (backward-compat), chain เป็น head เดียว

## มิติการรีวิว
- **Security**: injection, XSS, การ crash จาก untrusted input (event log/policy_id), teacher_token/HMAC, secrets ในโค้ด
- **Correctness**: edge case (input ว่าง/None/ผิดรูป), race (ingest upsert), off-by-one, contract ระหว่าง PR (producer↔consumer)
- **Performance**: N+1 query, ลูปไม่มีขอบเขต, object churn ในลูปเกม 60 FPS
- **Maintainability**: ชื่อ, single responsibility, dead code, เทสต์ครอบคลุม, เอกสาร ADR

## รูปแบบผลลัพธ์ (ภาษาไทย)
```markdown
## Code Review: <หัวข้อ PR / diff>
### Summary
<1-2 ประโยค: การเปลี่ยนแปลง + คุณภาพรวม + ผล pytest/mypy/ruff>
### 🔴 Critical Issues
| # | File | Line | Issue | Severity |
### 🟡 Suggestions
| # | File | Line | Suggestion | Category |
### 🟢 What Looks Good
- <จุดเด่น>
### Verdict
Approve / Request Changes / Needs Discussion  (+ merge order ถ้าเป็น PR stack)
```

## กติกา
- ทุก finding ต้องชี้ **ไฟล์:บรรทัด** และบอก **impact จริง** (เช่น "ทำ ingest ล่ม 500") ไม่ใช่ opinion ลอย ๆ
- แยก **บั๊กในตัว PR** ออกจาก **ปัญหา integration ข้าม PR** ให้ชัด และระบุว่า fix อยู่ฝั่งไหน (Dev A/Dev B, PR ไหน)
- ให้เครดิตสิ่งที่ทำได้ดีจริง อย่ารีวิวแต่ข้อเสีย
- อย่าโพสต์คอมเมนต์ลง GitHub เองจนกว่าจะได้รับอนุญาต — เสนอร่างก่อน
