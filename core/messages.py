"""Pure player-facing explanations for death and game-over transitions."""

from core.state import DeathCause, GameOverReason

_DEATH_MESSAGES = {
    DeathCause.FALL: "ตกนอกเส้นทาง",
    DeathCause.IDLE: "ยืนนิ่งนานเกินไป น้ำแข็งละลาย",
    DeathCause.MELT: "น้ำแข็งใต้เท้าละลายทัน",
}

_GAME_OVER_MESSAGES = {
    GameOverReason.HEARTS: "หัวใจหมด",
    GameOverReason.HEAT: "Heat แตะ 100 — โลกร้อนเกินควบคุม",
    GameOverReason.ANGER: "Anger แตะ 100 — ถูกถอดจากตำแหน่ง",
    GameOverReason.BOSS: "ตอบผิดครบ 3 เวฟ — Carbon Baron ชนะ",
}


def death_cause_text(cause: DeathCause) -> str:
    """Return the explanation shown when the player is respawning."""
    return _DEATH_MESSAGES[cause]


def game_over_reason_text(reason: GameOverReason) -> str:
    """Return the explanation shown on the game-over screen."""
    return _GAME_OVER_MESSAGES[reason]
