from core.config import GEM_ANIM_SPEED

class Gem:
    """
    คลาสไอเทมเพชร (Gems) - รองรับแอนิเมชันหมุนพื้นฐาน 4 เฟรม
    """
    def __init__(self):
        self.col = 0 # ตำแหน่งในตาราง (Column)
        self.row = 0 # ตำแหน่งในตาราง (Row)
        self.active = True # สถานะว่าเพชรยังอยู่หรือไม่ (ถ้าเก็บแล้วจะเป็น False)
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = GEM_ANIM_SPEED
        
    def reset(self):
        """ คืนค่าสถานะเพชรให้กลับมาแสดงผลใหม่ """
        self.active = True
        self.anim_frame = 0
        self.anim_timer = 0

    def update(self, dt):
        """ อัปเดตเฟรมแอนิเมชันให้เพชรดูเหมือนมีการหมุน/ขยับ """
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            # วนเฟรมไปเรื่อยๆ (0, 1, 2, 3)
            self.anim_frame = (self.anim_frame + 1) % 4

    def collect(self):
        """ ถูกเรียกเมื่อผู้เล่นเดินมาเหยียบช่องที่มีเพชร """
        self.active = False # ปิดการแสดงผล
        return 1 # ส่งคืนค่ามูลค่าเพชรที่ได้รับ (1 เม็ด)
