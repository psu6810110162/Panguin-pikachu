from core.config import TILE_TO_METER

class GridManager:
    \"\"\"
    ตัวจัดการตาราง Grid ของเกมและแนวทางเดิน 
    หน้าที่หลัก:
    - คำนวณขอบเขตทางเดินแบบ Isometric (Zigzag)
    - ตรวจสอบการชน (Collision)
    - นับจำนวนก้าวเดิน (forward_tiles) เพื่อคูณเป็นระยะทาง
    \"\"\"
    def __init__(self):
        # 0 คือเริ่มต้น, นับเพิ่มทุกครั้งที่หน้าจอเลื่อนไป 1 บล็อกบนเส้นทางหลัก
        self.forward_tiles = 0  
        self.path = [] # รายการตำแหน่ง (col, row) ของพื้นทางเดินที่เหยียบได้
    
    def reset(self):
        \"\"\"เริ่มเกมใหม่ รีเซ็ตค่าระยะทางทั้งหมด\"\"\"
        self.forward_tiles = 0
        self.path.clear()
        self.generate_initial_path()

    def generate_initial_path(self):
        \"\"\"สร้างเส้นทางตั้งต้นให้ผู้เล่นยืน\"\"\"
        # สร้างทางตรงให้ก่อน จากนั้นค่อยสับสลับซ้ายขวาในเฟสต่อๆ ไป
        for i in range(10):
            self.path.append((0, i))
            
    def step_forward(self):
        \"\"\"ถูกเรียกเมื่อเกมเลื่อนไปข้างหน้า 1 ช่อง\"\"\"
        self.forward_tiles += 1
        
    def get_distance_m(self):
        \"\"\"แปลงก้าวเดินเป็นหน่วยเมตร (ใช้แสดงค่าบน HUD หน้าจอ)\"\"\"
        return self.forward_tiles * TILE_TO_METER

    def is_on_path(self, col, row):
        \"\"\"เช็คว่าตัวละคร (col, row) หล่นจากกระดานทางเดินหรือไม่\"\"\"
        return (col, row) in self.path
