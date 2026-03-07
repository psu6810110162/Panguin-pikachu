# 🐧 PENGUIN DASH

**Penguin Dash** เป็นเกมแนว Endless Runner ในมุมมอง Isometric Grid (เส้นทางแบบ zigzag ซ้าย-ขวา) พัฒนาด้วย Kivy (Python)

เป้าหมายของเกมคือการวิ่งไปให้ไกลที่สุดเท่าที่จะทำได้ ผู้เล่นต้องควบคุมนกเพนกวินให้เลี้ยวตามทางให้ทัน พังสิ่งกีดขวาง (Obstacles) ที่ขวางทาง และระวังบล็อกทางเดินด้านหลังที่ค่อยๆ ร่วงหล่นตามมาถล่มตัวเรา!

---

## 👥 Members (สมาชิกกลุ่ม)

ผู้พัฒนาโปรเจกต์ (Contributors):

1. **6810110162** - นายอภิชาติ (Aphichat)
2. **6810110402** - นายธีรยุทธ (Teerayut)

---

## 🛠 Tech Stack

- **Language:** Python 3.10+
- **Framework:** Kivy
- **Database:** SQLite (สำหรับเก็บ Local Leaderboard และ Session History)
- **Deployment:** Buildozer

---

## � How to Run (วิธีการรันโปรแกรม)

### 1. Requirements

- **Python 3.10+**
- **pip** (Python Package Installer)

### 2. Installation (การติดตั้ง)

```bash
# ติดตั้ง dependencies ที่จำเป็น
pip install kivy[base] kivy_examples
# หากต้องการรันระบบเสียง อาจต้องติดตั้งเพิ่มเติม (Optional)
pip install ffpyplayer
```

### 3. Execution (การรัน)

```bash
python main.py
```

---

## 🎮 Gameplay Mechanics (ระบบการเล่น)

- **Controls:** ใช้ปุ่มลูกศร `←` และ `→` บนคีย์บอร์ด หรือกดปุ่มลูกศรบนหน้าจอเพื่อเลี้ยว
- **Obstacles:** บล็อกไม้ที่ขวางทางจะมีความสูง (Size) แตกต่างกัน คุณต้องชนมันตามจำนวนครั้งที่กำหนดเพื่อให้ทางเปิด
- **Gems:** เก็บ Gems ระหว่างทางเพื่อนำไปซื้อ Skins ใหม่ๆ ใน Shop
- **Progressive Difficulty:** ยิ่งวิ่งไกล บล็อกด้านหลังจะร่วงเร็วขึ้นเรื่อยๆ ท้าทายความไวของนิ้วคุณ!

---

## 📊 Technical Requirements Proof (ตรวจสอบเงื่อนไข Assignment)

โปรเจกต์นี้ได้รับการพัฒนาตามเงื่อนไขที่กำหนดไว้อย่างครบถ้วน:

### 1. Widgets (อย่างน้อย 30 Widgets)

เรามีการใช้งาน Widget ในหน้าจอต่างๆ รวมกัน **มากกว่า 55 Widgets** ดังนี้:

- **Layouts:** `BoxLayout`, `RelativeLayout`, `GridLayout`, `AnchorLayout`
- **Buttons:** `HoverButton` (Custom), `ArrowButton` (Custom), `ImageButton`
- **Labels:** สำหรับแสดง Score, Distance, Gem count, และ Headings
- **Inputs:** `TextInput` สำหรับรับชื่อผู้เล่นในหน้า Game Over
- **Others:** `Image`, `Canvas (Rectangle/RoundedRectangle/Line)`, `ScrollView`, `ScreenManager`
- _ตรวจสอบได้ที่ไฟล์ [style.kv](file:///Users/aphchat/Coding%20Year%201/KIVY_Project/Panguin-pikachu/style.kv) และ Python files ในโฟลเดอร์ `screens/`_

### 2. Callbacks (อย่างน้อย 10 Callbacks)

มีการใช้งาน Event Handlers และ Bindings **มากกว่า 17 จุด** เช่น:

- `on_release` ของปุ่ม Menu ต่างๆ (Start, Shop, History, Exit)
- `handle_press` / `handle_release` ของปุ่มลูกศรควบคุม
- `on_key_down` / `on_key_up` สำหรับการควบคุมผ่าน Keyboard
- `Clock.schedule_interval` (Game Loop)
- `Clock.schedule_once` (Delayed Actions)
- `bind(on_press=...)` ในการสร้าง UI Dynamic
- `on_enter` / `on_leave` ของ ScreenManager

### 3. Git Persistence (Commit Early & Commit Often)

- **Total Commits:** 99+ commits
- **Early Commit:** เริ่มต้นตั้งแต่วันที่ 23 กุมภาพันธ์ 2026
- **Contributors:**
  - 6810110162 (Aphichat)
  - 6810110402 (Teerayut)
  - _แต่ละคนมี Commit ไม่ต่ำกว่า 25 ตามเงื่อนไข_

---

## 📁 Project Structure

```text
penguin_dash/
├── assets/                  # Graphics (Sprites/Atlas/Backgrounds) & Audio (BGM/SFX)
├── core/                    # Game Engine Core
│   ├── config.py            # Global variables & Constants
│   ├── state.py             # Global State Manager
│   ├── audio.py             # Sound & Music system
│   └── database.py          # SQLite persistence (Leaderboard/Shop)
├── game/                    # Entities & Logic
│   ├── penguin.py           # Player logic & animation
│   ├── grid.py              # Zigzag math & world generation
│   ├── blocks.py            # Obstacle & Gem entities
│   └── pool.py              # Object recovery system
├── screens/                 # UI Views
│   ├── menu.py, gameplay.py, gameover.py, history.py, shop.py
├── main.py                  # Entry Point
└── style.kv                 # UI Design Definitions
```

---

## 🔄 Git Workflow & Commit Guide

เพื่อให้การทำงานร่วมกันเป็นไปอย่างราบรื่น เราจะใช้รูปแบบ **Git Flow** ขั้นพื้นฐาน และรูปแบบ **Conventional Commits**:

### การสลับ Branch

มี Branch หลัก 2 เส้น:

1. `main` : ใช้เก็บโค้ดตัวเต็มที่ **พร้อมใช้งานแบบสมบูรณ์** (Production-ready)
2. `develop` : ใช้เก็บโค้ดที่ **กำลังพัฒนาและประกอบรวมร่าง** (Integration branch)

**การสร้างฟีเจอร์ใหม่ ให้แยกสาขา (Branch) ออกจาก `develop` ชั่วคราว:**

```bash
# 1. เช็คเอาต์ไปที่ develop และอัปเดตงานให้ล่าสุดเสมอ
git checkout develop
git pull origin develop

# 2. แตกกิ่งใหม่สำหรับการทำฟีเจอร์นั้นๆ
git checkout -b feature/menu-screen

# 3. เมื่อทำเสร็จและทดสอบครบถ้วน
git add .
git commit -m "feat: setup initial menu screen UI"

# 4. รวมร่างกลับไปที่ develop
git checkout develop
git merge feature/menu-screen
git push origin develop
```

### รูปแบบการเขียน Commit Message

- `feat:` ฟีเจอร์ใหม่
- `fix:` แก้บั๊ก/ปัญหา
- `refactor:` ปรับปรุงโครงสร้างโค้ดเดิม
- `docs:` แก้ไขเอกสาร (เช่น README, Doc.md)
- `style:` จัดระเบียบหน้าตาโค้ด
- `test:` เพิ่มหรือแก้ไข Unit Test

---
