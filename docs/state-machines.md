# State Machines — Penguin Dash

> รวม state machine + invariants ทุกตัวไว้จุดเดียวเพื่อ review ง่าย. ADR ที่เกี่ยวข้องอ้างถึงไฟล์นี้แทนกระจายนิยาม.
> เกี่ยวข้อง: [adr/009 Dual-Meter](adr/009-dual-meter-model.md) · [adr/010 Health+Respawn](adr/010-health-respawn-state-model.md) · [GAME_DESIGN.md](GAME_DESIGN.md)

---

## 1. Run Lifecycle (`core/state.py` — มีอยู่แล้ว)

State machine ของการเล่น 1 รอบ, บังคับด้วย `_ALLOWED_TRANSITIONS` + `validate_transition()`:

```
LOBBY → RUNNING → RESPAWNING → RUNNING   (loop ช่วงวิ่ง)
                     │
        RUNNING → BOSS   (context: distance_m >= BOSS_MIN_DISTANCE_M = 1000)
                     │
                  BOSS → FINISHED → SYNCED
```

- **Invariant:** `RUNNING → BOSS` ต้องมี `distance_m >= 1000`; **BOSS ไม่มีทางกลับ RUNNING** (ไม่มี respawn ในบอส — ดู §3)
- ผิด transition → raise `InvalidTransitionError`

---

## 2. Dual-Meter Invariants (ADR-009)

หลอด 2 ตัว **อิสระต่อกัน** (ไม่ coupling ใน v1 เพื่อ explainable) — ค่าจริงอยู่ [`balance/v1/difficulty.json`](../balance/)

| ประเด็น | นิยาม v1 |
|---|---|
| Meters | `heat`, `capitalist_anger` |
| Type / Range | `float`, clamp `[0.0, 100.0]` |
| ทิศทาง | `+` = แย่ลง, `−` = ดีขึ้น (ตรง GDD §6) |
| ค่าเริ่มต้น | `50.0` ทั้งคู่ (ปรับได้ใน `difficulty.json`) — สอดคล้อง `rules.heat_controlled_pct(starting_heat=50.0)` เดิม |
| **Game Over** | `heat >= 100.0` **หรือ** `capitalist_anger >= 100.0` |
| ค่า 0 | `= 0` คือ **ปลอดภัย/ดีที่สุด ไม่แพ้** (แก้ความกำกวม "0 หรือ 100" ใน sprint doc — ยืนยันใน ADR-009) |
| Decay | **ไม่มี passive decay** — เปลี่ยนผ่าน event เท่านั้น → deterministic |
| แหล่งเปลี่ยนค่า | apply `meter_deltas: dict[str, float]` จาก `PolicyChoiceEvent` + Eco-Seed (ลด heat) เท่านั้น |

```
apply(delta):  value = clamp(value + delta, 0, 100)
               if value >= 100:  → GAME_OVER
```

> `meter_deltas` เป็น dict คีย์ด้วยชื่อ → เพิ่ม `"capitalist_anger"` **ไม่แก้ RunRecord schema**

---

## 3. Hearts / Health (ADR-010)

```
        pickup(+1, cap 5)
        ┌───────────────┐
        ▼               │
     ALIVE ──fall──► RESPAWNING ──(T=respawn_seconds, invincible)──► ALIVE
        │   hearts-=1 on enter        │
        │                             └─ ถ้า hearts == 0 ─────► GAME_OVER
        │
        └── meter >= 100 (ดู §2) ─────────────────────────────► GAME_OVER
```

**Invariants:**
- `hearts ∈ [0, 5]`; เริ่ม 5; pickup เพิ่ม +1 cap ที่ 5
- **RESPAWNING:** ผู้เล่น invincible ตลอด `respawn_seconds` (กัน double-hit ตกซ้ำ), respawn ที่ **last checkpoint** (`grid` เป็นเจ้าของตำแหน่ง — checkpoint ทุก 100  tiles)
- `hearts == 0` **หรือ** meter overflow → `GAME_OVER` (permanent — GDD V.2 กลับทิศจาก "no permanent game over" เดิม, ดู ADR-010)

**พฤติกรรมในบอส (RunState.BOSS):**
- **ไม่มี fall-respawn** (ไม่มีเหว, ไม่มีทางกลับ RUNNING)
- ตอบผิด (เลือกไอเทมผิด) = `hearts -= 1` ตรง ๆ → `hearts == 0` = GAME_OVER

---

## 4. Boss Wave Progression (ADR-011 context; content ใน `balance/v1/boss.json`)

```
BOSS enter (armor = 3)
   ├─ Wave 1 (Fake News)      → ตอบถูก: armor-=1 / ตอบผิด: hearts-=1
   ├─ Wave 2 (วิกฤตแทรกซ้อน)  → ตอบถูก: armor-=1 / ตอบผิด: hearts-=1
   └─ Wave 3 (ประนีประนอม)    → ตอบถูก: armor-=1 / ตอบผิด: hearts-=1
        │
     armor == 0 ──► VICTORY → FINISHED (world restore → Report Card)
     hearts == 0 ─► GAME_OVER
```

- **Invariant:** ชนะเฉพาะเมื่อ `armor == 0` (ตอบถูกครบ 3); ไม่มี timeout kill (มีเวลาตัดสินใจ/เวฟ แต่ตอบผิด ≠ แพ้ทันที เว้นแต่หัวใจหมด)
- decision 11–13 (3 เวฟ) log เป็น `BossPhaseEvent` → ใช้คำนวณ Cognitive Score + edge ใน DAG
