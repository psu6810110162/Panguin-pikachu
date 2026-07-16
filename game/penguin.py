class Penguin:
    """
    ผู้เล่น (Player Entity) ไม่มีพลังชีวิต (HP) ตายเมื่อ:
    1. ตกหลุมเดินผิดเลนพ้นตาราง
    2. หลบสิ่งกีดขวางหรือทุบบล็อกอุปสรรคไม่ทัน จนโดนพื้นหล่นใส่ไล่หลังทัน
    """

    def __init__(self, start_col=0, start_row=0):
        self.col = start_col
        self.row = start_row
        self.is_dead = False

        # หันหน้าทางตารางแกนไหน (เช่น +y หมายถึงพุ่งไปข้างหน้า, +x หมายถึงเฉียงขวา)
        self.direction = (0, 1)  # ปกติให้พุ่งตามแกน Row ให้เป็น forward

        # ระบบ Skin
        self.skin = "Ninja Frog"
        self.facing_left = False  # ทิศทางการหัน (False = ขวา, True = ซ้าย)

        # ระบบ Animation & Interpolation
        self.action = "Idle"
        self.action_timer = 0.0
        self.visual_x = None
        self.visual_y = None
        self.anim_offset_y = 0.0

        self.ACTION_FRAMES = {
            "Idle": 11,
            "Run": 12,
            "Jump": 1,
            "Fall": 1,
            "Hit": 7,
            "Double Jump": 6,
            "Wall Jump": 5,
        }

        # Keep the menu's cosmetic selection contract, but no longer resolve
        # it to a third-party sprite folder.  Runtime rendering uses the
        # generated project sheet for every skin until dedicated variants exist.
        self.SKIN_IDS = {"Mask Dude", "Ninja Frog", "Pink Man", "Virtual Guy"}

    def equip_skin(self, skin_id):
        if skin_id in self.SKIN_IDS:
            self.skin = skin_id

    def get_skin_path(self, action=None):
        """Compatibility accessor for callers that still ask for a skin path.

        The old Pixel Adventure path was a runtime dependency and made the
        visual language diverge.  All skins now resolve to the generated sheet;
        frame selection belongs to :meth:`get_generated_frame_name`.
        """
        return "assets/generated/character/penguin_sheet_v2.png"

    def get_generated_frame_name(self):
        """Return the canonical frame name from the generated player sheet.

        ``action`` remains the gameplay-facing vocabulary; the renderer owns
        the sheet and uses this small pure mapping so no Kivy or texture logic
        leaks into the entity.
        """
        if self.is_dead or self.action == "Fall":
            return "fall"
        if self.action == "Hit":
            return "hit"
        if self.action in {"Victory", "Report"}:
            return "victory"
        if self.action == "Respawn":
            return "respawn"
        if self.action == "Jump":
            return "jump"
        if self.action == "Run":
            return "run_left" if self.facing_left else "run_right"
        return "idle"

    def move_forward(self):
        """วิ่งตรงต่อไปข้างหน้า 1 หน่วยบนเส้นทางในเกม"""
        if not self.is_dead:
            self.col += self.direction[0]
            self.row += self.direction[1]

    def turn_left(self):
        """หันเลี้ยวซ้าย 90 องศาเปลี่ยนแกนการเดิน"""
        # คันตรรกะเลี้ยว (0, 1) -> (-1, 0) -> (0, -1) -> (1, 0)
        self.direction = (-self.direction[1], self.direction[0])

    def turn_right(self):
        """หันเลี้ยวขวา 90 องศาเปลี่ยนแกนการเดิน"""
        self.direction = (self.direction[1], -self.direction[0])

    def die(self):
        self.is_dead = True
