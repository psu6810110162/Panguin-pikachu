class Gem:
    """
    ไอเทมเพชรสำหรับเก็บสะสม - รองรับแอนิเมชัน 4 เฟรม
    """
    def __init__(self):
        self.col = 0
        self.row = 0
        self.active = True
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.15 # วินาทีต่อเฟรม
        
    def reset(self):
        self.active = True
        self.anim_frame = 0
        self.anim_timer = 0

    def update(self, dt):
        """วนลูปแอนิเมชัน 4 เฟรม"""
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def collect(self):
        self.active = False
        return 1 # มูลค่า 1 Gem
