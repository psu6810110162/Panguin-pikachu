from core.events import CheckpointReachedEvent, MissionCompleteEvent, QuizAnswerEvent
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


def test_evaluate_computes_distance_from_the_last_event():
    record = _record_with_representative_events()
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
