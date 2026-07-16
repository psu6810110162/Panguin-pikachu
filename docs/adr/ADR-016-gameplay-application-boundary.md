# ADR-016: Gameplay application boundary และ immutable ViewState

**Status:** Accepted

## Context

`screens/gameplay.py` เคยรวม input, simulation, RunRecord mutation, rendering, navigation และ
UI ไว้ใน object เดียว ทำให้แก้ gameplay กับ UI ขนานกันยาก และทดสอบ state transition โดยไม่เปิด
Kivy ไม่ได้อย่างมั่นใจ

## Decision

ใช้ `GameplayController` เป็น mutation boundary ของ live gameplay และให้ `GameSession` เป็น
writer เดียวของ RunRecord/event log. Controller สร้าง `GameplayViewState` แบบ immutable ใหม่ให้
Kivy screen, renderer, HUD และ overlay อ่านเท่านั้น; presentation layer ห้ามถือหรือแก้ mutable
domain objects โดยตรง. Core/controller ต้องไม่มี Kivy, persistence หรือ server dependency และใช้
port เมื่อต้องส่ง completed result ออกไปยัง local repository

Interface จะ freeze 80% หลังประกาศ draft และ hard-freeze หลัง controller/UI integration spike ผ่าน;
breaking change หลังจากนั้นต้องบันทึก mini-RFC และได้รับ approval ทั้งสองคน

## Consequences

- Gameplay state replay และ headless tests ทำได้โดยไม่เปิดหน้าต่าง
- UI/UX กับ controller พัฒนาขนานกันโดยยึด snapshot contract เดียว
- มี object allocation ต่อ update cycleเพิ่มขึ้น จึงต้องมี performance budget และ long-run test
- การย้ายจาก screen เดิมต้องทำเป็นช่วง โดยรักษา behavior และ event contract เดิมตลอดการเปลี่ยนผ่าน
