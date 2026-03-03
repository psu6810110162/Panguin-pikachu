import random
from game.pool import Pools

class ObstacleFactory:
    """
    ตัวนำวัตถุดิบจาก Object Pool มาประกอบสร้างและส่งให้ตัวเกม
    หน้าที่หลัก: สุ่มระดับความยาก (Size 1-5) ตามระยะทางที่ผู้เล่นวิ่งมา
    """
    @staticmethod
    def spawn_obstacle(distance_m, col_position, row_position):
        # 1. ขอบล็อกที่ไม่ได้ถูกใช้งานจาก Pool
        obs = Pools.obstacles.get()
        
        # 2. คำนวณความยาก
        # วิ่งไปยิ่งไกล ยิ่งมีโอกาสสุ่มเจอบล็อกระดับ 4-5 มากขึ้น
        max_size = min(5, 1 + (distance_m // 100)) # เพิ่ม Size สูงสุดทุกๆ 100 เมตร
        
        # 3. ตั้งค่าแล้วรีเซ็ต
        random_size = random.randint(1, max_size)
        obs.reset(size=random_size)
        
        # 4. (ตัวแปรเสริมสำหรับประกอบร่างลงหน้าจอ)
        obs.col = col_position
        obs.row = row_position
        
        return obs
        
    @staticmethod
    def spawn_gem(col_position, row_position):
        gem = Pools.gems.get()
        gem.reset()
        gem.col = col_position
        gem.row = row_position
        return gem
