class _BaseBuff:
    """
    Base class สำหรับ buff ทุกประเภท
    - จัดการ active flag + countdown timer
    - Subclass กำหนด DURATION และ logic พิเศษเพิ่มเติม
    """
    DURATION: float = 5.0

    def __init__(self):
        self.active = False
        self.timer  = 0.0

    def activate(self):
        """เปิด buff และตั้ง timer"""
        self.active = True
        self.timer  = self.DURATION

    def update(self, dt):
        """ลด timer ทุก frame — ปิด buff อัตโนมัติเมื่อหมดเวลา"""
        if not self.active:
            return
        self.timer -= dt
        if self.timer <= 0:
            self.active = False
            self.timer  = 0.0


class GoldBuff(_BaseBuff):
    """Gold buff — อมตะ 5 วิ + ทำลาย ice ทันที (= goldTime ใน JS)"""
    DURATION = 5.0


class ReverseBuff(_BaseBuff):
    """Dark buff — สลับทิศทางซ้าย/ขวา 5 วิ"""
    DURATION = 5.0

    def apply(self, direction):
        """คืน direction ที่สลับแล้วถ้า buff active"""
        if self.active:
            return (-direction[0], -direction[1])
        return direction
