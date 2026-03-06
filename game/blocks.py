class Obstacle:
    """
    บล็อกสิ่งกีดขวาง (Obstacle) มีระดับความสูง Size 1-5
    ทำหน้าที่ขวางทาง หากตัวละครวิ่งชน HP จะลดลง และขนาดจะหดเล็กลงทีละระดับ
    เมื่อ HP=0 หรือ Size=0 จะพังออกไป เปิดทางให้ผู้เล่นเดินได้
    """
    def __init__(self, size=1):
        self.size = size
        self.hp = size  # เริ่มต้น HP เท่ากับขนาดบล็อก
        self.active = True
        
    def reset(self, size=1):
        """ถูกเรียกโดย Object Pool เพื่อนำบล็อกเก่ากลับมาใช้ซ้ำ"""
        self.size = size
        self.hp = size
        self.active = True

    def hit(self):
        """ผู้เล่นวิ่งชน 1 ครั้ง"""
        if self.hp > 0:
            self.hp -= 1
            self.size -= 1
            
            # เมื่อถูกชนจน HP หมด ให้ปิดการทำงาน (เปิดทางผ่าน)
            if self.hp == 0:
                self.active = False
            return True # ยืนยันว่าชนสำเร็จ
        return False
        
    def get_display_blocks(self):
        """จำลองค่าส่งคืนสำหรับการวาดลง Kivy Renderer"""
        # ยิ่ง size เยอะ ก็ยิ่งวาดชิ้นส่วนบล็อกซ้อนทับกันหลายชั้นตามแกน Y
        return self.size
