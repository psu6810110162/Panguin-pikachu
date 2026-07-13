import random
from typing import List, Dict


class SpawningSystem:
    """ระบบสุ่มตำแหน่งเกิด Y-Junction (D1-A2)"""

    TOTAL_DISTANCE = 1000
    ZONE_SIZE = 100
    NUM_ZONES = 10

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self.junction_spawns: Dict[int, float] = self._generate_spawns()

    def _generate_spawns(self) -> Dict[int, float]:
        """สุ่มตำแหน่ง 1 จุด ต่อ 1 โซน (คืนค่า Dictionary {zone_id: spawn_distance_m})"""
        spawns = {}
        for zone in range(1, self.NUM_ZONES + 1):
            # โซน 1 = 0-100m, โซน 2 = 100-200m ...
            min_dist = (zone - 1) * self.ZONE_SIZE
            max_dist = zone * self.ZONE_SIZE

            # เผื่อระยะขอบเพื่อให้ไม่เกิดติดกันเกินไป (เช่น ขอบละ 10m)
            spawn_dist = random.uniform(min_dist + 10, max_dist - 10)
            spawns[zone] = round(spawn_dist, 2)

        return spawns

    def get_spawn_distance(self, zone_id: int) -> float:
        return self.junction_spawns.get(zone_id, 0.0)

    def get_all_spawns(self) -> Dict[int, float]:
        return self.junction_spawns
