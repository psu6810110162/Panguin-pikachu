# ADR-016: Gameplay application boundary และ immutable ViewState

**Status:** Accepted — transitional migration

## Context

`screens/gameplay.py` เคยรวม input, simulation, RunRecord mutation, rendering, navigation และ
UI ไว้ใน object เดียว ทำให้แก้ gameplay กับ UI ขนานกันยาก และทดสอบ state transition โดยไม่เปิด
Kivy ไม่ได้อย่างมั่นใจ

## Decision

ใช้ `GameplayController` เป็น mutation boundary ของ live gameplay และให้ `GameSession` เป็น
writer เดียวของ RunRecord/event log. การย้ายทำแบบ incremental: screen ยังเป็นเจ้าของ grid,
player และ presentation state แต่จะเข้าถึง session, metrics, interaction และ inventory ผ่าน
read-only forwarding properties และเรียก command surface ของ controller สำหรับการเปลี่ยน domain
(choice, death/respawn, collect, checkpoint, boss และ terminal result). `GameplayViewState` เป็น
snapshot แบบ immutable สำหรับ HUD/overlay; จนกว่างาน migration จะจบ ห้ามอ้างว่า screen เป็น
pure presentation layer.

Core/controller ต้องไม่มี Kivy, persistence หรือ server dependency และใช้ port เมื่อต้องส่ง
completed result ออกไปยัง local repository

Interface จะ freeze 80% หลังประกาศ draft และ hard-freeze หลัง controller/UI integration spike ผ่าน;
breaking change หลังจากนั้นต้องบันทึก mini-RFC และได้รับ approval ทั้งสองคน

## Consequences

- Gameplay state replay และ headless tests ทำได้โดยไม่เปิดหน้าต่าง
- UI/UX กับ controller พัฒนาขนานกันโดยยึด snapshot contract เดียว
- มี object allocation ต่อ update cycleเพิ่มขึ้น จึงต้องมี performance budget และ long-run test
- การย้ายจาก screen เดิมต้องทำเป็นช่วง โดยรักษา behavior และ event contract เดิมตลอดการเปลี่ยนผ่าน

## Migration exit criteria

งาน migration ถือว่าเสร็จเมื่อ screen ไม่มีคำสั่งเขียนลง `GameSession`, `RunMetrics`,
`YJunctionInteraction` หรือ `Inventory` โดยตรง, controller มี command สำหรับทุก domain mutation,
และ screenshot/UI regression tests ใช้ `GameplayViewState` เป็น input เดียว. ระหว่างช่วงเปลี่ยนผ่าน
architecture test จะกันการ rebind object เหล่านี้ใน screen และ review ต้องเพิ่ม command ให้ controller
ก่อนเพิ่มการเรียก domain ใหม่.
