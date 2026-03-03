import random
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
        self.current_dir = self.DIR_A  # ทิศปัจจุบันของเส้นทาง

    def reset(self):
        """เริ่มเกมใหม่ สร้างเส้นทางตั้งต้น"""
        self.forward_tiles = 0
        self.path.clear()
        self.path_set.clear()
        self.turn_points.clear()
        self.current_dir = self.DIR_A
        self.generate_path(num_segments=30)

    def generate_path(self, num_segments=30):
        """สร้างเส้นทาง Zigzag สุ่มความยาวแต่ละช่วง"""
        if not self.path:
            # จุดเริ่มต้น
            self.path.append((0, 0))
            self.path_set.add((0, 0))

        for _ in range(num_segments):
            # สุ่มความยาวช่วงนี้ (3-8 ช่อง)
            segment_len = random.randint(3, 8)

            last = self.path[-1]
            for step in range(segment_len):
                new_pos = (last[0] + self.current_dir[0],
                           last[1] + self.current_dir[1])
                self.path.append(new_pos)
                self.path_set.add(new_pos)
                last = new_pos

            # เก็บจุดหักเลี้ยว (ตำแหน่งสุดท้ายของช่วงนี้)
            self.turn_points.append(last)

            # สลับทิศทาง (Zigzag)
            if self.current_dir == self.DIR_A:
                self.current_dir = self.DIR_B
            else:
                self.current_dir = self.DIR_A

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
