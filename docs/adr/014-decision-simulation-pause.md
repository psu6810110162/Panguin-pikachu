# ADR-014: Pause simulation, continue presentation

## Decision

Policy and boss decisions enter an explicit presentation phase. During that phase
movement, tile decay, idle timeout, and boss progression are paused. Rendering,
particles, background motion, and UI animation continue.

The decision card waits for its intro period before starting its countdown. A
timeout is recorded as `PolicyChoiceEvent.outcome="timeout"`; it is never encoded
as a fabricated left/right choice. Timeout applies the configured small meter
penalty, does not remove a heart, and contributes no systemic-choice score.

Respawn has a behavioral invariant rather than a UI-only delay: after returning to
the checkpoint, the player cannot die from the same fallen-tile cause until they
move or the configured invincibility grace expires. Simulation remains paused while
the respawn timer runs, while presentation continues.

## Rationale

The game assesses policy reasoning, not reading speed. Freezing only the simulation
keeps the world alive without allowing a hidden timer or falling floor to punish the
player while they read. Explicit timeout data preserves honest learning telemetry.
