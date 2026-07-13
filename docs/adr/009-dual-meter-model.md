# ADR-009: Dual-Meter เป็น pure state model ใน core/

**Status:** Accepted

## Context

GDD V.2 ([GAME_DESIGN.md §3.1](../GAME_DESIGN.md)) ระบุหลอดวัดคู่ขนานชัดเจน 2 ตัว: **Heat Meter** (มิติสิ่งแวดล้อม) และ **Capitalist Anger** (มิติเศรษฐกิจ) — หลอดใดแตะ 100 = Game Over ดีไซน์เดิมใน [OVERVIEW.md](../OVERVIEW.md) พูดถึง "Heat / dual meters" กว้าง ๆ แต่ไม่เคยระบุหลอดที่สองชัด และ `core/scoring/rules.py` มี `heat_controlled_pct` ที่พับ `meter_deltas["heat"]` อยู่แล้ว คำถามคือ: เก็บ logic หลอดไว้ที่ไหน และเพิ่มหลอดที่สองต้องแตะ contract (`RunRecord`) ไหม

## Decision

- หลอดเป็น **pure state model ที่ `core/meters.py`** — ไม่ import kivy (บังคับด้วย `tests/test_no_kivy_in_core.py`) เพื่อให้ server re-score ได้ด้วยโค้ดตัวเดียวกัน (สอดคล้อง ADR-006 server-authoritative)
- **ไม่แก้ RunRecord schema:** `PolicyChoiceEvent.meter_deltas` เป็น `dict[str, float]` คีย์ด้วยชื่อหลอดอยู่แล้ว — เพิ่ม `"capitalist_anger"` ข้าง `"heat"` ได้โดยไม่เปลี่ยน contract (ADR-001 ไม่ถูกละเมิด)
- **Invariants (นิยามเต็มที่ [state-machines.md §2](../state-machines.md)):** ทั้งสองหลอด `float` clamp `[0, 100]`, `+`=แย่ลง `−`=ดีขึ้น, เริ่ม `50.0` ทั้งคู่ (เก็บใน `balance/v1/difficulty.json`), Game Over เมื่อ `>= 100`, **ค่า 0 = ปลอดภัยไม่แพ้** (แก้ความกำกวม "0 หรือ 100" ใน sprint doc), **ไม่มี passive decay** (เปลี่ยนผ่าน event เท่านั้น → deterministic)
- เพิ่ม scoring rule `capitalist` ใน `rules.py` คู่กับ `heat_controlled_pct` เดิม (ไม่แทนที่)

## Consequences

- ได้: หลอดที่สองมาโดยไม่แตะ contract/migration, unit test หลอดแยกจาก render (pure), server re-score ได้เพราะ core ไม่มี kivy
- เสีย: หลอดไม่มี coupling/decay ใน v1 — dynamics เรียบกว่าเกมจริงบางเกม (ยอมรับได้ เพราะ explainable + test ง่าย)
- Revisit เมื่อ: ถ้าอยากได้ feedback loop ระหว่างหลอด (เช่น heat สูง → anger เพิ่มเอง) ค่อยเพิ่ม coupling rule ทีหลัง โดย state model + event log เดิมรองรับได้
