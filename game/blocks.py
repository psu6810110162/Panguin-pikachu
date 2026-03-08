class Obstacle:
    """
    บล็อกสิ่งกีดขวาง (Obstacle) มีระดับความสูง Size 1-5
    ใช้รูปจาก Pixel Adventure (Box2) พร้อมแอนิเมชัน Idle, Hit, Break
    """
    STATE_IDLE  = 'Idle'
    STATE_HIT   = 'Hit'
    STATE_BREAK = 'Break'
    
    # จำนวนเฟรมในแต่ละ Spritesheet (Box2)
    STATE_FRAMES = {
        'Idle': 1,
        'Hit': 4,
        'Break': 4
    }

    def __init__(self, size=1):
        self.col = 0
        self.row = 0
        self.size = size
        self.hp = size
        self.active = True
        self.state = self.STATE_IDLE
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.1  # วินาทีต่อเฟรม
        
    def reset(self, size=1):
        self.size = size
        self.hp = size
        self.active = True
        self.state = self.STATE_IDLE
        self.anim_frame = 0
        self.anim_timer = 0

    def hit(self):
        """เมื่อถูกเพนกวินชน - ปรับให้พังและหายไปทันที"""
        if self.state != self.STATE_BREAK:
            from core.audio import AudioManager
            self.hp = 0
            self.state = self.STATE_BREAK
            self.active = False # หายไปทันทีตามสั่ง
            self.anim_frame = 0
            self.anim_timer = 0
            AudioManager().play_sfx('hit') # ใช้ lowercase ตาม AudioManager pattern
            return True
        return False

    def update(self, dt):
        """อัปเดตเฟรมแอนิเมชัน"""
        if not self.active: return

        max_frames = self.STATE_FRAMES.get(self.state, 1)
        if max_frames > 1:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_frame += 1
                
                # ถ้าเล่นจบแอนิเมชัน
                if self.anim_frame >= max_frames:
                    if self.state == self.STATE_HIT:
                        # กลับไป Idle
                        self.state = self.STATE_IDLE
                        self.anim_frame = 0
                    elif self.state == self.STATE_BREAK:
                        # พังเสร็จแล้ว ปิดการทำงาน (หายไป)
                        self.active = False
                        self.size = 0

    def get_display_blocks(self):
        return self.size
