from game.blocks import Obstacle
from game.gem import Gem

class ObjectPool:
    """
    ระบบ Object Pooling สำหรับ Obstacle และ Gem 
    ลดปัญหา Framerate ตกจากการใช้ Garbage Collector บ่อยเกินไปในเกมแนววิ่ง
    """
    def __init__(self, create_func, initial_size=20):
        self.create_func = create_func
        self.pool = [self.create_func() for _ in range(initial_size)]
        
    def get(self):
        # หา Object ที่ถูกปิดการใช้งานเพื่อนำกลับมาใช้ใหม่
        for obj in self.pool:
            if not getattr(obj, 'active', False): 
                return obj
                
        # หากใช้หมดแล้วจริงๆ ให้ขยาย Pool เพิ่ม
        new_obj = self.create_func()
        self.pool.append(new_obj)
        return new_obj

# สร้างระบบสระเก็บไว้เรียกใช้งานได้ทันที 
class Pools:
    obstacles = ObjectPool(lambda: Obstacle(), initial_size=20)
    gems = ObjectPool(lambda: Gem(), initial_size=10)
