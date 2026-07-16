"""Application ports shared by gameplay and local infrastructure adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.state import GameOverReason, RunState


@dataclass(frozen=True)
class TerminalResult:
    run_id: str
    state: RunState
    reason: GameOverReason | None
    distance_m: int
    gems: int
    duration_s: float


class CompletedRunRepository(Protocol):
    def last_player_name(self) -> str: ...

    def save_completed_run(self, player_name: str, result: TerminalResult) -> None: ...
