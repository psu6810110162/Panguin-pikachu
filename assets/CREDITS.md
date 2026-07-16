# Asset Credits

> ไฟล์นี้เพิ่งเริ่มทำ — ยังไม่ครอบคลุมทุก asset ในโปรเจกต์ (งานย้อนหลังตรวจ license asset เดิมยังไม่เสร็จ)
> เพิ่ม entry ใหม่ทุกครั้งที่โหลด asset จากภายนอกเข้ามาใช้จริง

## Fonts

**Noto Sans Thai** — `assets/Component_UI/Font/NotoSansThai-Regular.ttf`
Source: https://github.com/google/fonts/tree/main/ofl/notosansthai
License: SIL Open Font License 1.1 (OFL) — ใช้ได้ฟรีทั้งเชิงพาณิชย์และไม่เชิงพาณิชย์, แก้ไข/embed ได้, ข้อจำกัดหลักคือห้ามขายฟอนต์เดี่ยว ๆ แยกต่างหาก (ใช้ฝังในเกม/แจกพร้อมเกมได้ตามปกติ)
Reason: `Kenney Future.ttf`/`Kenney Future Narrow.ttf` (ฟอนต์หลักของโปรเจกต์) เป็นฟอนต์ Latin-only ไม่มี glyph ภาษาไทย — ข้อความไทยจาก `balance/v1/junctions.json` (situation/label) และ `balance/v1/boss.json` (wall_text) เรนเดอร์ไม่ออกก่อนหน้านี้ ใช้ฟอนต์นี้เฉพาะกับ label ที่มีเนื้อหาไทยเท่านั้น (`junction_banner`, `boss_wall_label`) — UI อื่นที่เป็นภาษาอังกฤษยังใช้ Kenney Future ตามเดิม
