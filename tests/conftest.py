import os

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_WINDOW", "mock")
os.environ.setdefault("KIVY_LOG_MODE", "PYTHON")

# test suite รันในบริบท dev เสมอ — ถ้าไม่ตั้ง load_config() จะ refuse default
# SYNC_SECRET (guard สำหรับ deploy/ngrok — ดู server/config.py) ตัว guard เอง
# มี test เฉพาะที่ delenv ค่านี้ก่อนทดสอบอยู่แล้ว (tests/test_server_config.py)
os.environ.setdefault("FLASK_DEBUG", "1")
