# Windows Release Runbook — Penguin Dash 0.1

> ขั้นตอนปฏิบัติของ RC/GA; สถานะจริงต้องบันทึกใน `GAME_FIRST_PLAN.md` เท่านั้น

## ก่อน cut release branch

```bash
ruff check .
ruff format --check .
mypy
pytest -q
python -m scripts.validate_resources
python main.py --self-test
```

P0/P1 feature ต้องครบก่อนสร้าง `release/0.1`. หลัง cut รับเฉพาะ bugfix ผ่าน reviewed PR

## Windows build

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m scripts.generate_build_info
.venv\Scripts\python -m scripts.validate_resources --release
.venv\Scripts\pyinstaller --noconfirm --clean PenguinDash.spec
Copy-Item README.txt,CHANGELOG.md,KNOWN_ISSUES.md,LICENSES.md,THIRD_PARTY_NOTICES.md,build_info.json dist\PenguinDash\
dist\PenguinDash\PenguinDash.exe --self-test
.venv\Scripts\python -m scripts.verify_client_bundle dist\PenguinDash
Compress-Archive dist\PenguinDash PenguinDash-v0.1.0-windows-x64.zip
Get-FileHash PenguinDash-v0.1.0-windows-x64.zip -Algorithm SHA256
```

GitHub workflow `Windows Release Candidate` ทำขั้นตอนเดียวกันและ upload ZIP/checksum. Tag build เปิด
release license gate อัตโนมัติ

## RC verification record

บันทึกใน STATUS: tag, Git SHA, artifact SHA-256, tester, Windows version, GPU, PR และวันที่

Manual gates:

1. แตก ZIP ใน clean Windows 10/11 x64 ที่ไม่มี Python
2. รัน `--self-test` แล้วต้อง exit 0
3. เล่นแพ้หนึ่งรอบ, save, ปิด–เปิด, ตรวจ history/gems
4. เล่นชนะ boss หนึ่งรอบ, ตรวจ Report และ history
5. ทดสอบ corrupted DB recovery จากสำเนาข้อมูล ไม่ใช้ข้อมูลผู้เล่นจริง
6. เล่นต่อเนื่อง 10 นาที เก็บ p95/99% frame budget และตรวจ junction/respawn/boss
7. ตรวจภาพ 1280×720 และ 1920×1080 ตาม `UI_UX_HANDOFF.md`
8. ตรวจ ZIP ว่าไม่มี server, Docker, `.env`, DB dev, report/cache หรือ absolute path

## RC/GA rule

- RC1 ใช้ discovery; RC2 รวมเฉพาะ fixes ที่ review แล้ว
- Fix หลัง RC2 ต้องเป็น RC3
- GA เมื่อ automated/manual/security/license gates ผ่านและไม่มี P0/P1 bug
- Merge GA กลับ main, tag `v0.1.0`, publish ZIP + checksum แล้วลบ release branch
