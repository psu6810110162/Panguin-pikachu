"""D1-A2 acceptance: Y-Junction ต้องเกิดครบ 10 โซน ไม่ซ้ำ ไม่หาย (กัน regression zone-skip)

บั๊กเดิม: _append_segment consume โซน (next_zone += 1) ก่อนเช็คว่า fork สร้างได้จริง
(_seg_count >= 2) — โซนที่ถึงกำหนดตอน segment ยังไม่พอจะหายเงียบ ทำให้ junction < 10
และ Stealth/DAG ฝั่ง scoring ขาด decision
"""

from game.grid import GridManager

# _append_segment เพิ่ม tile อย่างน้อย 1 tile ต่อรอบเสมอ — 3000 รอบพอถึง 1000m แน่นอน
_MAX_SEGMENTS = 3000


def _generate_until_finish_line(grid: GridManager) -> None:
    for _ in range(_MAX_SEGMENTS):
        if grid._total_generated >= 1000:
            return
        grid._append_segment()
    raise AssertionError("grid ไม่ถึง 1000m ภายในจำนวน segment ที่จำกัด")


def _zone_tiles(grid: GridManager) -> dict[int, set[str]]:
    """map zone_id -> เซ็ตของ side ที่ถูก tag บน tile (จุด entry ของ fork แต่ละข้าง)"""
    zones: dict[int, set[str]] = {}
    for tile in grid.path_set.values():
        if tile.zone_id is not None:
            zones.setdefault(tile.zone_id, set()).add(tile.side)
    return zones


def test_all_10_zones_spawn_a_junction_before_finish_line():
    grid = GridManager()
    grid.reset()
    _generate_until_finish_line(grid)

    zones = _zone_tiles(grid)
    assert sorted(zones.keys()) == list(range(1, 11)), (
        f"junction ต้องครบโซน 1-10 ไม่ซ้ำ ได้: {sorted(zones.keys())}"
    )


def test_every_junction_has_both_left_and_right_entry():
    grid = GridManager()
    grid.reset()
    _generate_until_finish_line(grid)

    for zone_id, sides in _zone_tiles(grid).items():
        assert sides == {"left", "right"}, f"โซน {zone_id} มี entry แค่ {sides}"


def test_zones_are_stable_across_multiple_resets():
    """reset แล้ว generate ใหม่ ต้องยังครบ 10 โซนทุกครั้ง (spawn สุ่มตำแหน่งในโซนได้
    แต่ห้ามหายทั้งโซน)"""
    grid = GridManager()
    for _ in range(3):
        grid.reset()
        _generate_until_finish_line(grid)
        assert sorted(_zone_tiles(grid).keys()) == list(range(1, 11))
