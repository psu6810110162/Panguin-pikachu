import random


class EventManager:
    """
    ตัดสินว่าถึงเวลา trigger Quiz Event หรือยัง
    Event จะเกิดขึ้นทุกๆ 50-100 เมตร (random interval)
    """
    INTERVAL_MIN = 50
    INTERVAL_MAX = 100

    def __init__(self):
        self.reset()

    def reset(self):
        self._next_trigger = random.randint(self.INTERVAL_MIN, self.INTERVAL_MAX)
        self._active = False  # True ขณะที่ quiz กำลังแสดงอยู่

    def should_trigger(self, dist_m: float) -> bool:
        return not self._active and dist_m >= self._next_trigger

    def mark_triggered(self, dist_m: float):
        self._active = True
        self._next_trigger = dist_m + random.randint(self.INTERVAL_MIN, self.INTERVAL_MAX)

    def mark_finished(self):
        self._active = False
