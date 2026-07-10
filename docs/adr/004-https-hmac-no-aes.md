# ADR-004: HTTPS + HMAC โดยไม่ใช้ AES-256

## Context

PDF ต้นฉบับระบุ pipeline: สร้าง HMAC-SHA256 signature → เข้ารหัส AES-256 → ส่งผ่าน REST API → server ตรวจ signature → เก็บ DB คำถามที่ reviewer จะถามคือ: ถ้าส่งผ่าน HTTPS อยู่แล้ว (ซึ่งเข้ารหัส transport layer ทั้งเส้นทาง) การเข้ารหัส AES-256 ซ้ำอีกชั้นที่ payload มีประโยชน์อะไรเพิ่ม — ถ้าตอบแค่ "PDF บอกให้ทำ" ไม่ใช่คำตอบทางวิศวกรรมที่หนักแน่นพอ

## Decision

ใช้ **HTTPS (encrypt-in-transit) + HMAC-SHA256 (integrity/authenticity)** โดยไม่เพิ่ม AES-256 อีกชั้น:

- HTTPS จัดการการเข้ารหัสระหว่างทางอยู่แล้ว — ป้องกัน eavesdropping
- HMAC เซ็นบน `timestamp + nonce + payload` (ไม่ใช่ payload เปล่า ๆ) — server เก็บ nonce ที่เคยเห็นและปฏิเสธ nonce ซ้ำ/timestamp เก่าเกินไป เพื่อป้องกัน **replay attack** (จุดที่ HMAC เปล่า ๆ ป้องกันไม่ได้)
- ไม่ทำ AES-256 เพิ่ม เพราะไม่ได้ป้องกันภัยคุกคามเพิ่มเติมใด ๆ ที่ HTTPS ยังไม่ครอบคลุมอยู่แล้ว ในสถาปัตยกรรมนี้ (client → server เดียว ไม่มี intermediate storage ที่ไม่เข้ารหัส)

## Consequences

- ได้: ลดความซับซ้อนของ client/server (ไม่ต้อง manage key เข้ารหัส/ถอดรหัส payload เพิ่ม), ตอบคำถาม security ของกรรมการได้ตรงประเด็นแทนที่จะอ้างอิงเอกสารเฉย ๆ, ยังคง integrity + authenticity + replay protection ครบ
- เสีย: ถ้าในอนาคตมี attack surface ใหม่ (เช่น ข้อมูลถูกเก็บที่ intermediate proxy โดยไม่เข้ารหัส) จะต้อง revisit
- Revisit เมื่อไหร่: ถ้า deployment model เปลี่ยนเป็นมี third-party relay ที่ไม่ใช่ HTTPS end-to-end
