"""SQLite adapter for the completed Game Run repository port."""

from game.ports import TerminalResult
from infrastructure.database import DatabaseManager


class LocalCompletedRunRepository:
    def __init__(self, database: DatabaseManager | None = None) -> None:
        self._database = database or DatabaseManager()

    def last_player_name(self) -> str:
        return self._database.get_last_player_name()

    def save_completed_run(self, player_name: str, result: TerminalResult) -> None:
        self._database.save_game_session(
            player_name,
            distance=result.distance_m,
            gems=result.gems,
            duration=result.duration_s,
            run_state=result.state.name,
            terminal_reason=result.reason.value if result.reason is not None else None,
        )
