from core.config import TILE_TO_METER

class GridManager:
    """
    ตัวจัดการตาราง Grid แบบ Zigzag Isometric
    สร้างเส้นทางเดินที่หักเลี้ยวสลับซ้าย-ขวาแบบสุ่มความยาว
    """

    # ทิศทางสองแกนที่สลับกันเป็นซิกแซก
    DIR_A = (1, 0)   # เดินไปทาง +col (เฉียงขวาบน)
    DIR_B = (0, 1)   # เดินไปทาง +row (เฉียงซ้ายบน)

    def __init__(self):
        self.forward_tiles = 0
        self.path = []          # ลิสต์ตำแหน่ง (col, row) ของทางเดินทั้งหมด
        self.path_set = set()   # set สำหรับเช็คตำแหน่งเร็วๆ
        self.turn_points = []   # จุดหักเลี้ยว (col, row) ที่ผู้เล่นต้องกด ← / →
        
        # ── LEVEL DESIGN (TEXT MAP) ──
        # S = Start (จุดเริ่มต้น)
        # 1 = Path (ทางเดิน)
        # . = Empty (ช่องว่าง)
        # 
        # การวางแผนผังให้มองเป็น Grid 2D (แถว, คอลัมน์) 
        # โดยให้เดินพาดไปตามตัวเลข 1 จนสุดทาง การหาเส้นทางจะใช้วิธีไล่ไปตามจุดที่ติดกัน
        self.level_map = [
            "..1",
            "SSS",
            "SSS",
            "SSS"
        ]

    def reset(self):
        """เริ่มเกมใหม่ สร้างเส้นทางตั้งต้น"""
        self.forward_tiles = 0
        self.path.clear()
        self.path_set.clear()
        self.turn_points.clear()
        
        # สร้างเส้นทางจากไฟล์แผนที่
        self.generate_path()

    def generate_path(self):
        """อ่าน text map และแปลงเป็น path ตามลำดับ"""
        if self.path:
            return  # สร้างไปแล้ว
            
        start_candidates = []
        path_tiles = set()
        
        # 1. หาจุด 'S' และช่อง '1' ทั้งหมด
        for r, row_str in enumerate(self.level_map):
            for c, char in enumerate(row_str):
                # (คอลัมน์จากซ้ายไปขวา, แถวจากล่างขึ้นบน) เพื่อให้เข้ากับ Isometric Grid
                # แปลง r จากบนลงล่าง ให้เป็นจากล่างขึ้นบน (ตรงกับแกน row ในเกม)
                grid_col = c
                grid_row = len(self.level_map) - 1 - r 
                
                if char == 'S':
                    start_candidates.append((grid_col, grid_row))
                    path_tiles.add((grid_col, grid_row))
                elif char == '1':
                    path_tiles.add((grid_col, grid_row))
                    
        if start_candidates:
            # เลือกจุด S ที่อยู่ล่างสุดในมุมมอง Isometric (คือจุดที่ col + row น้อยที่สุด)
            start_pos = min(start_candidates, key=lambda t: t[0] + t[1])
        else:
            start_pos = (0, 0)
            path_tiles.add(start_pos)
            
        # 2. เรียงลำดับ path จาก 'S' ไปหาทางที่เชื่อมต่อกัน (Pathfinding ง่ายๆ)
        current = start_pos
        self.path.append(current)
        self.path_set.add(current)
        path_tiles.remove(current)

        while path_tiles:
            found_next = False
            # หา tile ที่ติดกัน (เดินขึ้น, ลง, ซ้าย, ขวา)
            for neighbor in [
                (current[0] + 1, current[1]),
                (current[0] - 1, current[1]),
                (current[0], current[1] + 1),
                (current[0], current[1] - 1)
            ]:
                if neighbor in path_tiles:
                    current = neighbor
                    self.path.append(current)
                    self.path_set.add(current)
                    path_tiles.remove(current)
                    found_next = True
                    break
            
            if not found_next:
                # ถ้าหาทางไปต่อไม่เจอ ให้หยุด (แสดงว่าแผนที่ขาด)
                break
                
        # 3. คำนวณจุดหักเลี้ยวจากการเปลี่ยนทิศทาง
        if len(self.path) > 2:
            prev_dir = (self.path[1][0] - self.path[0][0], self.path[1][1] - self.path[0][1])
            for i in range(1, len(self.path) - 1):
                curr_dir = (self.path[i+1][0] - self.path[i][0], self.path[i+1][1] - self.path[i][1])
                if curr_dir != prev_dir:
                    self.turn_points.append(self.path[i])
                    prev_dir = curr_dir

    def step_forward(self):
        """ถูกเรียกเมื่อเกมเลื่อนไปข้างหน้า 1 ช่อง"""
        self.forward_tiles += 1

    def get_distance_m(self):
        """แปลงก้าวเดินเป็นหน่วยเมตร"""
        return self.forward_tiles * TILE_TO_METER

    def is_on_path(self, col, row):
        """เช็คว่าตำแหน่ง (col, row) อยู่บนทางเดินหรือไม่"""
        return (col, row) in self.path_set

    def get_correct_direction_at(self, path_index):
        """
        ดูว่า ณ ตำแหน่ง index นี้ในเส้นทาง ทิศทางที่ถูกต้องคืออะไร
        ใช้เพื่อให้เพนกวินวิ่งอัตโนมัติตามเส้นทาง
        """
        if path_index + 1 < len(self.path):
            curr = self.path[path_index]
            nxt = self.path[path_index + 1]
            return (nxt[0] - curr[0], nxt[1] - curr[1])
        return None

    def get_path_index(self, col, row):
        """หา index ของตำแหน่งใน path"""
        try:
            return self.path.index((col, row))
        except ValueError:
            return -1
