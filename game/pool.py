from game.blocks import Obstacle # นำเข้าคลาสอุปสรรค์
from game.gem import Gem       # นำเข้าคลาสไอเทม Gem
from core.logger import logger

class ObjectPool:
    """
    ระบบ Object Pooling สำหรับ Obstacle และ Gem
    - ช่วยลดปัญหาการสร้างและลบวัตถุใหม่ซ้ำๆ (Frequent Allocation/Deallocation)
    - ป้องกันปัญหา Framerate ตกจากการที่ Garbage Collector ทำงานบ่อยเกินไป
    """
    def __init__(self, create_func, initial_size=20, max_size=200):
        self.create_func = create_func # ฟังก์ชันสำหรับสร้างวัตถุใหม่ (เช่น Lambda)
        self.max_size = max_size
        # สร้างวัตถุเตรียมไว้ล่วงหน้า (Pre-allocation) ตามจำนวนที่กำหนด
        self.pool = [self.create_func() for _ in range(initial_size)]

    def get(self):
        """ ฟังก์ชันขอดึงวัตถุจาก Pool มาเลือกใช้ """
        # วนลูปหาวัตถุในตะกร้าที่ถูกปิดการใช้งาน (active=False) เพื่อนำกลับมาใช้ใหม่
        for obj in self.pool:
            if not getattr(obj, 'active', False):
                return obj

        # หากใช้จนหมดตะกร้า ให้สร้างวัตถุใหม่เพิ่มเข้า Pool (Dynamic Expansion)
        if len(self.pool) >= self.max_size:
            logger.warning(f"ObjectPool exceeded max_size={self.max_size}; possible leak")
        new_obj = self.create_func()
        self.pool.append(new_obj)
        return new_obj

# คลาสรวมศูนย์สำหรับเรียกใช้งาน Object Pool ในจุดต่างๆ ของโปรแกรม
class Pools:
    # สร้าง Pool สำหรับบล็อกอุปสรรค (เริ่มต้น 20 ชิ้น)
    obstacles = ObjectPool(lambda: Obstacle(), initial_size=20)
    # สร้าง Pool สำหรับ Gem (เริ่มต้น 10 ชิ้น)
    gems = ObjectPool(lambda: Gem(), initial_size=10)
