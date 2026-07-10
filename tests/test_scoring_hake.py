from core.scoring.hake import hake_gain


def test_hake_gain_matches_the_standard_formula():
    # (post - pre) / (100 - pre) = (90 - 40) / (100 - 40) = 50/60
    assert hake_gain(40.0, 90.0) == 50 / 60


def test_hake_gain_with_a_clean_round_number():
    assert hake_gain(50.0, 75.0) == 0.5


def test_hake_gain_zero_when_no_improvement():
    assert hake_gain(50.0, 50.0) == 0.0


def test_hake_gain_can_be_negative():
    assert hake_gain(60.0, 40.0) < 0


def test_hake_gain_is_none_when_pretest_is_already_maxed():
    assert hake_gain(100.0, 100.0) is None
