"""SpawningSystem — สุ่มจุดเกิด Y-Junction 1 จุดต่อโซน ตลอด 1000m (D1-A2).

RNG ต้อง isolate (random.Random instance) เพื่อ determinism — seed เดียวกันได้ผลเดิม
และแต่ละจุดต้องตกในช่วงของโซนตัวเอง (กัน junction ล้ำโซนกัน)
"""

from core.spawning import SpawningSystem


def test_same_seed_produces_identical_spawns() -> None:
    a = SpawningSystem(seed=42).get_all_spawns()
    b = SpawningSystem(seed=42).get_all_spawns()
    assert a == b


def test_different_seeds_differ() -> None:
    a = SpawningSystem(seed=1).get_all_spawns()
    b = SpawningSystem(seed=2).get_all_spawns()
    assert a != b


def test_one_spawn_per_zone_covering_all_ten_zones() -> None:
    spawns = SpawningSystem(seed=7).get_all_spawns()
    assert sorted(spawns) == list(range(1, SpawningSystem.NUM_ZONES + 1))


def test_every_spawn_falls_inside_its_own_zone_bounds() -> None:
    spawns = SpawningSystem(seed=7).get_all_spawns()
    for zone, dist in spawns.items():
        lower = (zone - 1) * SpawningSystem.ZONE_SIZE
        upper = zone * SpawningSystem.ZONE_SIZE
        assert lower <= dist <= upper, f"zone {zone} spawn {dist} หลุดขอบเขต [{lower},{upper}]"


def test_get_spawn_distance_returns_zero_for_unknown_zone() -> None:
    system = SpawningSystem(seed=7)
    assert system.get_spawn_distance(999) == 0.0
    assert system.get_spawn_distance(1) == system.get_all_spawns()[1]
