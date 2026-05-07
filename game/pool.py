from game.gem import Gem       # นำเข้าคลาสไอเทม Gem
from core.logger import logger

class ObjectPool:
    """
    ระบบ Object Pooling สำหรับ Gem
    - ช่วยลดปัญหาการสร้างและลบวัตถุใหม่ซ้ำๆ (Frequent Allocation/Deallocation)
    - obstacles ย้ายไปใช้ prop string แทน (ไม่ต้อง pool แล้ว)
    """
    def __init__(self, create_func, initial_size=20, max_size=200):
        self.create_func = create_func
        self.max_size = max_size
        self.pool = [self.create_func() for _ in range(initial_size)]

    def get(self):
        for obj in self.pool:
            if not getattr(obj, 'active', False):
                return obj
        if len(self.pool) >= self.max_size:
            logger.warning(f"ObjectPool exceeded max_size={self.max_size}; possible leak")
        new_obj = self.create_func()
        self.pool.append(new_obj)
        return new_obj

class Pools:
    # Gem pool ยังใช้ Object Pooling (มี animation state)
    gems = ObjectPool(lambda: Gem(), initial_size=10)
