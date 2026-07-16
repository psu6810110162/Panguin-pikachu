# ADR-015: Respawn grace is owned by the run metrics lifecycle

Status: Accepted

## Decision

`RunMetrics` owns the complete death and respawn lifecycle. A death request records
the first `DeathCause`, consumes at most one heart, and enters `needs_respawn` when
the run is still alive. `GameplayScreen` owns presentation and checkpoint repair,
then calls `complete_respawn()` exactly once when the respawn timer finishes.

The post-respawn grace period is time-based. It starts in `complete_respawn()` and
expires only through `tick_grace(dt)`; movement input cannot cancel it. While grace
is active, the current tile's trigger is suppressed and repeated fall checks do not
consume another heart. This prevents a repaired checkpoint from immediately killing
the player again and keeps the simulation/rendering boundary from leaking into the
domain model.

Game-over also records a first-write-wins `GameOverReason`. Heat and Anger choose
their reason from the pre-clamp overflow (a tie deterministically chooses Heat),
while heart exhaustion and boss failure provide explicit reasons. Player-facing
explanations are pure functions in `core/messages.py` so presentation cannot mutate
the run record.

## Consequences

- There is one authoritative `is_invincible` value; the view cannot clear it on the
  first movement input.
- Respawn overlays may animate independently, but no gameplay callback may bypass
  `complete_respawn()` or mutate grace fields directly.
- Tests can exercise death, respawn, grace, and terminal reasons without Kivy.
