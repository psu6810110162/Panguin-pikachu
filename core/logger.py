import logging
import sys

def setup_logger(name="PenguinDash"):
    """ ฟังก์ชันตั้งค่าพื้นฐานสำหรับระบบ Logger (บันทึกเหตุการณ์) """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # ตั้งระดับความละเอียดที่ DEBUG (เห็นข้อความทั้งหมด)

    # ตรวจสอบเพื่อป้องกันการสร้าง Handler ซ้ำซ้อน (หลีกเลี่ยง Log บรรทัดเดียวพิมพ์หลายครั้ง)
    if not logger.handlers:
        # กำหนดรูปแบบการแสดงผล: เวลา [ระดับความสำคัญ] ชื่อไฟล์สคริปต์: ข้อความแจ้งเตือน
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(module)s: %(message)s', datefmt='%H:%M:%S')

        # กำหนดให้ผลลัพธ์พิมพ์ออกทางจอภาพ (Console/Stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# สร้างตัวแปร Global logger เพื่อให้ไฟล์อื่นๆ import ไปใช้งานได้ทันที
logger = setup_logger()
