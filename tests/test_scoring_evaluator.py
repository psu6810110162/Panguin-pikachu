from core.events import (
    BossPhaseEvent,
    CheckpointReachedEvent,
    MissionCompleteEvent,
    PolicyChoiceEvent,
    QuizAnswerEvent,
)
from core.schema import RunRecord
from core.scoring.evaluator import evaluate


def _record_with_representative_events() -> RunRecord:
    record = RunRecord(run_id="run-1", player_id="player-1")
    record.record(CheckpointReachedEvent(timestamp=0.1, distance_m=100, checkpoint_index=1))
    record.record(
        MissionCompleteEvent(timestamp=0.2, distance_m=300, module_index=0, mission_id="a")
    )
    record.record(
        QuizAnswerEvent(
            timestamp=0.3,
            distance_m=1000,
            quiz_id="q1",
            question_id="1",
            correct=True,
            phase="posttest",
        )
    )
    record.record(CheckpointReachedEvent(timestamp=0.4, distance_m=1000, checkpoint_index=10))
    return record


def test_evaluate_assigns_and_returns_the_same_result():
    record = _record_with_representative_events()

    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)

    assert record.result is result


def test_evaluate_computes_max_distance():
    record = _record_with_representative_events()
    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    assert result.distance_m == 1000


def test_evaluate_computes_max_distance_despite_respawn_regression():
    from core.events import RespawnEvent

    record = _record_with_representative_events()
    record.record(
        RespawnEvent(
            timestamp=0.5,
            distance_m=500,
            checkpoint_col=1,
            checkpoint_row=0,
            respawn_count=1,
            score_penalty=0.1,
        )
    )
    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    assert result.distance_m == 1000


def test_evaluate_computes_hake_gain_from_pretest_posttest():
    record = _record_with_representative_events()
    result = evaluate(record, pretest_pct=50.0, posttest_pct=75.0, total_missions=2)
    assert result.hake_gain == 0.5


def test_evaluate_computes_mission_score():
    record = _record_with_representative_events()
    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    assert result.mission_score == 50.0


def test_evaluate_with_no_events_gives_zero_distance_and_scores():
    record = RunRecord(run_id="run-2", player_id="player-2")
    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=4)
    assert result.distance_m == 0
    assert result.mission_score == 0.0
    assert result.respawn_count == 0
    assert result.net_impact_score == 0.0
    assert result.cognitive_score == 0.0
    assert result.rank is None  # 0.0°C ต่ำกว่า rank ต่ำสุด (A: 0.8-1.2°C)


def test_evaluate_computes_stealth_assessment_fields_from_policy_and_boss_events():
    record = RunRecord(run_id="run-4", player_id="player-4")
    # zone1-right (โซลาร์ฟาร์ม) เป็นตัวเลือก systemic ตาม balance/v1/junctions.json
    record.record(
        PolicyChoiceEvent(
            timestamp=0.1,
            distance_m=100,
            checkpoint_index=1,
            policy_id="zone1-right",
            meter_deltas={"heat": -20, "capitalist_anger": 25},
        )
    )
    record.record(BossPhaseEvent(timestamp=0.2, distance_m=1000, phase=1, outcome="damage_dealt"))

    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)

    assert result.cognitive_score == 0.1  # 1 boss wave ถูก x boss_bonus_per_wave_c (0.1)
    assert result.net_impact_score == 0.2  # systemic 1 ข้อ (0.1) + cognitive (0.1)
    assert result.rank is None  # 0.2°C ยังต่ำกว่า rank ต่ำสุด (A: 0.8-1.2°C)


def test_evaluate_is_deterministic_across_repeated_calls():
    """ตาม ADR-012: event log เดียวกัน -> RunResult เดิม 100% เสมอ (หัวใจของ replay)"""
    record = RunRecord(run_id="run-5", player_id="player-5")
    record.record(
        PolicyChoiceEvent(
            timestamp=0.1,
            distance_m=100,
            checkpoint_index=1,
            policy_id="zone1-right",
            meter_deltas={"heat": -20, "capitalist_anger": 25},
        )
    )

    first = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    second = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    assert first.to_dict() == second.to_dict()


def test_evaluate_quiz_score_averages_only_phases_the_player_has_reached():
    """1 posttest answer (correct) ไม่ควรถูกหารด้วย 3 phase ทั้งที่อีก 2 phase ยังไม่มีข้อมูล
    (mid-run sync ก่อนถึง pretest/boss_debunk ไม่ควรโดนหักคะแนนเหมือนตอบผิดหมด)
    """
    record = _record_with_representative_events()  # มีแค่ posttest 1 ข้อ, ตอบถูก
    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    assert result.quiz_score == 100.0


def test_evaluate_quiz_score_is_zero_when_no_phase_has_any_answer():
    record = RunRecord(run_id="run-3", player_id="player-3")
    result = evaluate(record, pretest_pct=40.0, posttest_pct=90.0, total_missions=2)
    assert result.quiz_score == 0.0
