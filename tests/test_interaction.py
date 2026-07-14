"""YJunctionInteraction — Y-Junction input -> Dual-Meter + PolicyChoiceEvent (D1-A3).

จุดสำคัญที่ตรึงไว้: policy_id ที่ส่งเข้า GameSession ต้องเป็น canonical form
"zone{N}-{side}" (core.junction_data.Junction.policy_id) ไม่ใช่ "left"/"right" ดิบ —
ฝั่ง consumer (core/scoring/stealth.py, dag.py) parse ด้วย parse_policy_id ซึ่ง raise
ValueError ถ้าได้ค่าดิบ ทำให้ Stealth Assessment/DAG ตายเงียบทั้ง feature
"""

import pytest

from core.interaction import YJunctionInteraction
from core.junction_data import all_junctions, get_junction, parse_policy_id
from core.state import RunMetrics


class _RecordingSession:
    """fake GameSession ที่จำ kwargs ของ policy_choice ล่าสุด (มีเมธอดครบ -> hasattr ผ่าน)"""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def policy_choice(
        self,
        *,
        checkpoint_index: int,
        policy_id: str,
        meter_deltas: dict[str, float],
        distance_m: int,
    ) -> None:
        self.calls.append(
            {
                "checkpoint_index": checkpoint_index,
                "policy_id": policy_id,
                "meter_deltas": meter_deltas,
                "distance_m": distance_m,
            }
        )


def _interaction() -> tuple[YJunctionInteraction, _RecordingSession]:
    session = _RecordingSession()
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    return YJunctionInteraction(metrics, session), session


@pytest.mark.parametrize("side", ["left", "right"])
def test_handle_choice_emits_canonical_policy_id(side: str) -> None:
    interaction, session = _interaction()
    junction = get_junction(1)

    interaction.handle_choice(junction, side)

    assert len(session.calls) == 1
    policy_id = session.calls[0]["policy_id"]
    assert policy_id == f"zone1-{side}"
    # ต้อง round-trip ผ่าน consumer contract ได้จริง (ไม่ raise)
    assert parse_policy_id(str(policy_id)) == (1, side)


def test_emitted_policy_id_is_accepted_by_every_junction() -> None:
    """ทุก junction × ทั้งสองข้าง: policy_id ที่ปล่อยออกต้อง parse ได้ ไม่มีตัวไหน raise"""
    for junction in all_junctions():
        for side in ("left", "right"):
            interaction, session = _interaction()
            interaction.handle_choice(junction, side)
            policy_id = str(session.calls[0]["policy_id"])
            assert parse_policy_id(policy_id) == (junction.zone, side)


def test_handle_choice_updates_meters_from_selected_option() -> None:
    interaction, session = _interaction()
    junction = get_junction(1)
    expected = junction.left.meter_deltas

    interaction.handle_choice(junction, "left")

    assert interaction.run_metrics.heat_meter == 50.0 + expected.get("heat", 0.0)
    assert interaction.run_metrics.capitalist_anger == 50.0 + expected.get("capitalist_anger", 0.0)
    assert session.calls[0]["meter_deltas"] == dict(expected)


def test_handle_choice_rejects_invalid_side() -> None:
    interaction, _ = _interaction()
    with pytest.raises(ValueError):
        interaction.handle_choice(get_junction(1), "up")
