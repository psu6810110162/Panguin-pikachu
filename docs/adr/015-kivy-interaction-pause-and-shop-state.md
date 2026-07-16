# ADR-015: Kivy interaction-layer contract, pause-reason lifecycle, and atomic Shop ownership

**Status:** Accepted

## Context

Three independent bugs traced back to the same class of root cause — state that was
implicit, single-owner, or check-then-act across more than one step:

- Pause/Help buttons in `screens/gameplay.py` were unclickable because a full-screen
  `Widget(opacity=0, disabled=True)` (`decision_dim`) sat above them in the touch tree.
  Kivy dispatches touches to the top-most child first, and `Widget.on_touch_down()`
  returns `True` whenever a `disabled` widget collides with the touch — `opacity=0`
  does not exempt a widget from hit-testing. The same risk existed on every other
  full-screen overlay (`respawn_overlay`, `StateOverlay`, `HowToPlayOverlay`).
- Pause only cancelled the main `Clock` event. BGM and the delayed callbacks driving
  respawn/game-over/report transitions kept running under pause, and closing Help
  always left the game paused regardless of whether it was paused before Help opened.
- Shop's purchase flow was check-balance-then-deduct-then-insert-ownership across
  three separate statements with no transaction boundary, so a fast double-tap (or a
  crash between steps) could double-deduct gems or leave gems deducted with no skin
  granted. `players.equipped_skin` was never read back into `StateManager`, so the
  equipped skin reset to a hardcoded default on every app restart despite already
  having a durable column for it.

## Decision

**Interaction layers.** Every screen with overlays follows a fixed z-order: world
renderer → passive presentation/HUD → interactive controls → modal layer. Passive
full-screen visuals use `ui.components.PassiveOverlay`, which unconditionally returns
`False` from every `on_touch_*` regardless of `disabled`/`opacity`. Anything that must
gate touch when active (`StateOverlay`, `HowToPlayOverlay`) checks an explicit state
flag (`opacity == 0` / `is_open`) inside `on_touch_*` instead of relying on `disabled`
as an implicit hit-test gate. `tests/test_touch_layers.py` pins both contracts.

**Pause lifecycle.** `core/pause_state.py: PauseState` holds a set of pause reasons
(`"manual"`, `"help"`) and only fires `on_pause`/`on_resume` on a 0→1 / 1→0 reason-count
transition — so Pause-then-Help-then-close-Help correctly stays paused (still holds
`"manual"`), and Help-opened-from-HUD-then-closed correctly resumes (drops the only
reason). `GamePlayScreen` schedules delayed respawn/game-over/report transitions
through `_schedule_paused_aware` (ticked from `update`, which itself only runs while
un-paused) instead of `Clock.schedule_once`, so those transitions freeze for exactly as
long as the simulation is paused. `AudioManager.pause_bgm()`/`resume_bgm()` are
idempotent and restore playback position when the audio provider supports seeking.

**Atomic Shop ownership.** `core/shop_catalog.py` loads `balance/v1/shop.json` (skin
id/display name/price/preview asset/default flag) as the single source of catalog
data and exposes a pure state matrix (`resolve_item_state` → `LOCKED | BUY | EQUIP |
EQUIPPED`) that never touches the DB. `DatabaseManager.purchase_skin()` wraps the
recheck-ownership → conditional-balance-deduct → insert-ownership sequence in one
`BEGIN IMMEDIATE` transaction, committing or rolling back as a unit; a repeat call for
an already-owned skin is a no-op success instead of a second deduction. `main.py`
hydrates `StateManager.selected_skin` from `players.equipped_skin` at startup (falling
back to, and persisting, the catalog default if the stored value is empty or refers to
a since-removed skin), so equipping now survives an app restart.

**Responsive breakpoints.** `ui/responsive.py` classifies `Breakpoint` (mobile
portrait/landscape, tablet, desktop) from the *narrow* window axis and derives HUD
scale, HUD width fraction, control size, and safe-area insets from it in one place
(`compute_layout`), so `screens/gameplay.py`, `ui/how_to_play_overlay.py`, and
`screens/shop.py` all reflow from the same numbers instead of each guessing its own
thresholds. `SafeAreaProvider` returns zero insets on desktop/tablet and reads real
Android system-bar/cutout insets via a guarded `pyjnius` bridge, falling back to a
minimum padding on compact breakpoints if the bridge is unavailable.

## Consequences

- Touch-gating is now always an explicit per-widget decision, not an accidental side
  effect of `disabled`; adding a new full-screen overlay must pick `PassiveOverlay` or
  the `StateOverlay`-style explicit gate, there is no third, silently-broken default.
- Every current and future paused-while-delayed transition must go through
  `_schedule_paused_aware`, not `Clock.schedule_once`, or it will silently keep
  running under pause again.
- `purchase_skin`'s atomicity depends on no other code path writing
  `players.gem_balance` or `player_skins` outside a transaction; a future gem-earning
  path must reuse the same commit/rollback discipline, not a fire-and-forget
  `UPDATE ... commit()`.
- `shop.json` is the only place a skin's id, price, or default flag may change; both
  `game/penguin.py`'s `SKIN_ASSETS` keys and `shop.json`'s skin ids must be updated
  together, enforced by `tests/test_shop_catalog.py`.
- Breakpoint thresholds are centralized, so a future screen needing responsive layout
  should consume `ui.responsive.compute_layout`/`grid_columns` rather than
  reintroducing ad hoc pixel-fraction thresholds.
