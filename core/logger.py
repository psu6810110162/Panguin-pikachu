import logging
import sys

# สร้างระบบ Logger เพื่อใช้ดูสถานะและ Debug ภายในเกม
def setup_logger(name="PenguinDash"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # ไม่ให้ log ซ้ำซ้อนถ้ามีการเรียก setup ซ้ำ
    if not logger.handlers:
        # กำหนดรูปแบบการแสดงผล: เวลา [ระดับ] ชื่อสคริปต์: ข้อความ
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(module)s: %(message)s', datefmt='%H:%M:%S')

        # พิมพ์ออกหน้าจอคอนโซล
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# สร้าง Global logger ไว้เรียกใช้งาน
logger = setup_logger()
