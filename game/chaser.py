import math

class ChaserBlock:
    """
    บล็อกไล่ตาม (Chaser) ที่เคลื่อนที่ตามเส้นทางมาหาผู้เล่นอัตโนมัติ
    - เริ่ม spawn หลังจากผู้เล่นวิ่งไปแล้ว ACTIVATE_AFTER ก้าว
    - ยิ่งวิ่งไกลยิ่งเร็ว — ถ้าตามทันผู้เล่นก็แพ้
    """
    ACTIVATE_AFTER = 10   # ผู้เล่นต้องวิ่งถึง path_index นี้ก่อนถึง spawn
    START_GAP      = 4    # จุดเริ่มต้นห่างจากผู้เล่น (tiles)

    def __init__(self):
        self.path_index      = 0
        self.col             = 0
        self.row             = 0
        self.active          = False
        self.move_timer      = 0.0
        self.pulse_timer     = 0.0
        self._boost_factor   = 1.0   # multiplier ความเร็ว (>1 = เร็วขึ้น)
        self._boost_steps    = 0     # จำนวนก้าวที่ยังมี boost อยู่

    def activate(self, path_index, path):
        self.path_index = max(0, path_index)
        self.active     = True
        self.move_timer = 0.0
        if self.path_index < len(path):
            self.col, self.row = path[self.path_index]

    def reset(self):
        self.path_index      = 0
        self.col             = 0
        self.row             = 0
        self.active          = False
        self.move_timer      = 0.0
        self.pulse_timer     = 0.0
        self._boost_factor   = 1.0
        self._boost_steps    = 0

    def apply_speed_boost(self, factor: float = 1.1, steps: int = 30):
        """เพิ่มความเร็ว Chaser ชั่วคราว (penalty เมื่อตอบ Quiz ผิด)"""
        self._boost_factor = factor
        self._boost_steps  = steps

    def _move_interval(self, distance_m):
        """วินาทีต่อก้าว — เร่งเร็วต่อเนื่อง (เร็วสูงสุด 0.28 วินาที/ก้าว)"""
        return max(0.28, 0.80 - distance_m * 0.0013)

    def update(self, dt, player_path_index, distance_m, path):
        """อัปเดต chaser ทุกเฟรม — คืน True ถ้าตามทันผู้เล่น"""
        if not self.active:
            return False

        self.pulse_timer += dt
        self.move_timer  += dt

        effective_interval = self._move_interval(distance_m)
        if self._boost_steps > 0:
            effective_interval /= self._boost_factor
            self._boost_steps -= 1
        else:
            self._boost_factor = 1.0

        if self.move_timer >= effective_interval:
            self.move_timer = 0.0
            self.path_index += 1
            if self.path_index < len(path):
                self.col, self.row = path[self.path_index]

        return self.path_index >= player_path_index

    def pulse_alpha(self):
        """ค่า Alpha ที่เต้นเป็น pulse เพื่อใช้ตอนวาด"""
        return 0.55 + 0.35 * math.sin(self.pulse_timer * 4.0)

    def gap_to_player(self, player_path_index):
        """จำนวนก้าวที่ห่างจากผู้เล่น"""
        return player_path_index - self.path_index
