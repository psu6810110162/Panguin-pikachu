# ADR-010: Hearts (5 HP) + Game Over จริง ข้าง Respawn/Checkpoint

**Status:** Accepted (supersedes บางส่วนของ [ADR-002](002-respawn-checkpoint.md))

## Context

[ADR-002](002-respawn-checkpoint.md) ตัดสินใจว่า "ไม่มี permanent Game Over" — ชนแล้วเสีย HP/Heat, HP หมดเข้า Respawn (3s, −10%) เกิดใหม่ที่ checkpoint เพื่อให้ทั้งห้องเรียนเล่นจบ session พร้อมกัน แต่ GDD V.2 ([GAME_DESIGN.md §2.1](../GAME_DESIGN.md)) เพิ่ม **ระบบหัวใจ 5 ดวง** ที่ **ตกเหว = −1 หัวใจ** และ **หัวใจหมด = Game Over จริง** — กลับทิศจาก ADR-002 บางส่วน จึงต้องมี ADR ใหม่ (ห้ามแก้ ADR-002 ย้อนหลัง)

## Decision

- **หัวใจ 5 ดวง** เป็น resource ใหม่ ควบคู่ checkpoint/respawn เดิม (ไม่แทนที่):
  - **ตกเหว** = `hearts -= 1` + respawn ที่ **last checkpoint** (checkpoint ทุก 100 tiles ใน `grid` — reuse ของเดิม)
  - **หลอดแตะ 100** (ADR-009) หรือ **หัวใจ = 0** → **GAME_OVER (permanent)**
  - RESPAWNING มี **invincible frame** ตลอด `respawn_seconds` กัน double-hit
  - เก็บหัวใจเพิ่มได้ระหว่างทาง (pickup logic เดียวกับไอเทม, cap 5)
- state machine เต็มที่ [state-machines.md §3](../state-machines.md); ค่า `respawn_seconds`/`heart_cap` อยู่ `balance/v1/difficulty.json`
- **เหตุผลที่กลับทิศ:** GDD V.2 เปลี่ยนจุดเน้นเป็น **stakes จริง + Stealth Assessment** (ต้องมีความเสี่ยงแพ้เพื่อให้การบริหารหลอด/หัวใจมีความหมาย) — ADR-002 เหมาะกับโหมด "ทั้งห้องต้องจบพร้อมกัน" ซึ่งยังใช้ได้ในโหมด classroom; hearts เหมาะกับโหมด assessment
- **Merge ไม่ใช่ทิ้ง:** `RespawnEvent`/`respawn_count`/checkpoint เดิมยังใช้ครบ (respawn ยังเกิดตอนตกเหวถ้ายังมีหัวใจ) — เพิ่มแค่เงื่อนไข "หัวใจหมด = จบ" ทับบนสุด

## Consequences

- ได้: การตัดสินใจมี stakes จริง (หนุน Stealth Assessment), reuse checkpoint/RespawnEvent เดิมทั้งหมด, ไม่แตะ RunRecord (ใช้ `ObstacleHitEvent.damage` + `RespawnEvent` ที่มีอยู่)
- เสีย: ผู้เล่นอ่อนอาจแพ้ก่อนจบ (ขัดเจตนา ADR-002 เดิม) — บรรเทาด้วยหัวใจเก็บเพิ่มได้ + Visual Scaffolding (GDD §2.2) + balance pass (golden/evil path test)
- Revisit เมื่อ: ถ้าใช้ในห้องเรียนจริงแล้วพบว่ามีคนแพ้แล้วนั่งรอ ให้พิจารณา config toggle ระหว่าง "classroom mode" (ADR-002) กับ "assessment mode" (ADR-010) ผ่าน `difficulty.json`
