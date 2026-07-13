from core.items import Inventory, ItemType


def test_inventory_add():
    inv = Inventory()
    assert inv.add_item(ItemType.ALBEDO_DATA)
    assert inv.has_item(ItemType.ALBEDO_DATA)
    assert len(inv.get_items()) == 1



def test_inventory_max_slots():
    inv = Inventory()
    assert inv.add_item(ItemType.ALBEDO_DATA)
    assert inv.add_item(ItemType.METHANE_CORE)
    assert inv.add_item(ItemType.ECO_SEED)
    assert not inv.add_item(ItemType.ALBEDO_DATA)  # ควรเต็ม (3 ช่อง)
    assert len(inv.get_items()) == 3



def test_inventory_use():
    inv = Inventory()
    inv.add_item(ItemType.ECO_SEED)
    assert inv.use_item(ItemType.ECO_SEED)
    assert not inv.has_item(ItemType.ECO_SEED)
    assert not inv.use_item(ItemType.ECO_SEED)  # ไม่มีให้ใช้แล้ว
