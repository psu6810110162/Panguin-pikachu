class Penguin:
    \"\"\"
    ผู้เล่น (Player Entity) ไม่มีพลังชีวิต (HP) ตายเมื่อ:
    1. ตกหลุมเดินผิดเลนพ้นตาราง
    2. หลบสิ่งกีดขวางหรือทุบบล็อกอุปสรรคไม่ทัน จนโดนพื้นหล่นใส่ไล่หลังทัน
    \"\"\"
    def __init__(self, start_col=0, start_row=0):
        self.col = start_col
        self.row = start_row
        self.is_dead = False
        
        # หันหน้าทางตารางแกนไหน (เช่น +y หมายถึงพุ่งไปข้างหน้า, +x หมายถึงเฉียงขวา)
        self.direction = (0, 1)  # ปกติให้พุ่งตามแกน Row ให้เป็น forward
        
        # ระบบ Skin
        self.skin = 'default'
        
    def equip_skin(self, skin_id):
        self.skin = skin_id

    def move_forward(self):
        \"\"\"วิ่งตรงต่อไปข้างหน้า 1 หน่วยบนเส้นทางในเกม\"\"\"
        if not self.is_dead:
            self.col += self.direction[0]
            self.row += self.direction[1]

    def turn_left(self):
        \"\"\"หันเลี้ยวซ้าย 90 องศาเปลี่ยนแกนการเดิน\"\"\"
        # คันตรรกะเลี้ยว (0, 1) -> (-1, 0) -> (0, -1) -> (1, 0)
        self.direction = (-self.direction[1], self.direction[0])
        
    def turn_right(self):
        \"\"\"หันเลี้ยวขวา 90 องศาเปลี่ยนแกนการเดิน\"\"\"
        self.direction = (self.direction[1], -self.direction[0])

    def die(self):
        self.is_dead = True
