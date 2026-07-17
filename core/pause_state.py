"""Reason-based pause state for the gameplay simulation.

Multiple independent reasons can each request the simulation to be paused at
the same time — e.g. the player opened the pause menu (``"manual"``) *and*
then opened the How to Play overlay from within it (``"help"``). The overall
paused/running transition must fire exactly once when the reason set becomes
non-empty (0 -> 1 reasons) and exactly once when it becomes empty again
(1 -> 0 reasons), so callers (Clock scheduling, BGM pause/resume) never
double-cancel, double-schedule, or double-toggle audio.

Pure Python, no Kivy import — see AGENTS.md / CLAUDE.md layering rule.
"""

from __future__ import annotations

from collections.abc import Callable


class PauseState:
    def __init__(
        self,
        on_pause: Callable[[], None] | None = None,
        on_resume: Callable[[], None] | None = None,
    ) -> None:
        self._reasons: set[str] = set()
        self.on_pause = on_pause
        self.on_resume = on_resume

    @property
    def is_paused(self) -> bool:
        return bool(self._reasons)

    def reasons(self) -> frozenset[str]:
        return frozenset(self._reasons)

    def has_reason(self, reason: str) -> bool:
        return reason in self._reasons

    def pause(self, reason: str) -> bool:
        """Add ``reason``. Returns True only on the 0 -> 1 transition.

        Adding a reason that is already active is a no-op (idempotent):
        pressing Pause twice, or opening Help twice, must not re-fire
        ``on_pause`` and re-cancel/re-schedule anything.
        """
        was_paused = self.is_paused
        self._reasons.add(reason)
        if not was_paused:
            if self.on_pause:
                self.on_pause()
            return True
        return False

    def resume(self, reason: str) -> bool:
        """Remove ``reason``. Returns True only on the 1 -> 0 transition.

        Removing a reason that was never active, or that still leaves other
        active reasons, is a no-op — ``on_resume`` fires only once every
        active reason has been cleared.
        """
        if reason not in self._reasons:
            return False
        self._reasons.discard(reason)
        if not self.is_paused:
            if self.on_resume:
                self.on_resume()
            return True
        return False

    def clear(self) -> None:
        """Drop every reason silently, without firing ``on_resume``.

        Only for full lifecycle resets (e.g. re-entering the gameplay screen
        for a fresh run) where the caller is about to reinitialize
        pause-dependent state itself — never as a substitute for ``resume``.
        """
        self._reasons.clear()
