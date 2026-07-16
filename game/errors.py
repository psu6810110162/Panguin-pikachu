"""Typed errors crossing the gameplay application boundary."""


class GameError(Exception):
    """Base error with a player-safe message."""


class RecoverableGameError(GameError):
    """The current run can continue after surfacing a notice."""


class FatalStartupError(GameError):
    """Required startup state is invalid; gameplay must not begin."""


class InvariantViolation(GameError):
    """A programming contract was violated and must never be hidden."""
