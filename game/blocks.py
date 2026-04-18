from core.audio import AudioManager
from core.config import OBSTACLE_ANIM_SPEED

class Obstacle:
    """
    คลาสอุปสรรคหรือบล็อกสิ่งกีดขวาง (Obstacle)
    - มีระดับความสูง (Size) 1-5 ซึ่งจะสะท้อนความยากและจำนวนครั้งที่ต้องทุบ
    - ใช้รูปภาพจากชุด Pixel Adventure (Box2) พร้อมแอนิเมชันท่าทางต่างๆ
    """
    # กำหนดสถานะ (States) ของบล็อก
    STATE_IDLE  = 'Idle'  # สถานะปกติ (วางอยู่เฉยๆ)
    STATE_HIT   = 'Hit'   # สถานะเมื่อโดนทุบ (แสดงแอนิเมชันสั่น)
    STATE_BREAK = 'Break' # สถานะเมื่อพัง (แสดงแอนิเมชันแตกกระจาย)
    
    # จำนวนเฟรมภาพในแต่ละแอนิเมชัน (อิงตามไฟล์ Spritesheet Box2)
    STATE_FRAMES = {
        'Idle': 1,
        'Hit': 4,
        'Break': 4
    }

    def __init__(self, size=1):
        self.col = 0 # พิกัด Column บนตาราง
        self.row = 0 # พิกัด Row บนตาราง
        self.size = size # ระดับความสูง/ความยาก (1-5)
        self.hp = size   # พลังชีวิต (เท่ากับขนาด ถ้าขนาดใหญ่ต้องทุบหลายที)
        self.active = True # สถานะว่ายังแสดงผลอยู่ในเกมหรือไม่
        self.state = self.STATE_IDLE # สถานะเริ่มต้น
        self.anim_frame = 0 # เฟรมแอนิเมชันปัจจุบัน
        self.anim_timer = 0 # ตัวนับเวลาสำหรับเปลี่ยนเฟรม
        self.anim_speed = OBSTACLE_ANIM_SPEED
        
    def reset(self, size=1):
        """ รีเซ็ตค่าเพื่อนำบล็อกเก่าจาก Object Pool กลับมาใช้ใหม่ """
        self.size = size
        self.hp = size
        self.active = True
        self.state = self.STATE_IDLE
        self.anim_frame = 0
        self.anim_timer = 0

    def hit(self):
        """ ฟังก์ชันที่ทำงานเมื่อเพนกวินวิ่งมาทุบโดนบล็อกนี้ """
        if self.state == self.STATE_BREAK:
            return False

        self.hp -= 1  # ลด HP ทีละ 1 (size 5 ต้องทุบ 5 ครั้ง)
        self.anim_frame = 0
        self.anim_timer = 0
        AudioManager().play_sfx('hit')

        if self.hp <= 0:
            self.state = self.STATE_BREAK  # HP หมด → เล่น break animation แล้วค่อย deactivate
        else:
            self.state = self.STATE_HIT    # ยังมี HP เหลือ → สั่น แล้วกลับมา Idle

        return True

    def update(self, dt):
        """ อัปเดตตรรกะและเฟรมแอนิเมชันของบล็อก (ถูกเรียกทุกเฟรมจาก update loop หลัก) """
        if not self.active: return # ถ้าไม่ใช้งานแล้วไม่ต้องทำอะไร

        # ตรวจสอบจำนวนเฟรมสูงสุดของสถานะปัจจุบัน
        max_frames = self.STATE_FRAMES.get(self.state, 1)
        if max_frames > 1:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_frame += 1 # ขยับไปเฟรมถัดไป

                # ตรวจสอบว่าเล่นแอนิเมชันจบครบทุกเฟรมหรือยัง
                if self.anim_frame >= max_frames:
                    if self.state == self.STATE_HIT:
                        # ถ้าท่าสั่นจบ ให้กลับไปท่ายืนนิ่ง
                        self.state = self.STATE_IDLE
                        self.anim_frame = 0
                    elif self.state == self.STATE_BREAK:
                        # ถ้าท่าแตกจบ ให้ปิดการทำงานถาวร (deactivate หลัง animation จบ)
                        self.active = False

    def get_display_blocks(self):
        """ คืนค่าจำนวนบล็อกที่ต้องใช้วาด (เท่ากับระดับของขนาด) """
        return self.size
