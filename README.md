# 🐧 PENGUIN DASH

**Penguin Dash** เป็นเกมแนว Endless Runner แนว Isometric Grid (เส้นทางแบบ zigzag ซ้าย-ขวา) พัฒนาด้วย Kivy (Python) เป้าหมายของเกมคือการวิ่งให้ได้ระยะทางไกลที่สุดก่อนตาย โดยผู้เล่นจะต้องควบคุมนกเพนกวินให้วิ่งไปข้างหน้าและเลี้ยวตามทาง พังสิ่งกีดขวาง (Obstacles) เพื่อเปิดทาง และหนีบล็อกด้านหลังที่ร่วงหล่นตามมา

---

## ✨ Features (ฟีเจอร์หลักของเกม)

- **Endless Isometric Grid:** วิ่งทำคะแนนบนเส้นทางที่ถูกสร้างขึ้นแบบสุ่ม (Procedural Generation) ในมุมมอง 2.5D Isometric
- **Dynamic Obstacles:** หลบหลีกและทำลายสิ่งกีดขวางที่ขวางหน้าเพื่อเปิดทาง
- **Progressive Difficulty:** ระดับความยากและความเร็วจะเพิ่มขึ้นอย่างต่อเนื่องตามระยะทาง
- **Shop & Skins:** ระบบร้านค้าสำหรับสะสมและเปลี่ยนสกินตัวละครเพนกวิน
- **Leaderboard System:** ระบบบันทึกสถิติและคะแนนสูงสุดของผู้เล่นแบบ Local Database

## ⚙️ Core Functions (ระบบการทำงานเบื้องหลัง)

- **Object Pooling System:** ระบบนำบล็อกที่หลุดออกจากจอแล้วกลับมาเวียนใช้ใหม่ ช่วยลดการบริโภคหน่วยความจำ (Memory Optimization)
- **State Management:** ระบบแยกสถานะหน้าจอ (Menu, Gameplay, Pause, Game Over) อย่างชัดเจนด้วย Clean OOP Pattern
- **Grid Collision & Physics:** ระบบคำนวณพิกัดจากการเรนเดอร์ Isometric ผสานกับการตรวจจับการพุ่งชนขอบทาง (Edge Falling) และสิ่งกีดขวาง
- **SQLite Database:** ระบบจัดการข้อมูลผู้เล่นผ่าน Query ช่วยบันทึกประวัติได้อย่างมีประสิทธิภาพ

---

## 👥 Members

ผู้พัฒนาโปรเจกต์ (Contributors):

1. **6810110162**
2. **6810110402**

## 🛠 Tech Stack

- **Language:** Python 3.10+
- **Framework:** Kivy
- **Database:** SQLite (สำหรับเก็บ Local Leaderboard และ Session History)
- **Deployment:** Buildozer

## 📁 Project Structure (Clean OOP Architecture)

```text
penguin_dash/
├── assets/                  # รูปภาพ (Sprite/Atlas) และเสียงดนตรี (BGM/SFX)
│
├── core/                    # แกนหลักของโปรเจกต์
│   ├── config.py            # ตั้งค่าตัวแปรในเกม (ความเร็ว, ขนาด Grid)
│   ├── state.py             # จัดการ State ภาพรวม (เล่น, หยุด, จบเกม)
│   └── database.py          # จัดการ SQLite Database (ตารางคะแนน, ประวัติ)
│
├── game/                    # ลอจิกและวัตถุ (Entities & Systems) ในหน้าจอเล่น
│   ├── entity.py            # Base Class สำหรับทุกวัตถุ (พิกัด x, y)
│   ├── penguin.py           # ตัวละครนกเพนกวิน (สืบทอด Entity)
│   ├── blocks.py            # บล็อกขวางทาง (Obstacle) และพื้นร่วง (Platform)
│   ├── grid.py              # คำนวณการเดินแบบซิกแซก และตรวจจับการตกขอบ
│   └── pool.py              # ระบบนำบล็อกที่ใช้แล้วกลับมาวางใหม่ (Object Pooling)
│
├── screens/                 # หน้าจอ UI ต่างๆ ของแอป (Views)
│   ├── menu.py              # หน้า Menu หลัก เริ่มเกม
│   ├── gameplay.py          # หน้าจอตอนกำลังวิ่ง
│   ├── gameover.py          # หน้าจบเกม (ให้พิมพ์ชื่อ)
│   ├── history.py           # หน้าตารางคะแนน (Leaderboard)
│   ├── pause.py             # หน้าหยุดเกมชั่วคราว
│   └── shop.py              # หน้าร้านค้าซื้อ Skin นกเพนกวิน
│
├── ui/                      # ชิ้นส่วน UI เล็กๆ ที่ใช้ซ้ำในหลายๆ หน้าจอ
│   └── components.py        # เช่น ปุ่มกด, แถบคะแนน, Pop-up
│
├── main.py                  # Entry point จุดเริ่มต้นรัน Kivy App
└── style.kv                 # ไฟล์ จัดหน้าตา Kivy (แยก Design ออกจาก Code)
```

## 🔄 Git Workflow & Commit Guide

เพื่อให้การทำงานร่วมกันเป็นไปอย่างราบรื่น เราจะใช้รูปแบบ **Git Flow** ขั้นพื้นฐาน และรูปแบบ **Conventional Commits**:

### การสลับ Branch

มี Branch หลัก 2 เส้น:

1. `main` : ใช้เก็บโค้ดตัวเต็มที่ **พร้อมใช้งานแบบสมบูรณ์** (Production-ready)
2. `develop` : ใช้เก็บโค้ดที่ **กำลังพัฒนาและประกอบรวมร่าง** (Integration branch)

**การสร้างฟีเจอร์ใหม่ ให้แยกสาขา (Branch) ออกจาก `develop` ชั่วคราว:**

> สมมติว่าต้องการทำหน้า Menu Screen

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

### รูปแบบการเขียน Commit Message (แบบมืออาชีพ)

กรุณาเขียนคำนำหน้า Commit เพื่อบอกด้วยว่างานใน Commit นี้กำลังทำอะไร:

- `feat:` ฟีเจอร์ใหม่ - เช่น `feat: add local database schema`
- `fix:` แก้บั๊ก/ปัญหา - เช่น `fix: penguin falling exact tile condition`
- `refactor:` ปรับปรุงโครงสร้างโค้ดเดิม - เช่น `refactor: move grid math to separate class`
- `docs:` แก้ไขเอกสาร (เช่น README, Doc.md) - เช่น `docs: update project structure`
- `style:` จัดระเบียบหน้าตาโค้ด (เช่น เคาะบรรทัด, ลบ whitespace)
- `test:` เพิ่มหรือแก้ไข Unit Test

> **ตัวอย่าง:** `git commit -m "feat: add obstacle object pooling system"`
