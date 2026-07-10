# 🐧 PENGUIN DASH - Kivy Project Assignment

**Penguin Dash** เป็นโปรเจกต์เกมแนว Endless Runner พัฒนาด้วย Kivy Framework (Python) สำหรับส่งวิชาการเขียนโปรแกรม โดยเน้นการสร้าง Application ที่มีความสวยงาม ลื่นไหล และมีระบบ Logic ที่ซับซ้อนตามเงื่อนไขที่อาจารย์กำหนด

---

## 👥 สมาชิกกลุ่ม (Team Members)

1. **6810110162** - นายอภิชาติ (Aphichat)
2. **6810110402** - นายธีรยุทธ (Teerayut)

---

## 🎮 ภาพรวมของโปรแกรม (Program Overview)

**Penguin Dash** คือเกมวิ่งไม่จำกัด (Endless Runner) ในมุมมอง Isometric ที่ผู้เล่นต้องใช้ทักษะความไวในการตัดสินใจเลี้ยวซ้าย-ขวาตามเส้นทางที่เปลี่ยนไปตลอดเวลา

### ฟีเจอร์เด่นของเกม:

- **Infinite Terrain Generation:** เส้นทาง zigzag และทางแยก (Forks) ที่สร้างแบบ Procedural ทำให้การเล่นแต่ละครั้งไม่เหมือนกัน
- **Obstacle & Smashing Mechanics:** การตัดสินใจเลี้ยวเพื่อหลบหรือชนทำลายกล่องไม้ที่เป็นอุปสรรค
- **Falling Floors:** ระบบ "พื้นถล่ม" หากผู้เล่นหยุดนิ่งนานเกินไปจะถูกบีบให้ต้องก้าวเดินต่อ
- **Full Shop System:** ระบบสะสม Gems เพื่อปลดล็อก Skin ตัวละครใหม่ๆ และสวมใส่ได้ทันที
- **Persistence Data:** บันทึกประวัติการเล่น คะแนนสูงสุด และของสะสมลงใน Database

---

## 🕹 วิธีเล่น (How to Play)

> เอกสารนี้อธิบาย **เกมที่มีอยู่จริงตอนนี้** ส่วนดีไซน์เป้าหมายเต็มรูปแบบ (checkpoint, policy, boss, quiz — ดู [docs/OVERVIEW.md](docs/OVERVIEW.md)) ยังอยู่ระหว่างพัฒนา (D2–D6) เพื่อไม่ให้เอกสารเพี้ยนไปจากของจริงเมื่อ build

- **ควบคุม:** ปุ่มลูกศร ← → บนคีย์บอร์ด หรือปุ่มลูกศรบนหน้าจอ — เลี้ยวซ้าย/ขวาเท่านั้น เพนกวินวิ่งไปข้างหน้าอัตโนมัติ
- **เก็บเพชร (Gem):** เดินผ่านจะเก็บอัตโนมัติ สะสมไว้ซื้อสกินในร้านค้า
- **ชนกล่องน้ำแข็ง (Obstacle):** ชนแล้วกล่องจะแตกทีละชั้น (ไม่ตายทันที) ชนซ้ำจนกล่องแตกหมดถึงจะผ่านไปได้
- **ตาย:** เดินหลุดออกนอกเส้นทาง, ยืนนิ่งเกิน 2 วินาที (พื้นจะถล่ม), หรือโดนพื้นที่กำลังถล่ม — จบเกมทันที (ยังไม่มีระบบ Respawn ในเวอร์ชันปัจจุบัน)
- **เป้าหมาย:** วิ่งให้ไกลที่สุดและเก็บเพชรให้เยอะที่สุดก่อนตาย แข่งกับสถิติเดิมของตัวเองใน History

## 🛠 คำอธิบายการทำงานของ Code (Technical Logic)

ทีมงานเราแบ่งโครงสร้างโค้ดออกเป็นส่วนๆ (Modular Architecture) เพื่อให้ง่ายต่อการพัฒนาและตรวจสอบ:

1. **Core Generation (`game/grid.py`):**
   - หัวใจหลักคือ `GridManager` ที่ใช้การสุ่มเลือกทิศทางและทำทางแยก (Diamond Forks)
   - ใช้ระบบ Coordinate Mapping เพื่อเปลี่ยน Grid index เป็นพิกัดหน้าจอแบบ Isometric

2. **Game Loop & Rendering (`screens/gameplay.py`):**
   - ใช้ `Clock.schedule_interval` ที่ความถี่ 60 FPS เพื่อคำนวณตำแหน่งและวาดภาพ
   - `KivyRenderer` ทำหน้าที่จัดการ Canvas instructions (Rectangle, Color) เพื่อรีดประสิทธิภาพสูงสุด

3. **Global State (`core/state.py`):**
   - เก็บข้อมูลการเลือก Skin, คะแนนปัจจุบัน และสถานะ Pause โดยใช้ Singleton เพื่อให้ข้อมูลคงที่ตลอดทั้ง Application

4. **Persistence Helper (`core/database.py`):**
   - จัดการ SQLite3 เพื่อเก็บ Gems Balance, บันทึกชื่อผู้เล่น และสถานะการเป็นเจ้าของ Skin

---

## 📊 Technical Requirements Proof (ตรวจสอบเงื่อนไข Assignment)

ครบถ้วนตามเกณฑ์คะแนนที่กำหนด:

### 1. Widgets (อย่างน้อย 30 Widgets)

เรามีการใช้งาน Widget รวมกัน **มากกว่า 60 Widgets** ครอบคลุมทั้ง:

- **Containers:** `BoxLayout`, `RelativeLayout`, `GridLayout`, `ScrollView`, `ScreenManager`
- **Active Widgets:** `HoverButton` (Custom CSS-like styles), `ArrowButton`, `TextInput`, `Label`, `Image`
- **Visuals:** Canvas instructions จำนวนมาก (Rectangle/Line/RoundedRectangle) ในหน้า Gameplay และ Shop

### 2. Callbacks (อย่างน้อย 10 Callbacks)

มีการนำระบบ Callback มาใช้อย่างคุ้มค่า เช่น:

1. `on_release`: สำหรับทุกปุ่มนำทางและปุ่มเมนู
2. `handle_press/release`: ระบบควบคุมการเดินที่ตอบสนองไว
3. `on_key_down/up`: การผูก Event Keyboard กับ Window Direct
4. `Clock.schedule_interval`: ระบบ Game Engine Update
5. `Clock.schedule_once`: ระบบ Delay เมื่อตายหรือเปลี่ยนหน้าจอ
6. `on_enter/leave`: การ Reset ข้อมูลและโหลด Scene
7. `bind(on_press=...)`: การสร้าง List ในหน้า History แบบ Dynamic
8. `update_balance_label`: การสื่อสารข้อมูลระหว่าง Database กับ UI
9. `toggle_sound`: การสลับสถานะ Global AudioManager
10. `on_text_validate`: ระบบรับชื่อผู้เล่นผ่านคีย์บอร์ด

### 3. Git Persistence (Commit Early & Often)

- **จำนวน Commits รวม:** 140+ Commits (เกินเกณฑ์ 50 Commits)

- **Link:** [GitHub Repository](https://github.com/psu6810110162/Panguin-pikachu)

---

## 🚀 How to Use

**System diagram:**

```
Game (Kivy) ──HTTPS/REST──▶ Flask ──SQLAlchemy──▶ SQLite (dev) / PostgreSQL (deploy)
                              │
                     Teacher Dashboard (Socket.IO)
```

### Requirements

- Python 3.12
- Docker + Docker Compose (ถ้าจะรัน backend ผ่าน container)
- `make` (ไม่จำเป็น — เป็นแค่ shortcut, ดูหมายเหตุ Windows ด้านล่าง)

### ตั้งค่าครั้งแรก (5 นาที)

```bash
python3.12 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install --install-hooks -t pre-commit -t pre-push
```

`requirements-dev.txt` ติดตั้ง Kivy/ffpyplayer (`requirements.txt`) + Flask/SQLAlchemy/Flask-SocketIO/psycopg (`server/requirements.txt`) บวกเครื่องมือ dev ทั้งหมด: pytest, ruff, mypy, pre-commit

### รันเกม

```bash
python main.py            # หรือ: ./scripts/run_game.sh  /  make run-game
```

### รัน backend (ไม่ต้องมี Kivy window)

```bash
python -m server           # หรือ: ./scripts/run_server.sh  /  make run-server
# เปิดที่ http://localhost:5000 — ดูหน้า dashboard ที่ /dashboard/<room_code>
```

บน macOS ถ้าเจอ "Address already in use" ที่ port 5000 นั่นคือ AirPlay Receiver ของระบบ (ไม่เกี่ยวกับโค้ดเรา) — ปิดที่ System Settings > General > AirDrop & Handoff หรือตั้ง `PORT=5051 python -m server` แทน

### รัน backend ผ่าน Docker

```bash
cp .env.example .env
docker compose up                        # SQLite ใน container — ไม่ต้องตั้งค่าอะไรเพิ่ม
# หรือ
docker compose --profile postgres up     # ทดลอง path PostgreSQL จริงตาม docs/adr/005-sqlite-dev-postgres-deploy.md
                                          # (ต้อง uncomment DATABASE_URL บรรทัด postgresql+psycopg ใน .env ก่อน)
```

`docker compose down` เพื่อหยุด, `docker compose --profile postgres down -v` เพื่อหยุดพร้อมลบ Postgres volume ทิ้ง — ดู [ADR-008](docs/adr/008-docker-compose-backend.md)

> **ข้อควรรู้ (SQLite ใน Docker):** โหมด SQLite เก็บไฟล์ DB ไว้ในตัว container — ข้อมูลหายเมื่อ container ถูก recreate (`docker compose down` แล้ว `up` ใหม่) เพราะไม่มี volume mount ให้ ถ้าต้องการข้อมูล persist ข้ามรอบ ให้ใช้ profile postgres (มี named volume `postgres-data` อยู่แล้ว)

### Windows (เพื่อนร่วมทีมใช้ Windows, อีกคนใช้ Mac)

`make` ไม่มีมาให้บน Windows โดย default — ใช้ **Git Bash** (ติดมากับ Git for Windows อยู่แล้ว) รัน `.sh` scripts และ `make` ได้ตามปกติ หรือข้าม Make ไปเลยแล้วรันคำสั่ง `python`/`docker compose` ตรง ๆ ด้านบน — ทำงานเหมือนกันทุก OS ไม่มี `.bat` แยกให้ดูแลเพิ่ม

### Make shortcuts (ทางลัด — ดู `Makefile`)

| Command | ทำอะไร |
|---|---|
| `make run-game` / `make run-server` | รันเกม / รัน backend |
| `make docker-up` / `make docker-up-postgres` | รัน backend ผ่าน Docker (SQLite / Postgres) |
| `make test` / `make lint` / `make format` | pytest / ruff+mypy / ruff --fix |
| `make check` | lint + test รวด — เหมือนที่ pre-push hook รัน |
| `make clean` | ลบ `__pycache__`/`.pytest_cache`/`.ruff_cache`/`.mypy_cache` เท่านั้น (ไม่แตะ `instance/` หรือ DB) |

## 🗂 Architecture Map

```
main.py            # entry point — ScreenManager + Builder.load_file("style.kv")
style.kv            # Kivy UI/layout definitions (kv language) ของทุกหน้าจอ

core/               # ระบบกลาง ห้าม import kivy (ยกเว้น audio.py) — server/ import ตรงได้
                    # โดยไม่ต้องติดตั้ง Kivy, มี type hints ครบ, ดู tests/test_no_kivy_in_core.py
  config.py           ค่าคงที่: ขนาดหน้าจอ, grid, ความเร็ว
  state.py            StateManager (screen state) + RunState machine (lifecycle ของการเล่น 1 รอบ)
  schema.py           RunRecord/RunResult — contract กลาง ดู docs/adr/001-runrecord-contract.md
  events.py           GameEvent ที่เป็นไปได้ทั้งหมด (Collect, Respawn, Policy, Mission, Boss, Quiz, ...)
  scoring/             evaluator.py (orchestration), rules.py (rule-based scoring), hake.py (Hake Gain)
  sync.py             HMAC-signed sync client: sign/verify, offline queue, retry/backoff
  database.py         DatabaseManager — SQLite (local game data): player, session, score, owned skins
  audio.py            AudioManager — BGM/SFX ผ่าน Kivy SoundLoader (ข้อยกเว้นเดียวที่ import kivy)
  logger.py           logger กลางของแอป

game/               # gameplay logic (import kivy ได้)
  grid.py             GridManager — สร้างเส้นทาง zigzag/fork แบบ procedural, isometric mapping
  penguin.py          ตัวละครผู้เล่น
  blocks.py           Obstacle (กล่องน้ำแข็งแบบ stack, ถูกชนแล้วแตกทีละชั้น)
  gem.py              ไอเทมสะสม
  pool.py             ObjectPool — reuse obstacle/gem objects กัน GC กระตุก
  obstacle_factory.py สุ่มความยากของ obstacle/gem ตามระยะทาง
  particles.py        เอฟเฟกต์อนุภาค
  entity.py           base class ของ entity ในเกม

screens/            # แต่ละไฟล์ = 1 หน้าจอ (ScreenManager screen)
  menu.py, gameplay.py, gameover.py, history.py, shop.py, pause.py

ui/                 # widget ที่ใช้ซ้ำข้ามหลายหน้าจอ
  components.py       HoverButton, AnimatedSkin ฯลฯ

server/             # Flask backend — import ได้เฉพาะ core/ (ดู server/requirements.txt แยกจากเกม)
  __init__.py          create_app() factory (Flask + SQLAlchemy + Flask-SocketIO)
  __main__.py           bootstrap: `python -m server` — อ่าน config จาก config.py แล้วรัน
  config.py            อ่าน env var (DATABASE_URL/SYNC_SECRET/PORT) จุดเดียว
  models.py            SessionModel/PlayerModel/RunModel (SQLite dev, PostgreSQL deploy)
  services.py          session lifecycle, verify+score+upsert run, leaderboard query
  api.py               REST: create/join/end session, ingest run, leaderboard, healthz
  dashboard.py         Teacher Dashboard (Jinja) + Export CSV + SocketIO room events
  static/               dashboard.css, dashboard.js
  templates/            index.html (create session), dashboard.html
  Dockerfile            image สำหรับ backend เท่านั้น (เกม Kivy containerize ไม่ได้ประโยชน์)
  requirements.txt      Flask/SQLAlchemy/Flask-SocketIO/psycopg — แยกจากเกม

tests/              # pytest — ดู "Testing" ด้านล่าง
scripts/            # run_game.sh, run_server.sh — เรียกตรงหรือผ่าน Makefile ก็ได้
assets/             # sprites, fonts, sounds
docker-compose.yml, .env.example, Makefile   # ดูหัวข้อ "How to Use"
```

## ✅ Testing & Quality Gates

```bash
# รัน test suite ทั้งหมด (KIVY_WINDOW=mock ไม่เปิดหน้าต่างจริง)
env KIVY_NO_ARGS=1 KIVY_WINDOW=mock pytest -v

# lint + format + type check (เหมือนที่ CI รัน)
ruff check .
ruff format --check .
mypy

# รัน quality gate เดียวกับที่ pre-commit จะรันตอน commit/push
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files
```

- **ruff/ruff-format** และ hygiene hooks (trailing whitespace, large files ฯลฯ) รันทุกครั้งที่ `git commit`
- **pytest + mypy** รันทุกครั้งที่ `git push` (pre-push hook) — ช้ากว่าแต่กันโค้ดพังไม่ให้หลุดขึ้น remote
- `core/` ต้องมี type hints ครบ (`mypy` บังคับ `disallow_untyped_defs`) เพราะเป็นเลเยอร์ที่ backend ในอนาคตจะ import ตรง — `game/`/`screens/`/`ui/` ยังไม่บังคับ (Kivy ไม่มี type stubs)
- CI (`.github/workflows/ci.yml`) รัน job เดียวกันทุก push เข้า `main` และทุก PR

## 🤝 Contributing

1. Branch ตั้งชื่อด้วย prefix: `feat/`, `fix/`, `chore/`, `test/`, `docs/`, `ci/` — ห้าม push ตรงเข้า `main`
2. Commit message แบบ [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): message`
3. ก่อนเปิด PR: รัน `pre-commit run --all-files` และ `pre-commit run --hook-stage pre-push --all-files` ให้ผ่านทั้งคู่
4. ทุก PR ต้องมี CI เขียว + อีกคน review (CODEOWNERS auto-request ทั้งสองคน)
5. คำถาม/policy/quiz ข้อมูลเก็บเป็น JSON แยกจาก logic — แก้เนื้อหาไม่ต้องแตะโค้ด
6. เปลี่ยน/เพิ่ม architecture decision (dependency ใหม่, data model, security model) → เขียน ADR ใหม่ก่อน อย่าแก้ ADR เก่าย้อนหลัง — ดู [docs/adr/TEMPLATE.md](docs/adr/TEMPLATE.md) และ "Changing หรือเพิ่ม ADR" ใน [docs/ENGINEERING_PLAN.md](docs/ENGINEERING_PLAN.md)
