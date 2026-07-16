# UI Redesign Plan — Penguin Dash

## Problem statement

The current UI mixes gameplay labels, quiz text, boss text, and inventory in one
visual layer. The result is low hierarchy: the player cannot tell what is
actionable, what is feedback, and what is telemetry. The redesign is a state-driven
presentation system, not a collection of larger labels.

## Design principles

1. **One primary question at a time.** During a decision, the card owns the centre
   of the screen; the world dims but remains visible.
2. **Telemetry is peripheral.** Distance, hearts, Heat, Anger, and inventory live
   in one compact HUD rail and never compete with a question.
3. **Action is explicit.** Left/right choices are two equal cards with a clear key
   hint. Feedback appears only after the choice.
4. **Boss has impact, not clutter.** Carbon Baron occupies the top third, the wall
   message occupies the centre, and the two lanes occupy the lower third.
5. **Every state has one composition.** RUNNING, POLICY_DECISION, BOSS_DECISION,
   RESPAWNING, and REPORT each have a deterministic widget visibility contract.

## Target compositions

### Running

- Top rail: pause, distance, hearts, Heat, Anger, inventory.
- Centre: unobstructed isometric path and player.
- Lower corners: left/right controls only.
- Contextual hints: short-lived, low-opacity, never stacked.

### Policy decision

- Background: simulation paused; presentation animation continues.
- Centre card: situation title + two-line context.
- Lower split: LEFT and RIGHT policy cards, each showing the policy label only.
- Bottom: countdown and key hints.
- After choice: a short feedback toast with meter deltas and reason; then return
  to RUNNING.
- The answer input is not a movement input: the penguin stays on the prompt tile;
  movement resumes on the next directional input, and the selected side owns
  the lane when the actual fork split is reached.

### Boss decision

- Top: Carbon Baron silhouette, wave index, armour pips.
- Centre: Problem Wall message.
- Lower split: two item lanes with the actual grid-owned LEFT/RIGHT placement.
- Bottom: countdown; wrong answer feedback uses the same toast component as policy.

### Respawn

- Keep the world visible and frozen.
- Centre: “RESPAWNING” plus a short progress ring.
- Do not show stale player coordinates or a second question card.
- On completion: player appears at checkpoint with a cyan grace ring before input.

## Component contract

Create reusable code-native components before replacing assets:

- `HudRail`: distance/hearts/meter/inventory slots.
- `DecisionCard`: title, situation, choice cards, countdown.
- `FeedbackToast`: selected option, Heat/Anger delta, one explanation line.
- `BossBanner`: boss name, wave, armour, state color.
- `StateOverlay`: respawn, game-over, victory, report transition.

Each component receives domain data and exposes no gameplay mutations. The screen
controller owns state transitions; widgets only render and emit a user intent.

## Color/state mapping

| State | Primary | Secondary | Meaning |
|---|---|---|---|
| Running | cyan | navy | navigation and safety |
| Policy decision | cyan/violet | white | think and compare |
| High Heat | amber/red | smoke violet | systemic escalation |
| Boss wave | red/orange | charcoal | pressure and misconception |
| Correct/eco | lime/cyan | navy | recovery and evidence |
| Respawn | cyan | dim navy | protected recovery |
| Victory | lime/white | violet | restored system |

## Implementation order

1. Replace duplicated Labels with the five components while keeping current domain
   events and state transitions unchanged.
2. Add a single layout/visibility table keyed by `DecisionPhase` and `RunState`.
3. Wire the generated player/boss/tile review assets only after their frame sizes,
   anchors, and crop contracts are fixed.
4. Add screenshot regression checks for running, policy decision, boss wave 1,
   respawn, and report card at 16:9.

## Acceptance criteria

- No overlapping question/banner text at any state.
- The player can identify the next action within one second without reading the
  entire HUD.
- Text remains readable over both cool and high-Heat backgrounds.
- Boss, player, tile, and UI use the same navy/cyan/violet/amber language.
- UI changes do not mutate session, metrics, inventory, or grid ownership.
