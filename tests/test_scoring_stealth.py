import pytest

from core.events import BossPhaseEvent, GameEvent, PolicyChoiceEvent
from core.scoring import stealth
from core.scoring.stealth import RankBand, ScoringConfig

# ScoringConfig ทดสอบเอง — แยกจากค่าจริงใน balance/v1/difficulty.json เพื่อไม่ให้ test
# เปราะบางเมื่อทีมปรับ tuning ทีหลัง มี test แยกท้ายไฟล์ที่ตรวจว่า load_config() จริงพาร์สได้
_CONFIG = ScoringConfig(
    systemic_point_c=0.1,
    max_run_reduction_c=1.0,
    boss_bonus_per_wave_c=0.1,
    max_boss_reduction_c=0.5,
    ranks=(
        RankBand(rank="S", label="Eco-Systemic Master", min_c=1.3, max_c=1.5),
        RankBand(rank="A", label="Green Negotiator", min_c=0.8, max_c=1.2),
    ),
)


def _policy(policy_id: str) -> PolicyChoiceEvent:
    return PolicyChoiceEvent(
        timestamp=0.0, distance_m=0, checkpoint_index=0, policy_id=policy_id, meter_deltas={}
    )


def _boss(outcome: str) -> BossPhaseEvent:
    return BossPhaseEvent(timestamp=0.0, distance_m=1000, phase=1, outcome=outcome)  # type: ignore[arg-type]


def test_systemic_choice_count_only_counts_systemic_options():
    # zone1-right (solar) and zone2-left (ป่าสงวน) are systemic; zone3-left (EV subsidy) is not
    events: list[GameEvent] = [_policy("zone1-right"), _policy("zone2-left"), _policy("zone3-left")]
    assert stealth.systemic_choice_count(events) == 2


def test_systemic_choice_count_dedupes_duplicate_zone_first_write_wins():
    # zone1 ปรากฏสองครั้ง (เช่น ตายกลาง fork แล้ว respawn เดินผ่านซ้ำ, #46) — ตัวแรกเป็น
    # systemic (right) ตัวสองไม่ใช่ (left) ต้องนับแค่ตัวแรก ไม่ใช่ 0 หรือ 2
    events: list[GameEvent] = [_policy("zone1-right"), _policy("zone1-left")]
    assert stealth.systemic_choice_count(events) == 1


def test_systemic_choice_count_dedupe_does_not_drop_other_zones():
    events: list[GameEvent] = [
        _policy("zone1-right"),
        _policy("zone1-left"),  # ซ้ำ zone1 — ไม่นับ
        _policy("zone2-left"),
    ]
    assert stealth.systemic_choice_count(events) == 2


def test_run_reduction_c_multiplies_systemic_count_by_point_value():
    events: list[GameEvent] = [_policy("zone1-right"), _policy("zone2-left")]
    assert stealth.run_reduction_c(events, config=_CONFIG) == 0.2


def test_run_reduction_c_is_capped_at_max_run_reduction():
    # เกมมีแค่ 10 zone จริง (ซ้ำ zone เดียวกันไม่นับซ้ำแล้วหลัง fix dedup) ใช้ 10 zone จริง
    # แยกกันทั้งหมด (all_junctions) เลือกฝั่ง systemic ทุกอัน = 10 systemic choices แล้วตั้ง
    # cap ให้แคบกว่านั้นเพื่อทดสอบว่า capping ทำงานจริง
    from core.junction_data import all_junctions

    events: list[GameEvent] = [
        _policy(j.policy_id("left" if j.left.systemic else "right")) for j in all_junctions()
    ]
    tight_cap_config = ScoringConfig(
        systemic_point_c=_CONFIG.systemic_point_c,
        max_run_reduction_c=0.5,  # 10 * 0.1 = 1.0, capped ที่ 0.5
        boss_bonus_per_wave_c=_CONFIG.boss_bonus_per_wave_c,
        max_boss_reduction_c=_CONFIG.max_boss_reduction_c,
        ranks=_CONFIG.ranks,
    )
    assert stealth.run_reduction_c(events, config=tight_cap_config) == 0.5


def test_correct_boss_wave_count_only_counts_damage_dealt():
    events: list[GameEvent] = [
        _boss("damage_dealt"),
        _boss("damaged"),
        _boss("damage_dealt"),
    ]
    assert stealth.correct_boss_wave_count(events) == 2


def test_cognitive_score_c_multiplies_correct_waves_by_bonus():
    events: list[GameEvent] = [_boss("damage_dealt"), _boss("damage_dealt")]
    assert stealth.cognitive_score_c(events, config=_CONFIG) == 0.2


def test_cognitive_score_c_is_capped_at_max_boss_reduction():
    events: list[GameEvent] = [_boss("damage_dealt")] * 6  # 6 * 0.1 = 0.6, capped at 0.5
    assert stealth.cognitive_score_c(events, config=_CONFIG) == 0.5


def test_net_impact_score_c_sums_run_and_boss_reductions():
    events: list[GameEvent] = [
        _policy("zone1-right"),
        _policy("zone2-left"),
        _boss("damage_dealt"),
    ]
    assert stealth.net_impact_score_c(events, config=_CONFIG) == pytest.approx(0.3)


def test_net_impact_score_c_is_deterministic_across_repeated_calls():
    events: list[GameEvent] = [_policy("zone1-right"), _boss("damage_dealt"), _boss("damaged")]
    first = stealth.net_impact_score_c(events, config=_CONFIG)
    second = stealth.net_impact_score_c(events, config=_CONFIG)
    assert first == second


def test_rank_for_matches_s_band():
    assert stealth.rank_for(1.5, config=_CONFIG) == "S"
    assert stealth.rank_for(1.3, config=_CONFIG) == "S"


def test_rank_for_matches_a_band():
    assert stealth.rank_for(0.8, config=_CONFIG) == "A"
    assert stealth.rank_for(1.2, config=_CONFIG) == "A"


def test_rank_for_returns_none_below_lowest_band():
    assert stealth.rank_for(0.79, config=_CONFIG) is None


def test_rank_for_returns_none_in_gap_between_bands():
    assert stealth.rank_for(1.25, config=_CONFIG) is None


def test_load_config_parses_real_balance_file():
    config = stealth.load_config()
    assert config.systemic_point_c == 0.1
    assert config.max_boss_reduction_c == 0.5
    assert {band.rank for band in config.ranks} == {"S", "A"}


# ── Robustness: server-authoritative scoring ต้องไม่ crash จาก policy_id เสีย ──
# (client เชื่อไม่ได้; producer ที่ยัง emit "left"/"right" แทน "zone{N}-{side}" ก็ต้องไม่ทำ
#  ให้ evaluate()/ingest ล่ม — นับเป็น non-systemic แทน) ดู docs/adr/006


@pytest.mark.parametrize("bad_id", ["left", "right", "", "zone-left", "zoneX-left", "zone99-left"])
def test_systemic_choice_count_ignores_malformed_policy_id(bad_id: str) -> None:
    # ไม่ raise และไม่ถูกนับเป็น systemic
    assert stealth.systemic_choice_count([_policy(bad_id)]) == 0


def test_malformed_policy_id_does_not_crash_net_impact() -> None:
    events: list[GameEvent] = [_policy("right"), _policy("zone1-right")]
    # "right" ถูกข้าม, "zone1-right" (systemic ใน balance/v1) นับ 1 -> 0.1°C
    assert stealth.net_impact_score_c(events) == pytest.approx(0.1)
