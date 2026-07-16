"""Pure gameplay application boundary and immutable presentation snapshot.

This is the first extraction seam from the legacy Kivy screen. New gameplay
mutations belong here; the screen migration can proceed incrementally while the
frozen snapshot contract remains testable without Kivy.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from core.interaction import YJunctionInteraction
from core.items import Inventory, ItemType
from core.session import GameSession
from core.state import DecisionPhase, GameOverReason, RunMetrics, RunState
from game.ports import TerminalResult

Side = Literal["left", "right"]

DEFAULT_DIFFICULTY: dict[str, Any] = {
    "meters": {
        "start_heat": 50.0,
        "start_capitalist_anger": 50.0,
        "max": 100.0,
        "min": 0.0,
        "game_over_at": 100.0,
    },
    "hearts": {"start": 5, "cap": 5, "respawn_seconds": 3.0, "invincible_seconds": 3.0},
    "eco_seed": {"heat_reduction": -10.0},
}


class GridPort(Protocol):
    def reset(self) -> None: ...

    def get_distance_m(self) -> int: ...


class _HeadlessGrid:
    """Small deterministic test adapter; Kivy screen injects the real grid."""

    def __init__(self) -> None:
        self.forward_tiles = 0

    def reset(self) -> None:
        self.forward_tiles = 0

    def step_forward(self) -> None:
        self.forward_tiles += 1

    def get_distance_m(self) -> int:
        return self.forward_tiles * 10


@dataclass(frozen=True)
class GameplayViewState:
    run_state: RunState
    decision_phase: DecisionPhase | None
    distance_m: int
    gems: int
    hearts: int
    heat: float
    anger: float
    inventory: tuple[str, ...]
    junction_title: str | None = None
    left_choice: str | None = None
    right_choice: str | None = None
    countdown_s: float | None = None
    boss_wave: int | None = None
    boss_armor: int | None = None
    overlay: str | None = None
    feedback: str | None = None
    terminal_reason: GameOverReason | None = None
    recoverable_error: str | None = None


class GameplayController:
    """Own the mutable objects that together form one local Game Run."""

    def __init__(
        self,
        *,
        grid: GridPort | None = None,
        difficulty: dict[str, Any] | None = None,
        on_game_over: Callable[[], None] | None = None,
    ) -> None:
        self._on_game_over = on_game_over
        self._difficulty = difficulty or DEFAULT_DIFFICULTY
        self.grid: GridPort = grid or _HeadlessGrid()
        self.session = GameSession()
        self.metrics = RunMetrics(on_game_over=on_game_over, difficulty=self._difficulty)
        self.inventory = Inventory()
        self.interaction = YJunctionInteraction(self.metrics, self.session)
        self.gems = 0
        self.decision_phase: DecisionPhase | None = None
        self.paused = False
        self._terminal: TerminalResult | None = None
        self._recoverable_error: str | None = None
        self.start_run()

    def start_run(self) -> GameplayViewState:
        self.grid.reset()
        self.session = GameSession()
        self.metrics = RunMetrics(
            on_game_over=self._on_game_over,
            difficulty=self._difficulty,
        )
        self.inventory = Inventory()
        self.interaction = YJunctionInteraction(self.metrics, self.session)
        self.gems = 0
        self.decision_phase = None
        self.paused = False
        self._terminal = None
        self._recoverable_error = None
        self.session.start()
        return self.view_state()

    def restart(self) -> GameplayViewState:
        return self.start_run()

    def tick(self, dt: float) -> GameplayViewState:
        if dt < 0:
            raise ValueError("dt must be non-negative")
        if not self.paused:
            self.metrics.tick_grace(dt)
        return self.view_state()

    def move(self, side: Side) -> Side:
        if side not in ("left", "right"):
            raise ValueError(f"unsupported side: {side}")
        return side

    def use_eco_seed(self) -> bool:
        if not self.inventory.use_item(ItemType.ECO_SEED):
            return False
        effect = self._difficulty.get("eco_seed", {})
        self.metrics.update_meters(float(effect.get("heat_reduction", 0.0)), 0.0)
        return True

    def pause(self) -> GameplayViewState:
        self.paused = True
        return self.view_state()

    def resume(self) -> GameplayViewState:
        self.paused = False
        return self.view_state()

    def finish(self, reason: GameOverReason | None = None) -> TerminalResult:
        if self.session.state is RunState.BOSS:
            self.session.finish()
        self._terminal = TerminalResult(
            run_id=self.session.run_record.run_id,
            state=self.session.state,
            reason=reason,
            distance_m=self.grid.get_distance_m(),
            gems=self.gems,
            duration_s=self.session.elapsed(),
        )
        return self._terminal

    def take_terminal_result(self) -> TerminalResult | None:
        terminal, self._terminal = self._terminal, None
        return terminal

    def set_recoverable_error(self, notice: str | None) -> GameplayViewState:
        self._recoverable_error = notice
        return self.view_state()

    def view_state(self) -> GameplayViewState:
        return GameplayViewState(
            run_state=self.session.state,
            decision_phase=self.decision_phase,
            distance_m=self.grid.get_distance_m(),
            gems=self.gems,
            hearts=self.metrics.hearts,
            heat=self.metrics.heat_meter,
            anger=self.metrics.capitalist_anger,
            inventory=tuple(item.value for item in self.inventory.get_items()),
            terminal_reason=self.metrics.game_over_reason,
            recoverable_error=self._recoverable_error,
        )
