from enum import Enum
from typing import List


class ItemType(Enum):
    ALBEDO_DATA = "Albedo Data"
    METHANE_CORE = "Methane Core"
    ECO_SEED = "Eco-Seed"


class Inventory:
    """ระบบช่องเก็บของ 3 slot (D1-B2)"""

    MAX_SLOTS = 3

    def __init__(self):
        self.slots: List[ItemType] = []

    def add_item(self, item: ItemType) -> bool:
        """เพิ่มไอเทมลง Inventory คืนค่า True ถ้าสำเร็จ"""
        if len(self.slots) < self.MAX_SLOTS:
            self.slots.append(item)
            return True
        return False

    def use_item(self, item: ItemType) -> bool:
        """ใช้ไอเทมและนำออกจาก Inventory"""
        if item in self.slots:
            self.slots.remove(item)
            return True
        return False

    def has_item(self, item: ItemType) -> bool:
        return item in self.slots

    def get_items(self) -> List[ItemType]:
        return self.slots
