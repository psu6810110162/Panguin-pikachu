# Penguin Dash Domain Language

ภาษากลางของเกม Penguin Dash เพื่อให้ gameplay, UI, persistence และระบบห้องเรียนในอนาคตใช้คำเดียวกันโดยไม่ปะปนขอบเขต

## Language

**Game Run**:
การเล่นเกมหนึ่งรอบตั้งแต่เริ่มวิ่งจนเข้าสถานะจบ ไม่ว่าจะชนะหรือแพ้
_Avoid_: Session, Match, Classroom Session

**Run Record**:
บันทึกเหตุการณ์ตามลำดับเวลาของ Game Run ซึ่งเป็นหลักฐานต้นทางสำหรับคำนวณผลใหม่ได้
_Avoid_: Save Game, Score Row

**Run Result**:
ผลลัพธ์ที่คำนวณจาก Run Record และสร้างใหม่ได้เสมอ ไม่ใช่ข้อมูลต้นทาง
_Avoid_: Event Log, Save Data

**Player Profile**:
ข้อมูลถาวรของผู้เล่นบนเครื่อง เช่น ชื่อ เพชร สกิน และประวัติการเล่น
_Avoid_: Player Session, Account

**Save Data**:
ข้อมูลถาวรบนเครื่องที่รวม Player Profile และข้อมูลตั้งค่าที่มีเวอร์ชันสำหรับ migration
_Avoid_: Run Record, Database File

**Classroom Session**:
ห้องออนไลน์ที่ครูสร้างเพื่อรวม Game Run ของผู้เล่นหลายคน เป็นขอบเขต P2 และไม่จำเป็นต่อเกม offline
_Avoid_: Game Run, Local Session

**Submission**:
สำเนา Run Record ที่รอส่งหรือส่งไปยัง Classroom Session โดยไม่เปลี่ยนต้นฉบับบนเครื่อง
_Avoid_: Save Data, Run Result

**View State**:
ภาพนิ่งแบบอ่านอย่างเดียวของสถานะเกม ณ รอบการอัปเดตหนึ่งครั้ง ซึ่ง UI ใช้แสดงผล
_Avoid_: Game State, Mutable Model
