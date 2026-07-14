import pytest

from core.junction_data import (
    all_junctions,
    get_junction,
    option_for_policy_id,
    parse_policy_id,
)


def test_get_junction_returns_zone_1_cause_data():
    junction = get_junction(1)
    assert junction.zone == 1
    assert junction.category == "cause"
    assert junction.left.meter_deltas == {"heat": 25, "capitalist_anger": -20}
    assert junction.right.meter_deltas == {"heat": -20, "capitalist_anger": 25}


def test_get_junction_raises_key_error_for_unknown_zone():
    with pytest.raises(KeyError):
        get_junction(11)


def test_all_junctions_returns_ten_sorted_by_zone():
    junctions = all_junctions()
    assert [j.zone for j in junctions] == list(range(1, 11))


def test_junction_option_selects_left_or_right():
    junction = get_junction(1)
    assert junction.option("left") is junction.left
    assert junction.option("right") is junction.right


def test_policy_id_round_trips_through_junction_and_parser():
    junction = get_junction(6)
    policy_id = junction.policy_id("right")
    assert policy_id == "zone6-right"
    assert parse_policy_id(policy_id) == (6, "right")


def test_parse_policy_id_rejects_malformed_input():
    with pytest.raises(ValueError):
        parse_policy_id("not-a-policy-id")


def test_option_for_policy_id_resolves_systemic_flag():
    # zone 1 right (โซลาร์ฟาร์ม) is the systemic choice; left (ถ่านหิน) is not
    assert option_for_policy_id("zone1-right").systemic is True
    assert option_for_policy_id("zone1-left").systemic is False


def test_zone_10_is_the_tipping_point_high_stakes_pair():
    junction = get_junction(10)
    assert junction.category == "solution"
    assert junction.left.meter_deltas["capitalist_anger"] == 50
    assert junction.right.meter_deltas["heat"] == 50
