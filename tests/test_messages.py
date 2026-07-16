from core.messages import death_cause_text, game_over_reason_text
from core.state import DeathCause, GameOverReason


def test_every_death_cause_has_player_facing_text():
    for cause in DeathCause:
        assert death_cause_text(cause)


def test_every_game_over_reason_has_player_facing_text():
    for reason in GameOverReason:
        assert game_over_reason_text(reason)
