import math

class ChaserBlock:
    """
    บล็อกไล่ตาม (Chaser) ที่เคลื่อนที่ตามเส้นทางมาหาผู้เล่นอัตโนมัติ
    - เริ่ม spawn หลังจากผู้เล่นวิ่งไปแล้ว ACTIVATE_AFTER ก้าว
    - ยิ่งวิ่งไกลยิ่งเร็ว — ถ้าตามทันผู้เล่นก็แพ้
    """
    ACTIVATE_AFTER = 10   # ผู้เล่นต้องวิ่งถึง path_index นี้ก่อนถึง spawn
    START_GAP      = 8    # จุดเริ่มต้นห่างจากผู้เล่น (tiles)

    def __init__(self):
        self.path_index  = 0
        self.col         = 0
        self.row         = 0
        self.active      = False
        self.move_timer  = 0.0
        self.pulse_timer = 0.0

    def activate(self, path_index, path):
        self.path_index = max(0, path_index)
        self.active     = True
        self.move_timer = 0.0
        if self.path_index < len(path):
            self.col, self.row = path[self.path_index]

    def reset(self):
        self.path_index  = 0
        self.col         = 0
        self.row         = 0
        self.active      = False
        self.move_timer  = 0.0
        self.pulse_timer = 0.0

    def _move_interval(self, distance_m):
        """วินาทีต่อก้าว — ยิ่งไกลยิ่งเร็ว (เร็วสูงสุด 0.40 วินาที/ก้าว)"""
        return max(0.40, 1.6 - distance_m * 0.005)

    def update(self, dt, player_path_index, distance_m, path):
        """อัปเดต chaser ทุกเฟรม — คืน True ถ้าตามทันผู้เล่น"""
        if not self.active:
            return False

        self.pulse_timer += dt
        self.move_timer  += dt

        if self.move_timer >= self._move_interval(distance_m):
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
