import random # นำเข้าไลบรารีสุ่ม
from game.pool import Pools # นำเข้าระบบ Object Pool เพื่อดึงวัตถุกลับมาใช้ใหม่

class ObstacleFactory:
    """
    คลาสโรงงานผลิตสิ่งกีดขวาง (ObstacleFactory)
    - ทำหน้าที่นำวัตถุดิบ (กล่อง/Gem) จาก Object Pool มาประกอบร่าง
    - สุ่มระดับความยาก (Size 1-5) โดยอิงจากระยะทางที่ผู้เล่นวิ่งมา
    """
    @staticmethod
    def spawn_obstacle(distance_m, col_position, row_position):
        """ ฟังก์ชันสร้างกล่องอุปสรรค ณ พิกัดที่กำหนด """
        # 1. ขอดึงวัตถุ Obstacle ที่ไม่ได้ถูกใช้งานมาจาก Pool (เพื่อประหยัด Memory)
        obs = Pools.obstacles.get()
        
        # 2. คำนวณความยาก (Difficulty Scaling)
        # วิ่งไปยิ่งไกล ยิ่งมีโอกาสสุ่มเจอบล็อกระดับสูงๆ (Size 4-5) มากขึ้น
        # สูตร: เพิ่มเพดานความสูงของบล็อกขึ้น 1 ทุกๆ 40 เมตร (จำกัดสูงสุดที่ 5)
        max_size = min(5, 1 + (int(distance_m) // 40))
        
        # 3. สุ่มขนาดที่แท้จริงของบล็อก และรีเซ็ตค่าสถานะ
        random_size = random.randint(1, max_size)
        obs.reset(size=random_size)
        
        # 4. กำหนดตำแหน่งพิกัดบนตาราง
        obs.col = col_position
        obs.row = row_position
        
        return obs # ส่งวัตถุกลับไปให้ GridManager ใช้งาน
        
    @staticmethod
    def spawn_gem(col_position, row_position):
        """ ฟังก์ชันสร้าง Gem ณ พิกัดที่กำหนด """
        gem = Pools.gems.get()   # ดึง Gem จาก Pool
        gem.reset()              # รีเซ็ตสถานะ (เช่น active=True)
        gem.col = col_position   # ตั้งพิกัด Column
        gem.row = row_position   # ตั้งพิกัด Row
        return gem
