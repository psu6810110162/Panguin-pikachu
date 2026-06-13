# 🐧 Penguin Dash — The Great Melt

![CI](https://github.com/psu6810110162/Panguin-pikachu/actions/workflows/ci.yml/badge.svg)

**Penguin Dash** เป็นเกมแนว Endless Runner มุมมอง Isometric พัฒนาด้วย Kivy Framework (Python). ธีม *The Great Melt* พาผู้เล่นออกเดินทางผ่าน 4 ไบโอม (Arctic → Drought → Flood → Wildfire) เพื่อเล่าเรื่องผลกระทบจากภาวะโลกร้อน พร้อมระบบ Quiz เพื่อการเรียนรู้และ Climate Report สรุปข้อมูล

---

## 👥 สมาชิกกลุ่ม

1. **6810110162** — อภิชาติ (Aphichat)
2. **6810110402** — ธีรยุทธ (Teerayut)

---

## 🎮 ฟีเจอร์หลัก

- **Infinite Procedural Terrain** — เส้นทาง zigzag และทางแยก (Diamond Forks) สุ่มแบบ deterministic
- **Biome System** — 4 ไบโอม (Arctic / Drought / Flood / Wildfire) เปลี่ยน background + tile ตามระยะทาง
- **Obstacle & Smashing Mechanics** — เลี้ยวหลบหรือชนกล่องไม้
- **Falling Floors** — พื้นถล่มถ้าหยุดนิ่งนานเกินไป
- **Buff & Trap System** — เก็บ buff เพิ่มพลัง / โดน trap ลดความสามารถ
- **Chaser Event** — ตัวไล่ล่าโผล่เป็นระยะ บีบจังหวะการเล่น
- **Quiz Learning System** — มินิเกมคำถามด้านสิ่งแวดล้อม คั่นระหว่างเกม
- **Climate Report** — หน้าจอสรุปข้อมูลผลกระทบโลกร้อนจากที่ผ่านในรอบ
- **Shop System** — สะสม Gems → ปลดล็อก Skin ใหม่
- **Persistence** — SQLite เก็บ high score, gems, skin ownership
- **i18n** — รองรับไทย/อังกฤษ สลับได้
- **Audio Manager** — เพลง BGM + SFX สลับเปิด/ปิดได้

---

## 🛠 โครงสร้างโค้ด

```
.
├── core/        # config, database, logger, state, audio, i18n
├── game/        # grid, penguin, chaser, biome, buffs, quiz_manager, obstacle_factory
├── screens/     # menu, gameplay, gameover, history, shop, learning_path, quiz_popup
├── ui/          # components (HoverButton, AnimatedSkin), quiz_popup
├── debug/       # screenshot_capture (dev only)
├── assets/      # great_melt/* (tiles, backgrounds, characters, obstacles, gems)
├── scripts/     # report figure/diagram/experiment generators
├── tests/       # pytest: grid logic + smoke imports
└── main.py
```

---

## 🚀 วิธีการรัน

### Setup
```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux  (Windows: venv\Scripts\activate)
pip install -r requirements.txt
```

### เริ่มเกม
```bash
python main.py
```

### Dev capture mode (สำหรับทำรายงาน)
```bash
ENABLE_REPORT_CAPTURE=1 python main.py
```
กด **F12** ระหว่างเล่นเพื่อบันทึก screenshot ลง `assets/report_figures/captures/`

### รัน Tests
```bash
pip install -r requirements-dev.txt
pytest tests/
```

---

## 📊 Technical Requirements Proof

### Widgets (≥ 30)
ใช้ Widget มากกว่า **60 ชิ้น** ครอบคลุม `BoxLayout`, `RelativeLayout`, `GridLayout`, `ScrollView`, `ScreenManager`, `HoverButton`, `ArrowButton`, `TextInput`, `Label`, `Image` และ Canvas instructions จำนวนมากในหน้า Gameplay/Shop

### Callbacks (≥ 10)
- `on_release` ของปุ่มเมนู/นำทาง
- `handle_press/release` ระบบควบคุมการเดิน
- `on_key_down/up` ผูก keyboard
- `Clock.schedule_interval` — game loop 60 FPS
- `Clock.schedule_once` — delay ตอนตาย/เปลี่ยนหน้าจอ
- `on_enter/leave` — reset/load scene
- `bind(on_press=...)` — dynamic list ในหน้า History
- `update_balance_label` — sync DB ↔ UI
- `toggle_sound` — สลับ AudioManager
- `on_text_validate` — รับชื่อผู้เล่น

### Git Persistence
- 140+ commits — ใช้ Conventional Commits scope (feat / fix / chore / refactor / docs / ci / test)
- **Repo:** [github.com/psu6810110162/Panguin-pikachu](https://github.com/psu6810110162/Panguin-pikachu)

---

## 📄 เอกสารเพิ่มเติม
- [SETUP.md](./SETUP.md) — การติดตั้งแบบละเอียด
- [Project_Proposal.md](./Project_Proposal.md) — Proposal โปรเจกต์
