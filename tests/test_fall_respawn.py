"""Fall-point respawn contract (ADR-016).

GamePlayScreen is a heavy Kivy widget; these tests call unbound methods
against a minimal stand-in so the fall→respawn coordinate path can be
pinned without a Window provider.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from core.state import RunMetrics, RunState
from screens.gameplay import GamePlayScreen


def _fake_screen(*, col: int, row: int, hearts: int = 5):
    metrics = RunMetrics(hearts=hearts)
    session = MagicMock()
    session.state = RunState.RUNNING
    grid = MagicMock()
    grid.get_distance_m.return_value = 42
    grid.path = [(0, 0), (0, 1), (col, row)]
    grid.path_set = {
        (col, row): MagicMock(state="falling", trigger_timer=0, fall_velocity=0, offset_y=0)
    }
    grid.get_path_index.return_value = 2
    grid.trigger_seconds_for_distance.return_value = 2.5

    penguin = SimpleNamespace(col=col, row=row, is_dead=False)
    fake = SimpleNamespace(
        is_respawning=False,
        penguin=penguin,
        metrics=metrics,
        session=session,
        grid=grid,
        last_checkpoint_col=0,
        last_checkpoint_row=0,
        fall_col=0,
        fall_row=0,
        respawn_count=0,
        respawn_grace_active=False,
        path_index=2,
        checkpoint_label=MagicMock(),
        respawn_overlay=MagicMock(),
        hearts_label=MagicMock(),
        heat_bar=MagicMock(),
        anger_bar=MagicMock(),
        _schedule_paused_aware=MagicMock(),
        _refresh_status_hud=lambda: None,
        _respawn_penguin=MagicMock(),
    )
    return fake


def test_handle_fall_stores_fall_point_not_start_checkpoint():
    fake = _fake_screen(col=7, row=11)

    GamePlayScreen._handle_fall(fake)

    assert fake.fall_col == 7
    assert fake.fall_row == 11
    assert fake.penguin.is_dead is True
    assert fake.metrics.hearts == 4
    fake.session.respawn.assert_called_once()
    kwargs = fake.session.respawn.call_args.kwargs
    assert kwargs["checkpoint_col"] == 7
    assert kwargs["checkpoint_row"] == 11
    # Must NOT silently use the start checkpoint.
    assert kwargs["checkpoint_col"] != fake.last_checkpoint_col or fake.last_checkpoint_col == 7


def test_respawn_penguin_places_player_at_fall_point():
    fake = _fake_screen(col=3, row=5)
    fake.fall_col, fake.fall_row = 3, 5
    fake.is_respawning = True
    fake.penguin.is_dead = True
    fake.session.state = RunState.RESPAWNING
    fake.renderer = MagicMock()
    fake.junction_banner = MagicMock()
    fake.respawn_overlay = MagicMock()
    fake._close_decision = MagicMock()
    fake.decision_grace_active = False
    fake.pending_policy_zone = None
    fake.pending_policy_side = None
    fake.active_prompt_zone = None
    fake.metrics.is_invincible = False
    fake.metrics.invincible_seconds = 3.0
    fake.respawn_grace_remaining = 0.0

    GamePlayScreen._respawn_penguin(fake)

    assert fake.penguin.col == 3
    assert fake.penguin.row == 5
    assert fake.penguin.is_dead is False
    fake.grid.repair_path_ahead_of_checkpoint.assert_called()
    args = fake.grid.repair_path_ahead_of_checkpoint.call_args[0]
    assert args[0] == 3 and args[1] == 5
