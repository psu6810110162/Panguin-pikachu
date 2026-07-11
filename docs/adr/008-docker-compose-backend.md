# ADR-008: Docker Compose สำหรับ backend — SQLite เป็น default, Postgres เป็น profile

**Status:** Accepted

## Context

[ADR-005](005-sqlite-dev-postgres-deploy.md) ตกลงไว้ว่า dev local ใช้ SQLite, deploy จริงใช้ PostgreSQL ผ่าน SQLAlchemy โดยสลับแค่ connection string — แต่ไม่มีวิธีทดลอง path ของ Postgres จริง ๆ ก่อนถึงวัน deploy เลย ทุกอย่างรันบน SQLite มาตลอดตั้งแต่ D9 กรรมการ/reviewer จะถามได้ว่า "แน่ใจได้ยังไงว่า Postgres path ใช้งานได้จริง" ถ้าไม่มีใครลองรันมันเลยสักครั้ง

## Decision

เพิ่ม containerization ให้ **`server/` เท่านั้น** — เกม Kivy (`game/`, `screens/`, `ui/`, `assets/`) เป็น desktop GUI app ที่ต้องมี display/audio/input จริง ใส่ลง container ไม่ได้ประโยชน์อะไร (ไม่มี X11/display ให้ใช้)

- `server/Dockerfile`: `python:3.12-slim` (ตรงกับ `pyproject.toml`'s `target-version = "py312"` และ dev venv จริง) — single-stage, `COPY . .` + `.dockerignore` (ไม่ COPY ทีละ package เพราะจะลืม package ใหม่ในอนาคต), `HEALTHCHECK` ยิง `GET /healthz` (endpoint เปล่า ไม่แตะ DB — ใช้ร่วมกับ Compose `depends_on` และ Railway health probe ในอนาคตได้)
- `docker-compose.yml`: service `server` (SQLite เป็น default ผ่าน `DATABASE_URL` env) + service `postgres` (`postgres:16.4`, named volume, healthcheck ของตัวเอง) อยู่ใต้ `profiles: ["postgres"]` — `docker compose up` เฉย ๆ ได้ SQLite, `docker compose --profile postgres up` ได้ Postgres จริง โดย `server` มี `depends_on.postgres.condition: service_healthy, required: false` (ไม่ error เวลาไม่ได้เปิด profile postgres, แต่รอ Postgres พร้อมจริงเมื่อเปิด)
- `psycopg[binary]` (psycopg3) เป็น driver, ไม่ใช้ `psycopg2-binary` — SQLAlchemy 2.x รองรับ psycopg3 ดีกว่าและ psycopg2 อยู่ใน maintenance mode แล้ว
- `server/config.py` แยกการอ่าน env var ออกจาก `server/__main__.py` (ซึ่งเป็นแค่ bootstrap) — Docker แค่ set `DATABASE_URL`/`SYNC_SECRET`/`PORT` ผ่าน env ธรรมดา ไม่ต้องแก้โค้ด
- CI เพิ่ม `docker compose build` (build อย่างเดียว ไม่ต้องรัน) กัน Dockerfile พังแบบไม่มีใครรู้จนถึงวัน deploy

### Alternatives considered

- **Podman** แทน Docker — ทีมมี Docker ติดตั้งอยู่แล้วทั้งสองคน ไม่มีเหตุผลให้เปลี่ยน
- **แยก `docker-compose.dev.yml` / `docker-compose.postgres.yml` เป็นคนละไฟล์** — Compose profiles ทำงานเดียวกันได้ในไฟล์เดียว ดูแลง่ายกว่า
- **ไม่ทำ Docker เลย** — แล้ว Postgres path จาก ADR-005 จะไม่มีใครทดลองจนกว่าจะถึงวัน deploy จริง ซึ่งเสี่ยงเกินไป

## Consequences

- ได้: ทดลอง Postgres path ได้จริงก่อน deploy, `docker compose up` เดียวได้ backend พร้อมใช้ทันทีสำหรับใครก็ตามที่ clone repo (ไม่ต้องตั้ง venv), Dockerfile เดียวกันนี้ใช้ deploy ไป Railway ได้ต่อ (Railway build จาก Dockerfile ได้อยู่แล้ว ไม่ขัดกับแผน)
- เสีย: เพิ่ม `psycopg[binary]` เป็น dependency ใหม่ (แม้ SQLite เป็น default ก็ยังต้องติดตั้งไว้เผื่อสลับ profile) — ยอมรับได้เพราะเป็น dependency เดียวและไม่กระทบ path SQLite ที่ใช้งานจริงตอนนี้
- Revisit เมื่อไหร่: ถ้า deploy จริงบน Railway แล้วต้องการ production-grade WSGI (gunicorn) แทน Werkzeug dev server ที่ใช้อยู่ตอนนี้ (ดู [ADR-007](007-flask-socketio-realtime.md)) — ยังไม่ทำตอนนี้เพราะเกินขอบเขตของเดโม
