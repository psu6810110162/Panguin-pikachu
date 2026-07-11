from core.events import (
    MissionCompleteEvent,
    PolicyChoiceEvent,
    QuizAnswerEvent,
    RespawnEvent,
)
from core.scoring import rules


def _mission_complete(module_index: int, mission_id: str) -> MissionCompleteEvent:
    return MissionCompleteEvent(
        timestamp=0.0, distance_m=0, module_index=module_index, mission_id=mission_id
    )


def _quiz_answer(correct: bool, phase: str) -> QuizAnswerEvent:
    return QuizAnswerEvent(
        timestamp=0.0,
        distance_m=0,
        quiz_id="q1",
        question_id="1",
        correct=correct,
        phase=phase,
    )


def _policy(meter_deltas: dict[str, float]) -> PolicyChoiceEvent:
    return PolicyChoiceEvent(
        timestamp=0.0,
        distance_m=0,
        checkpoint_index=0,
        policy_id="solar",
        meter_deltas=meter_deltas,
    )


def test_mission_score_counts_completed_missions_out_of_total():
    events = [_mission_complete(0, "a"), _mission_complete(1, "b")]
    assert rules.mission_score(events, total_missions=4) == 50.0


def test_mission_score_is_zero_with_no_missions_defined():
    assert rules.mission_score([], total_missions=0) == 0.0


def test_quiz_score_counts_correct_answers_for_the_given_phase_only():
    events = [
        _quiz_answer(True, "posttest"),
        _quiz_answer(True, "posttest"),
        _quiz_answer(True, "posttest"),
        _quiz_answer(False, "posttest"),
        _quiz_answer(True, "pretest"),  # different phase, must not count
    ]
    assert rules.quiz_score(events, phase="posttest") == 75.0


def test_quiz_score_is_none_when_no_answers_for_that_phase():
    assert rules.quiz_score([], phase="posttest") is None


def test_heat_controlled_pct_applies_policy_deltas_in_order_and_clamps():
    events = [_policy({"heat": -10.0}), _policy({"heat": -5.0})]
    # starting_heat 50 -> 40 -> 35, controlled % = 100 - 35 = 65
    assert rules.heat_controlled_pct(events, starting_heat=50.0) == 65.0


def test_heat_controlled_pct_clamps_to_zero_and_hundred():
    events = [_policy({"heat": -1000.0})]
    assert rules.heat_controlled_pct(events, starting_heat=50.0) == 100.0


def test_policy_score_counts_net_non_positive_choices_as_good():
    events = [_policy({"heat": -5.0}), _policy({"heat": 5.0})]
    assert rules.policy_score(events) == 50.0


def test_policy_score_is_zero_with_no_choices():
    assert rules.policy_score([]) == 0.0


def test_respawn_count_counts_respawn_events():
    events = [
        RespawnEvent(
            timestamp=0.0,
            distance_m=100,
            checkpoint_col=1,
            checkpoint_row=0,
            respawn_count=1,
            score_penalty=0.1,
        ),
        RespawnEvent(
            timestamp=0.0,
            distance_m=200,
            checkpoint_col=2,
            checkpoint_row=0,
            respawn_count=2,
            score_penalty=0.1,
        ),
    ]
    assert rules.respawn_count(events) == 2


def test_environmental_score_is_the_weighted_sum():
    score = rules.environmental_score(
        policy_component=100.0, heat_component=50.0, mission_component=0.0
    )
    assert score == 100.0 * rules.POLICY_WEIGHT + 50.0 * rules.HEAT_WEIGHT
