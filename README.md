# � PENGUIN DASH - Kivy Project Assignment

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

## วิธีการรันโปรแกรม (How to Run)

1. **เตรียม Environment:**
   ```bash
   pip install kivy[base] ffpyplayer
   ```
2. **เริ่มเกม:**
   ```bash
   python main.py
   ```
