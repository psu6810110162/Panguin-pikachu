# ADR-016: Fall-point respawn (hearts buy progress)

**Status:** Accepted (supersedes the *respawn location* clause of [ADR-010](010-health-respawn-state-model.md); hearts count, GAME_OVER-at-zero, invincible frames, and `RespawnEvent` schema from ADR-010 remain in force)

## Context

ADR-010 placed fall-respawn at the **last 100m checkpoint**. In practice `GamePlayScreen` only wrote `last_checkpoint_*` at run start and when `forward_tiles % 100 == 0` on a centreline tile — so any fall before the first 100m milestone (or on a fork lane with no centreline index) teleported the player back to `path[0]`. That made hearts feel useless: dying early always meant restarting the map.

Players and GDD copy both expect **"กลับจุดที่ตก"** when hearts remain: lose one heart, repair the local path, continue from that tile so distance and map generation keep progressing.

## Decision

- On fall, capture `(fall_col, fall_row)` from the penguin's position *before* marking dead.
- `_respawn_penguin` places the player at `(fall_col, fall_row)`, repairs path ahead of that cell, and restores the fall tile itself if it was destroyed or off-path (fallback: last known centreline `path_index`).
- The 100m "checkpoint reached" toast / `session.checkpoint_reached` event remains a **progress milestone only** — it is no longer the respawn coordinate.
- `RespawnEvent.checkpoint_col/row` keep their schema names for compatibility but now carry the **fall-point** coordinates the player resumes at.
- Hearts rules from ADR-010 are unchanged: start 5, fall −1 + respawn while hearts > 0, hearts = 0 or meter ≥ game_over_at → permanent GAME_OVER; invincible grace after respawn.

## Consequences

- Hearts buy continued progress instead of a free restart — correct stakes for Stealth Assessment.
- Early-run falls no longer soft-reset the endless runner.
- Telemetry that assumed `RespawnEvent` coordinates equalled a 100m platform must treat them as fall points (distance_m on the event is still authoritative for how far the run had gone).
- Revisit only if classroom mode needs ADR-002-style "everyone finishes together" and wants forced checkpoint warps again — that would be a new ADR, not an edit to this one.
