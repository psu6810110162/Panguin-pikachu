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

## 🚀 Dev Setup (5 นาที)

```bash
python3.12 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install --install-hooks -t pre-commit -t pre-push
python main.py
```

`requirements-dev.txt` ติดตั้ง Kivy/ffpyplayer (`requirements.txt`) บวกเครื่องมือ dev ทั้งหมด: pytest, ruff, mypy, pre-commit

## 🗂 Architecture Map

```
main.py            # entry point — ScreenManager + Builder.load_file("style.kv")
style.kv            # Kivy UI/layout definitions (kv language) ของทุกหน้าจอ

core/               # ระบบกลาง ไม่ผูกกับหน้าจอใดหน้าจอหนึ่ง — มี type hints ครบ
  config.py           ค่าคงที่: ขนาดหน้าจอ, grid, ความเร็ว
  state.py            StateManager (Singleton) — สถานะเกมภาพรวม (MENU/PLAYING/...)
  database.py         DatabaseManager — SQLite: player, session, score, owned skins
  audio.py            AudioManager — BGM/SFX ผ่าน Kivy SoundLoader
  logger.py           logger กลางของแอป

game/               # gameplay logic
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

tests/              # pytest — ดู "Testing" ด้านล่าง
assets/             # sprites, fonts, sounds
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
