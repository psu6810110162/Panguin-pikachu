# ADR-013: Ownership boundary สำหรับ Y-Junction gameplay integration (#46)

**Status:** Accepted (extends [ADR-001](001-runrecord-contract.md), [ADR-011](011-learning-evaluation-pipeline.md), [ADR-012](012-runresult-contract.md))

## Context

`core/interaction.py::YJunctionInteraction`, `core/spawning.py::SpawningSystem`, `core/items.py::Inventory` และ `core/state.py::RunMetrics` เขียนเสร็จและมีเทสต์ครบ (module-level) แต่ **ยังไม่ถูกเรียกจาก `screens/gameplay.py`** — เกมจริงยังไม่สร้าง `PolicyChoiceEvent` สักตัว (#46)

งานนี้ไม่ใช่แค่ "ต่อสาย" — มันข้าม 4 เลเยอร์ (`game/grid.py` topology → `screens/gameplay.py` input/render → `core/interaction.py` semantic → `core/session.py` persistence) ถ้าไม่กำหนด owner ของแต่ละก้อนข้อมูลไว้ก่อน จะเกิด double ownership เช่น `Gameplay` แคช junction ปัจจุบันเองพร้อมกับที่ `Grid` ก็รู้ตำแหน่งอยู่แล้ว — สอง source of truth ที่ drift ได้

คำถามที่สองที่ต้องตอบ: `PolicyChoiceEvent.policy_id` (canonical form `zone{N}-{side}`, [ADR ที่เกี่ยวข้อง: `tests/test_policy_id_contract.py`]) ผูกความหมาย (`systemic`) กับ `balance/v1/junctions.json` เวอร์ชันปัจจุบันเสมอ (`core/junction_data.py::BALANCE_DIR` hardcode `v1`) ทั้งที่ `RunRecord.balance_version` มีอยู่แล้วแต่ไม่เคยถูกอ่าน — ถ้ามี `balance/v2/junctions.json` ในอนาคตที่สลับว่าฝั่งไหน `systemic`, run เก่าจะถูก re-score ด้วยความหมายใหม่ ขัด determinism (ADR-012)

## Decision

### 1. Layer ownership (ตรึงไว้ กัน double ownership)

| Layer | เป็นเจ้าของ (owns) | ต้องไม่รู้ (must not know) |
|---|---|---|
| `Grid` (`game/grid.py`) | topology — fork ซ้าย/ขวาอยู่ tile ไหน, zone ปัจจุบัน | policy semantics, scoring |
| `Gameplay` (`screens/gameplay.py`) | rendering + input — ผู้เล่นเลี้ยวทางไหน | systemic flag, policy_id format |
| `YJunctionInteraction` (`core/interaction.py`) | semantic decision — side → junction choice → event | Kivy, rendering |
| `GameSession` (`core/session.py`) | persistence — append `PolicyChoiceEvent` ลง `RunRecord` | UI, grid internals |

`Gameplay` ส่งแค่ `zone` (จาก `Grid`) + `side` (จาก input) ให้ `YJunctionInteraction.handle_choice()` — **ห้ามคำนวณ policy/systemic เอง**. `YJunctionInteraction` เป็นที่เดียวที่ resolve semantic ผ่าน `junctions.json`

### 2. Invariant เชิงโค้ด — ห้าม hardcode semantic ใน gameplay layer

ห้ามเขียน `if side == "left": policy_a`. `side` เป็น *input* ล้วน (ไม่ผิดที่จะส่ง `"left"`/`"right"` เป็นพารามิเตอร์) — สิ่งที่ห้ามคือแตกแขนงตาม semantic นอก `junctions.json`. ปัจจุบัน `core/interaction.py` ทำถูกอยู่แล้ว (`handle_choice(junction, side)` แล้ว policy/systemic มาจาก `Junction.option(side)`) — ยืนยันด้วย `tests/test_policy_id_contract.py`

### 3. balance_version — pin ตอน re-score (deferred, ยัง latent)

`RunRecord.balance_version` มีแล้วแต่ **ไม่ถูก consume ที่ไหนใน `core/` เลย**; `core/junction_data.py` โหลด `balance/v1/` ตายตัว ยังไม่ใช่บั๊กที่ trigger ได้จริง (มีแค่ v1) — **ไม่ block #46**. เมื่อมี `balance/v2/` ในอนาคต scoring ต้อง resolve เทียบ `record.balance_version` ไม่ใช่ current (แนวทาง: loader รับ `balance_version` param โหลด `balance/{version}/…`)

### 4. Data Flow

```
Player → Gameplay(input) → Interaction(side→junction) → PolicyChoiceEvent
      → RunRecord(GameSession) → [sync HMAC] → Server(evaluate)
      → Stealth/DAG → Leaderboard + CSV + Report Card
```

### 5. System Invariants

1. ทุก policy decision → `PolicyChoiceEvent` พอดี 1 ตัว (ไม่ซ้ำ/ไม่หาย)
2. ทุก `PolicyChoiceEvent` ต้องปรากฏใน `RunRecord` (append-only, ADR-001)
3. ทุกคะแนนที่ export (leaderboard/CSV/report) ต้อง originate จาก `RunRecord` — ห้ามมี side-channel
4. re-score record เดิม + `balance_version` เดิม → ผลเดิม 100% (ADR-012)

### 6. Definition of Done สำหรับ #46 (เชิงสถาปัตยกรรม ไม่ใช่แค่ pytest ผ่าน)

```
[ ] Gameplay emit event ครั้งเดียวต่อ 1 decision (ไม่ซ้ำ/ไม่หาย)
[ ] PolicyChoiceEvent persist ลง RunRecord (policy_id canonical)
[ ] Stealth อ่าน → systemic_choice_count ถูก
[ ] DAG อ่าน → edge เปลี่ยนจาก unplayed เป็น correct/incorrect
[ ] Server persist + Leaderboard + CSV สะท้อนค่า (flag เปิด)
[ ] replay/re-score ให้ผลเดิม (balance_version pinned เมื่อจำเป็น — ดูข้อ 3)
```
ใส่ checklist นี้ใน PR description ของ #46 — ไม่ต้องสร้างไฟล์ tracking แยก

## Consequences

- ได้: ownership ชัดกันโค้ดพัน — `Gameplay` แก้ rendering ได้โดยไม่แตะ semantic, `Interaction` แก้กติกาได้โดยไม่แตะ Kivy; seam ระหว่าง producer/consumer มี invariant ตรึงไว้เป็นลายลักษณ์อักษรก่อนเขียนโค้ดจริง
- เสีย: เพิ่มขั้นตอนอ่าน ADR ก่อนแตะ `screens/gameplay.py` — ยอมรับได้เพราะ #46 เป็น cross-lane work (Dev A + Dev B) ที่เคยพังจากบั๊ก policy_id contract มาแล้วครั้งหนึ่ง (PR #61)
- Revisit เมื่อ: มี `balance/v2/junctions.json` จริง — ต้อง implement ข้อ 3 (pin balance_version) ก่อน merge เวอร์ชันที่สอง ไม่งั้น re-score ของ run เก่าจะผิด
