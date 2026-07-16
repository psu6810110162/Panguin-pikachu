from core.events import BossPhaseEvent, GameEvent, PolicyChoiceEvent
from core.scoring import dag


def _policy(policy_id: str) -> PolicyChoiceEvent:
    return PolicyChoiceEvent(
        timestamp=0.0, distance_m=0, checkpoint_index=0, policy_id=policy_id, meter_deltas={}
    )


def _boss(phase: int, outcome: str) -> BossPhaseEvent:
    return BossPhaseEvent(timestamp=0.0, distance_m=1000, phase=phase, outcome=outcome)  # type: ignore[arg-type]


def test_load_graph_data_parses_the_real_balance_file():
    graph = dag.load_graph_data()
    assert len(graph.nodes) == 22
    assert len(graph.edges) == 13
    assert {e.decision for e in graph.edges} == set(range(1, 14))


def test_build_projection_with_no_events_marks_every_edge_unplayed():
    projection = dag.build_projection([])
    assert len(projection.edges) == 13
    assert all(e.status == "unplayed" for e in projection.edges)


def test_build_projection_ignores_malformed_policy_id_without_crashing():
    """server-authoritative: policy_id เสียจาก client ต้องไม่ทำ build_projection ล่ม
    (producer ที่ยัง emit "left"/"right" ก็ไม่ crash) — ถือว่าโซนนั้นยังไม่ถูกเล่น"""
    events: list[GameEvent] = [_policy("right"), _policy("zoneX-left"), _policy("")]
    projection = dag.build_projection(events)
    assert len(projection.edges) == 13
    assert all(e.status == "unplayed" for e in projection.edges)
    assert all(e.tooltip is None for e in projection.edges)
    assert projection.unplayed_count == 13
    assert projection.correct_count == 0
    assert projection.incorrect_count == 0


def test_systemic_run_choice_marks_its_decision_correct_with_no_tooltip():
    events: list[GameEvent] = [_policy("zone1-right")]  # zone1 right is the systemic option
    projection = dag.build_projection(events)

    edge_1 = next(e for e in projection.edges if e.decision == 1)
    assert edge_1.status == "correct"
    assert edge_1.tooltip is None


def test_non_systemic_run_choice_marks_its_decision_incorrect_with_tooltip():
    events: list[GameEvent] = [_policy("zone1-left")]  # zone1 left is not systemic
    projection = dag.build_projection(events)

    edge_1 = next(e for e in projection.edges if e.decision == 1)
    assert edge_1.status == "incorrect"
    assert edge_1.tooltip is not None and len(edge_1.tooltip) > 0


def test_other_run_decisions_stay_unplayed_when_only_one_zone_was_chosen():
    events: list[GameEvent] = [_policy("zone1-right")]
    projection = dag.build_projection(events)

    other_decisions = [e for e in projection.edges if e.decision != 1 and e.phase == "run"]
    assert all(e.status == "unplayed" for e in other_decisions)


def test_boss_wave_correct_maps_to_decision_ten_plus_wave():
    events: list[GameEvent] = [_boss(phase=2, outcome="damage_dealt")]
    projection = dag.build_projection(events)

    edge_12 = next(e for e in projection.edges if e.decision == 12)
    assert edge_12.status == "correct"
    assert edge_12.tooltip is None


def test_boss_wave_wrong_marks_incorrect_with_tooltip():
    events: list[GameEvent] = [_boss(phase=3, outcome="damaged")]
    projection = dag.build_projection(events)

    edge_13 = next(e for e in projection.edges if e.decision == 13)
    assert edge_13.status == "incorrect"
    assert edge_13.tooltip is not None


def test_full_run_of_all_systemic_choices_and_all_correct_boss_waves_is_all_green():
    # ทุกโซนเลือก right ยกเว้นโซนที่ systemic คือ left (2, 7, 8, 10) — ใช้ junction_data ตรวจแทนการเดา
    from core.junction_data import all_junctions

    events: list[GameEvent] = []
    for junction in all_junctions():
        side = "left" if junction.left.systemic else "right"
        events.append(_policy(junction.policy_id(side)))
    events += [_boss(phase=w, outcome="damage_dealt") for w in (1, 2, 3)]

    projection = dag.build_projection(events)
    assert projection.correct_count == 13
    assert projection.incorrect_count == 0
    assert projection.unplayed_count == 0


def test_projection_is_deterministic_across_repeated_calls():
    events: list[GameEvent] = [_policy("zone1-right"), _boss(phase=1, outcome="damage_dealt")]
    first = dag.build_projection(events)
    second = dag.build_projection(events)
    assert first == second


def test_to_dict_serializes_edges_and_nodes():
    events: list[GameEvent] = [_policy("zone1-left")]
    payload = dag.build_projection(events).to_dict()

    assert len(payload["nodes"]) == 22
    assert len(payload["edges"]) == 13
    edge_1 = next(e for e in payload["edges"] if e["decision"] == 1)
    assert edge_1["status"] == "incorrect"
    assert edge_1["from"] == "coal_power"
    assert edge_1["to"] == "co2"
    assert isinstance(edge_1["tooltip"], str)
