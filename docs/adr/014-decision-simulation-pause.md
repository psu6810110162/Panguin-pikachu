# ADR-014: Pause simulation, continue presentation

Status: Accepted; respawn-grace clause superseded by [ADR-015](015-respawn-grace-lifecycle.md)

## Decision

Policy and boss decisions enter an explicit presentation phase. During that phase
movement, tile decay, idle timeout, and boss progression are paused. Rendering,
particles, background motion, and UI animation continue.

The decision card waits for its intro period before starting its countdown. A
timeout is recorded as `PolicyChoiceEvent.outcome="timeout"`; it is never encoded
as a fabricated left/right choice. Timeout applies the configured small meter
penalty, does not remove a heart, and contributes no systemic-choice score.

Respawn has a behavioral invariant rather than a UI-only delay. Its lifecycle and
the rule for when protection expires are defined by ADR-015. Simulation remains
paused while the respawn timer runs, while presentation continues.

## Rationale

The game assesses policy reasoning, not reading speed. Freezing only the simulation
keeps the world alive without allowing a hidden timer or falling floor to punish the
player while they read. Explicit timeout data preserves honest learning telemetry.
