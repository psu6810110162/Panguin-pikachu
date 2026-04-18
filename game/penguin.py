class Penguin:
    """
    คลาสผู้เล่น (Player Entity)
    - เก็บตำแหน่งปัจจุบัน (col, row)
    - จัดการทิศทางการวิ่งและการหันเลี้ยว
    - จัดการระบบสกิน (Skins) และการโหลด Asset ที่เกี่ยวข้อง
    - ผู้เล่นไม่มีเลือด (HP) จะตายทันทีเมื่อตกพื้นหรือโดนแผ่นพื้นไล่หลังทัน
    """
    def __init__(self, start_col=0, start_row=0):
        self.col = start_col # พิกัด Column เริ่มต้น
        self.row = start_row # พิกัด Row เริ่มต้น
        self.is_dead = False # สถานะว่าตายหรือยัง
        
        # เวกเตอร์ทิศทาง (direction) บอกว่าก้าวถัดไปจะไปทางไหน
        # (0, 1) หมายถึง พุ่งไปข้างหน้าตามแนว Row (Isometric Forward)
        self.direction = (0, 1)  
        
        # ระบบสกิน (Skin System)
        self.skin = 'Ninja Frog' # สกินเริ่มต้น
        self.facing_left = False  # ทิศทางการหันหน้า (False = หันขวา, True = หันซ้าย)
        
        # รายการแม็พชื่อสกิน (ID) กับ ชื่อโฟลเดอร์สำหรับโหลดไฟล์รูปภาพแอนิเมชัน
        self.SKIN_ASSETS = {
            'Mask Dude': 'Mask Dude',
            'Ninja Frog': 'Ninja Frog',
            'Pink Man': 'Pink Man',
            'Virtual Guy': 'Virtual Guy'
        }
        
    def equip_skin(self, skin_id):
        """ เปลี่ยนสกินปัจจุบันของผู้เล่นตาม ID ที่ส่งมา """
        if skin_id in self.SKIN_ASSETS:
            self.skin = skin_id

    def get_skin_path(self, action='Idle'):
        """ สร้าง Path สำหรับโหลดรูปภาพแอนิเมชันตามท่าทาง (Action) ที่ต้องการ """
        folder = self.SKIN_ASSETS.get(self.skin, 'Ninja Frog') # ดึงชื่อโฟลเดอร์จาก ID
        if action == 'Idle':
            # ท่ายืนนิ่ง
            return f'assets/pixelAdventure/Free/Main Characters/{folder}/Idle (32x32).png'
        elif action == 'Fall':
            # ท่าตกรอบ
            return f'assets/pixelAdventure/Free/Main Characters/{folder}/Fall (32x32).png'
        # ค่าเริ่มต้นถ้าไม่ตรงกับท่าไหนเลยให้ใช้ท่ายืนนิ่ง
        return f'assets/pixelAdventure/Free/Main Characters/{folder}/Idle (32x32).png'

    def move_forward(self):
        """ วิ่งตรงต่อไปข้างหน้า 1 หน่วยบนเส้นทางในเกม """
        if not self.is_dead:
            self.col += self.direction[0]
            self.row += self.direction[1]

    def turn_left(self):
        """ หันเลี้ยวซ้าย 90 องศา (ใช้หลักการคณิตศาสตร์เวกเตอร์ในการเปลี่ยนทิศ) """
        # ตรรกะการหมุนเวกเตอร์ทวนเข็มนาฬิกา: (x, y) กลายเป็น (-y, x)
        self.direction = (-self.direction[1], self.direction[0])
        
    def turn_right(self):
        """ หันเลี้ยวขวา 90 องศา (ใช้หลักการคณิตศาสตร์เวกเตอร์ในการเปลี่ยนทิศ) """
        # ตรรกะการหมุนเวกเตอร์ตามเข็มนาฬิกา: (x, y) กลายเป็น (y, -x)
        self.direction = (self.direction[1], -self.direction[0])

    def die(self):
        """ เปลี่ยนสถานะเป็นตาย (เกมจะจบทันที) """
        self.is_dead = True
