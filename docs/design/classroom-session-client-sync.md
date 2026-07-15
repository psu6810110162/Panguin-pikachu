# Design Doc: Classroom Session — Kivy Client Join + Offline-Resilient Run Submission

> **สถานะ:** DRAFT (รอ review ก่อนเปิด/แนบ issue) · เขียนโดย Dev B · 2026-07-15
> **เกี่ยวข้องกับ:** #46 (Day-1 Integration, ADR-013), #53 ([D2-B4] Backend Sync Integration), #54 (Final Integration & Demo Freeze)
> **ประเภท:** Integration design spec — ไม่ใช่ ADR (ไม่ได้ตัดสินใจ architecture ใหม่ แค่ "ต่อสาย" client เข้าของเดิม)

> ⚠️ **This document intentionally defines integration *contracts and invariants*, not implementation details.**
> Implementation choices (method names, class layout, screen hierarchy, config mechanism, object-creation
> timing, `ScreenManager` usage, singleton vs lazy) remain owned by Dev A / Dev B — **provided the contracts
> and invariants below are preserved.** รีวิวเอกสารนี้ควรถามว่า "contract พังไหม" ไม่ใช่ "ทำไมไม่ใช้ X".

---

## 0. ทำไมเอกสารนี้ถึงมี (deconfliction)

เอกสารนี้ **ไม่ใช่ issue สาย sync ตัวที่ 4** — มันคือ *spec ที่ #53 ยังไม่มี*. ตอนนี้ #53 body เป็นบรรทัดเดียว
("Send Net Impact Score + rank via core/sync.py to /api/v1/sessions/<code>/runs, fallback local").
เอกสารนี้แตกงานนั้นออกเป็น 2 ส่วนที่ owner ต่างกัน:

| ส่วน | issue ที่ควรรับผิดชอบ | owner |
|---|---|---|
| **A. Sync submission wiring** (เรียก `SyncClient`, enqueue หลัง save, flush เป็นระยะ) | **#53** (spec นี้ = เนื้อของ #53) | Dev B |
| **B. Client join UX** (join screen, กรอก room code, server URL config) | **ยังไม่มี issue** → เสนอเปิดใหม่ / หรือ sub-task ของ #53 | Dev A (screens) |

> **การตัดสินใจที่ต้องขอ:** ส่วน B จะเปิดเป็น issue แยก (Dev A) หรือรวมกับ #53 — ดู §13.

---

## 1. สถานะปัจจุบัน (verified ต่อ `origin/main`)

**Backend พร้อมเต็ม (ใช้ผ่าน browser ได้ครบ):**
- session active ทันทีที่สร้าง — ไม่มี state "not started" ให้ต้องกด "เริ่ม"
- `server/templates/dashboard.html` มีปุ่ม **End Session** + **Export CSV** อยู่แล้ว
- REST endpoint `/api/v1/sessions/<code>/runs` รับผลได้ (อ้างจาก #53)

**Client (Kivy) ไม่แตะระบบ session เลย — 3 ช่องว่าง (grep ยืนยัน):**
1. **ไม่มี join UI** — `git grep 'room_code\|SyncClient\|join'` ใน `screens/*.py` = ไม่เจอเลย
2. **`core/sync.py` เขียนครบ (HMAC + offline queue + retry/backoff, มีเทสต์) แต่ไม่มีใครเรียก** — `git grep 'SyncClient('` เจอแค่ `tests/test_sync.py`. ไม่มี `Clock.schedule_interval` เรียก `flush()`
3. **ไม่มี server URL config** — `core/config.py` ไม่มี `SERVER_URL`/`API_BASE`. นักเรียนยังไม่มีทางรู้ที่อยู่เซิร์ฟเวอร์

**สรุป:** ถ้าเน็ตหลุดตอนนี้ "ไม่มีอะไรเกิดขึ้น" ไม่ใช่เพราะ resilience พัง — แต่เพราะ **ไม่มีอะไรถูกส่งตั้งแต่แรก**

---

## 2. Assumptions

ข้อเสนอทั้งหมดในเอกสารนี้อิงสมมติฐานต่อไปนี้ — ถ้าข้อไหนไม่จริง ต้อง revisit:

- Backend session API ยังคง **backward-compatible** (endpoint/schema ที่ browser ใช้อยู่ไม่เปลี่ยน)
- client 1 เครื่อง เข้าร่วม **ได้มากสุด 1 classroom session ต่อครั้ง**
- **Local SQLite พร้อมใช้เสมอ** เมื่อเล่นจบ (การ save local ไม่มีทางล้มด้วยเหตุ network)
- **Sync เป็น best-effort** — ล้มได้ ช้าได้ และ **ต้องไม่ block gameplay** ไม่ว่ากรณีใด
- ทุก run มี **stable unique `run_id`** ที่ใช้เป็นกุญแจสำหรับ **idempotent submission** ได้
  (assumption นี้เป็นฐานของ exactly-once ใน §4 และ duplicate-enqueue ใน §8)

---

## 3. User journey ที่ต้องการ

นักเรียนเปิดเกม → กรอกโค้ดห้อง (ครูโชว์บนโปรเจกเตอร์) → เล่น → ผลเข้า leaderboard ของห้อง
อัตโนมัติ → **ทนเน็ตไม่ดี** (queue ไว้ retry, ผลไม่หาย)

---

## 4. Goals / Success Criteria (Definition of Done)

Feature นี้ถือว่า **เสร็จ** เมื่อทุกข้อเป็นจริง (reviewer / PM / Dev A ใช้เกณฑ์นี้ปิดงาน):

- ✅ นักเรียน **join classroom session** ได้
- ✅ เล่นจบ 1 รอบ → **enqueue submission ตรง ๆ 1 ครั้ง** (exactly-once ต่อ run, ไม่ซ้ำ)
- ✅ **Server รับ submission ที่ accepted ได้มากสุด 1 ครั้งต่อ run** (แม้ queue จะ retry ก็ตาม — ต้องพูดให้ครบทั้งฝั่ง client และ server)
- ✅ **Local SQLite save สำเร็จเสมอ ไม่ว่า network เป็นยังไง**
- ✅ ถ้า offline ระหว่างเล่นแล้วกลับมา online ภายหลัง → **ผลถูกส่งอัตโนมัติ** (ไม่ต้องกดเอง)
- ✅ **Dashboard leaderboard อัปเดต** หลัง sync สำเร็จ

---

## 5. Invariant ที่ต้องรักษา (ห้ามแตะ)

**ผลการเล่นต้องไม่หายแม้ sync ล้มเหลว.** Local SQLite save (`gameover.py::_save_data`, มีอยู่แล้ว)
ต้องเกิด **ก่อน/อิสระจาก** sync เสมอ. Sync เป็น *additive* — ไม่ใช่ path เดียวที่เก็บผล.

```
เล่นจบ ──► _save_data() [local SQLite]  ◄── source of truth, มีอยู่แล้ว, ห้ามพัง
              │
              └─(additive)─► SyncClient.enqueue(record)  ◄── ของใหม่, ล้มได้ไม่กระทบ local
                                   │
                                   └── flush() เป็นระยะ ──► POST /api/v1/sessions/<code>/runs
```

---

## 6. Ownership

### 6.1 Module ownership (ตาม ADR-013 pattern)

- **`core/sync.py`** (signing, queue, retry): ของเดิม **ไม่ต้องแก้**
- **หน้าจอ/input ใหม่** (join screen, network-status indicator): เขต **Screens = Dev A**

### 6.2 Screen ↔ Sync contract (boundary สำคัญ)

```
Screen เป็นเจ้าของ lifecycle (สร้าง/ถือ/ทิ้ง SyncClient).
SyncClient เปิด capability แค่:
    - รับ run เข้าคิว (enqueue)
    - พยายามส่งคิวที่ค้าง แล้วรายงานว่า run ไหนส่งสำเร็จ (flush)
    - เปิดให้ UI อ่านสถานะการ sync ได้ (read-only observability)

Screen ห้ามยุ่งกับคิวโดยตรง — ต้องผ่าน capability เหล่านี้เท่านั้น.
```
> **Capability, not API shape:** `SyncClient` shall expose **read-only synchronization state to the UI** —
> จะ implement เป็น method, property, observer, callback หรือ event ก็ได้ (เขต Dev A/Dev B).
> spec ล็อกแค่ "UI ต้องมีทางสังเกตสถานะ sync ได้" ไม่ล็อกชื่อ/รูปแบบ.

### 6.3 State ownership (ใครเก็บ data อะไร — กันแย่งกันถือ state)

| Data | Owner |
|---|---|
| `room_code` | Join screen (Dev A) |
| server endpoint / URL | Config (`core/config.py`, ยังไม่มี) |
| offline queue (pending runs) | `SyncClient` (`core/sync.py`) |
| local history (ผลทุก run) | `DatabaseManager` (`core/database.py`) |
| leaderboard | Server (authoritative) |

### 6.4 Lifecycle (ไม่ใช่ implementation — แค่วงจรชีวิต)

```
App start
   └─ Join session (กรอก room_code)
        └─ SyncClient available ────────────────┐
             └─ Gameplay                        │ (available throughout
                  └─ GameOver                   │  joined session)
                       └─ _save_data()  [local, ต้องสำเร็จก่อน]
                            └─ enqueue(record)   │
             ┌───────── background flush() เป็นระยะ ┘
   └─ Leave session → dispose
```

---

## 7. SyncClient availability (contract — ไม่ระบุจังหวะการสร้าง)

> **A `SyncClient` instance must be available *before the first* `enqueue()` operation, and must remain
> available throughout a joined gameplay session.**

เจตนา: spec ล็อกแค่ "มีให้ใช้ตอนไหน" — **ไม่ล็อกว่าสร้างเมื่อไหร่/อย่างไร**. Dev A จะเลือก
create ตอน Join, ตอน Gameplay, lazy-init, หรือ singleton ก็ได้ ตราบใดที่ availability ข้างบนเป็นจริง.

**จุดต่อสาย (Dev B เสนอ, Dev A เดินสายฝั่ง screen):**
- เรียก `enqueue(record)` **หลัง** `_save_data()` ใน `gameover.py`
- `Clock.schedule_interval(flush, N)` เรียก flush เป็นระยะ — **ค่า `N` (flush cadence) เป็น
  implementation detail และตั้งใจปล่อยไม่ระบุ** (ถ้าใส่ตัวเลข จะกลายเป็น contract ทั้งที่ไม่ควรเป็น)

---

## 8. Failure matrix (มีแล้ว vs ยังขาด vs ต้อง verify)

| Failure | Expected behavior | สถานะปัจจุบัน |
|---|---|---|
| **Network unavailable during gameplay** | **Gameplay continues normally; submission is deferred until connectivity is available** (reinforce invariant §5 — gameplay ต้องไม่ผูกกับ network) | ✅ by design (local save อิสระจาก sync) |
| Server down / เน็ตหลุด | queue + backoff | ✅ มีใน `core/sync.py` |
| Timeout | retry (backoff) | ✅ มี |
| Invalid room code | UI error (ไม่เข้า session) | ❌ ต้องทำฝั่ง Join screen |
| Server reject 401/403 (auth ผิด) | **terminal — หยุด retry** | ⚠️ verify: retry policy แยก terminal vs retryable ชัดไหม |
| Server reject 4xx อื่น (bad payload) | terminal vs retryable ตาม policy | ⚠️ verify |
| Duplicate enqueue (run เดิมส่งซ้ำ) | queue ต้อง **idempotent** ต่อ `run_id` | ✅ มี invariant `_pending_run_ids` ใน `sync.py` (verify ครอบ enqueue ซ้ำ) |
| ใครเรียก `flush()` เป็นระยะ | wire ผ่าน `Clock.schedule_interval` | ❌ ยังไม่มี |
| **App ปิดตอน queue ยังไม่ส่ง** | Queued submission survives app restart? | ❌ **ไม่รอด** — คิวเป็น in-memory `deque` (`sync.py:168`); โค้ดเองก็ note ไว้แล้ว (`sync.py:92`) ว่าถ้า restart บ่อยควรเปลี่ยนเป็น store ที่ persist ได้ → ดู Q4 + Risks |
| UI บอก "กำลังส่ง / ส่งไม่สำเร็จ" | via `status()` | ❓ คำถามเปิด (Q3) |

---

## 9. Non-goals (ตั้งใจไม่ทำ)

- ❌ ไม่ redesign dashboard
- ❌ ไม่ redesign gameplay / scoring
- ❌ ไม่ redesign server REST API ที่มีอยู่
- ❌ ไม่เพิ่ม sequence/class diagram, API payload schema, retry algorithm — ทั้งหมดนี้เป็น
  implementation ของ `core/sync.py` ที่มีอยู่แล้ว เอกสารนี้เป็น *integration spec* ไม่ใช่ design ใหม่
- feature นี้แค่ **"ต่อสาย" client เข้าของเดิมที่ backend มีครบแล้ว**

## 10. Out of scope ของ *doc นี้* (ตัดสินใจไม่ได้ตอนนี้)

- ไม่ prescribe หน้าตา UI ของ join screen
- ไม่ตัดสินใจ mechanism ของ server URL config แทน Dev A — แค่ชี้ว่า **ต้องมี**

---

## 11. Open Questions (รวมศูนย์)

| # | คำถาม | Owner |
|---|---|---|
| **Q1** | Classroom join เป็น **mandatory หรือ optional**? (ตอนนี้ 100% local single-player) | Product / Team |
| **Q2** | Server URL / room discovery — ดู **Requirement §11.1** ด้านล่าง (reframe แล้ว) | Dev A / UX |
| **Q3** | ต้องมี **sync status indicator** สำหรับ demo ไหม? | UX / Demo Lead |
| **Q4** | Offline queue restart-resilience — ดู **Requirement §11.2** ด้านล่าง (reframe แล้ว) | Architecture / Dev B |

### 11.1 Requirement: ลดการป้อนข้อมูลด้วยตนเอง (server discovery)

> **Requirement:** ขั้นตอนการเข้าร่วมห้องเรียนควร **ลดการป้อนข้อมูลด้วยตนเองของผู้เล่นให้น้อยที่สุด**
> (นักเรียนไม่ควรต้องพิมพ์ที่อยู่เซิร์ฟเวอร์เองทุกครั้งก่อนเข้าเล่น)

เหตุผล: server URL เป็น *implementation detail* — สิ่งที่เป็น requirement จริงคือ UX ("ลดการพิมพ์").
**Possible approaches (non-binding):** preset configuration · QR code · room-code resolving · preconfigured endpoint

### 11.2 Requirement: restart-resilience ของ submission queue

> **Requirement:** หากระบบต้องรองรับการส่งผลหลังการปิด–เปิดแอป (app-restart resilience) จะต้องมี
> **persistence สำหรับ offline submission queue แยกจาก in-memory queue ปัจจุบัน**
>
> **Open design decision:** กลไก persistence (เช่น SQLite หรือ persistent storage อื่น) เป็นการตัดสินใจ
> ด้าน implementation และ **อยู่นอกขอบเขตของเอกสารนี้**

สถานะปัจจุบัน (verified): queue เป็น in-memory `deque` (`sync.py:168`) → **ไม่รอด restart**; โค้ดเอง note
ไว้แล้ว (`sync.py:92`) ว่าถ้า restart บ่อยควรเปลี่ยนเป็น store ที่ persist ได้.

> **นี่คือเส้นแบ่งที่สำคัญที่สุด** — "ผลไม่หายถ้าเน็ตหลุด" (มีแล้ว) vs "ผลไม่หายถ้าปิดแอป" (ยังไม่มี).
> สำหรับ classroom demo ที่นักเรียนอาจปิดแอปกลางคัน การ *ตัดสินใจว่าต้องการ requirement นี้ไหม* เป็น
> product decision จริง ไม่ใช่ nice-to-have — แม้ *วิธี* implement จะ out of scope ก็ตาม.

---

## 12. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Product decision (Q1 mandatory/optional) ล่าช้า | block การออกแบบ flow | ให้ join เป็น **optional** ไปก่อนจนกว่าจะสรุป — local ยังเล่นได้ปกติ |
| Server URL discovery (Q2) ยังไม่มีคำตอบ | นักเรียน join ไม่ได้เลย | track แยกเป็น Join UX issue, ไม่ block ส่วน A |
| Queue ไม่ persist (Q4) | **data loss** ถ้าปิดแอปตอนออฟไลน์ | invariant §5 คุมไว้แล้ว: local SQLite ไม่หาย → ครู export CSV ชดเชยได้; persistence เป็น follow-up |
| Sync integration (#53) slip | ส่งผลเข้าห้องไม่ได้ทัน demo | Local SQLite ยังทำงานเต็ม → **demo ยังเล่นได้** (sync เป็น additive) |
| Long-running network operations executed on the UI thread (DNS / TLS / timeout ไม่ใช่แค่ตัว request) | gameplay lag / frame ตก | flush ต้องไม่รันบน frame-critical path (Dev A จัดจังหวะ schedule / offload) |

---

## 13. Next step

1. **#53** รับ **ส่วน A** (sync wiring) — เอา §5–§8 ของ doc นี้เป็น spec
2. เปิด issue ใหม่ **หรือ** sub-task ของ #53 สำหรับ **ส่วน B** (join UX, Dev A) — พร้อม §11 เป็นคำถามที่ต้องตอบก่อน
3. **#54 consumes the completed integration work from #53 and the Join UX issue** (demo freeze รอทั้งสองเสร็จก่อน full playthrough)

> **Acceptance / dependency:** **#54 should not start until both A (#53) and B (Join UX) are complete.**
> Sequencing: `A (#53) + B (Join UX)  ──►  #54 (demo freeze)`.
