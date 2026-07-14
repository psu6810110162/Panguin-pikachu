"""Contract guard: policy_id ที่ producer ปล่อย ↔ ที่ consumer parse ต้องเป็นฟังก์ชันผกผันกัน.

นี่คือ seam ระหว่างเลน producer (core/interaction.py -> PolicyChoiceEvent.policy_id) กับ
เลน consumer (core/scoring/stealth.py, dag.py -> parse_policy_id/option_for_policy_id).
ถ้า producer ปล่อย "left"/"right" ดิบ (บั๊กเดิมของ PR #61) parse_policy_id จะ raise
ValueError -> Stealth Assessment/DAG ตายเงียบทั้ง feature. เทสต์นี้ตรึง invariant ระดับ
dataset ให้ CI จับก่อน merge — คล้าย tests/test_no_kivy_in_core.py ที่กันชั้น core พึ่ง Kivy
"""

import pytest

from core.junction_data import (
    Side,
    all_junctions,
    option_for_policy_id,
    parse_policy_id,
)

_SIDES: tuple[Side, ...] = ("left", "right")


def test_policy_id_is_the_inverse_of_parse_policy_id_for_every_junction() -> None:
    """Junction.policy_id (producer) กับ parse_policy_id (consumer) ต้องผกผันกันทุกกรณี"""
    for junction in all_junctions():
        for side in _SIDES:
            assert parse_policy_id(junction.policy_id(side)) == (junction.zone, side)


def test_option_for_policy_id_resolves_every_emitted_policy_id() -> None:
    """policy_id ที่ปล่อยออกต้อง resolve กลับไปที่ JunctionOption เดิมได้เป๊ะ (ไม่ raise/ไม่หลง)"""
    for junction in all_junctions():
        for side in _SIDES:
            assert option_for_policy_id(junction.policy_id(side)) is junction.option(side)


def test_policy_id_uses_canonical_zone_prefix_format() -> None:
    """รูปแบบ canonical เดียวที่ทั้งระบบยอมรับคือ "zone{N}-{side}" — ล็อกไว้กัน drift"""
    for junction in all_junctions():
        for side in _SIDES:
            assert junction.policy_id(side) == f"zone{junction.zone}-{side}"


@pytest.mark.parametrize("raw", ["left", "right", "", "zone-left", "zoneX-left", "zone1-up"])
def test_raw_or_malformed_policy_id_is_rejected_by_parser(raw: str) -> None:
    """ค่าดิบ/ผิดรูป (เช่นที่บั๊กเดิมปล่อยออกมา) ต้องถูก parse_policy_id ปฏิเสธเสมอ"""
    with pytest.raises(ValueError):
        parse_policy_id(raw)
