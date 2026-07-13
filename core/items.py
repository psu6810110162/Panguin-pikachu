from enum import Enum


class ItemType(Enum):
    ALBEDO_DATA = "albedo_data"
    METHANE_CORE = "methane_core"
    ECO_SEED = "eco_seed"


class Inventory:
    """ระบบช่องเก็บของ 3 slot (D1-B2)"""

    MAX_SLOTS = 3

    def __init__(self) -> None:
        self.slots: list[ItemType] = []

    def add_item(self, item: ItemType) -> bool:
        """เพิ่มไอเทมลง Inventory คืนค่า True ถ้าสำเร็จ (ห้ามเก็บไอเทมซ้ำ)"""
        if item in self.slots:
            return False
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

    def get_items(self) -> list[ItemType]:
        return self.slots
