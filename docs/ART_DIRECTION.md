# Penguin Dash — Art Direction v1

## Intent

Keep every screen in one visual language: **crisp 16-bit pixel art, isometric ice
path, deep navy space, cyan/violet technology, and restrained eco-green accents**.
The player must remain readable at the real gameplay scale; art is subordinate to
movement, questions, and feedback.

## Visual pillars

1. **Readable first** — the playfield centre stays low contrast and uncluttered;
   the penguin, path, prompt card, and hazards use the strongest contrast.
2. **Cool-to-hot progression** — early running uses navy/cyan. Distance and Heat
   may add muted amber/smog tints, but never reduce text or path readability.
3. **One silhouette** — the canonical penguin keeps the same navy body, cyan visor,
   violet pack, orange beak/feet, and lime eco badge in every pose and skin.
4. **Pixel discipline** — hard pixel clusters, limited palette, no smooth vector
   gradients, no photographic textures, no text baked into world art.
5. **World has two layers** — a quiet presentation background behind the simulated
   path, then gameplay objects/UI above it. Decision pauses freeze simulation but
   leave background particles/animation alive.

## First generated review set

These are review assets, not yet wired as the final runtime sprites:

- [`gameplay_background_v1.png`](../assets/generated/background/gameplay_background_v1.png)
  — 16:9 navy starfield with icy edge silhouettes and a quiet centre.
- [`penguin_sheet_v1.png`](../assets/generated/character/penguin_sheet_v1.png)
  — 8-pose canonical character sheet with alpha background.
- [`environment_tiles_v1.png`](../assets/generated/tiles/environment_tiles_v1.png)
  — six environment block variants: cool ice, frozen ice, neon pivot, warning,
  thawed/smog, and boss-safe.
- [`carbon_baron_sheet_v1.png`](../assets/generated/boss/carbon_baron_sheet_v1.png)
  — Carbon Baron in six gameplay states, with heat/pulse colors tied to the three
  boss waves and shutdown.
- [`penguin_guide_drone_v1.png`](../assets/generated/characters/penguin_guide_drone_v1.png)
  — P.E.N.G.U.I.N. guide drone with idle, pointing, warning, and report poses.

The source chroma-key image is retained as
`assets/generated/character/penguin_sheet_v1_key.png` for reproducibility; the
runtime should consume the alpha PNG after the sheet is sliced and validated.

## Asset production order

### Phase A — lock the language

- Approve background mood and canonical penguin silhouette.
- Slice the character sheet into deterministic frames; do not use generated
  artwork as a live animation source until frame dimensions and anchor points are
  verified.
- Define one palette file/reference: navy, indigo, cyan, violet, amber, lime,
  danger red, and readable white.

### Phase B — gameplay readability

- Replace the current gameplay background with a version that has no baked text.
- Add separate state variants only if needed: normal, high Heat/smog, boss.
- Create tile overlays for neon pivot, safe boss lane, falling warning, and
  scientific-item pickup. These must be silhouettes/accents, not busy scenery.
- Add a single respawn effect: short cyan ring + one-frame fade; never hide the
  penguin after the respawn timer completes.

### Phase C — questions and boss

- Policy card: one dark translucent panel, one question block, two large cyan/
  violet choice lanes, countdown below; no duplicate banner behind it.
- Feedback card: show the selected policy, Heat/Anger deltas, and one short reason
  after the choice. Do not reveal deltas before the choice.
- Boss wall: same card grammar, with only the palette shifting toward amber/smog.

### Phase D — supporting assets

- Carbon Baron silhouette and three wave wall motifs. The boss must visibly react
  to the same Heat state as the meters: red/orange for escalation, violet for the
  final overload, and cold cyan for defeat.
- P.E.N.G.U.I.N. guide drone and one neutral research/briefing character for menu,
  tutorial, and report-card context. Keep them subordinate to the player and boss.
- Three scientific item icons matching the penguin badge language.
- Victory/defeat/Report Card accents, reusing the same border, glow, and palette.

## Runtime integration contract

- Backgrounds are presentation-only and may animate while simulation is paused.
- Character frames are anchored to the tile centre; no random sprite offset is
  allowed during normal running.
- All generated assets get versioned filenames (`*_v1`, `*_v2`) and are reviewed
  before replacing an existing runtime asset.
- Pixel dimensions, frame order, and pivot/anchor coordinates must be recorded in
  an asset manifest before code references them.

## Acceptance checklist for the next review

- At 100% gameplay scale the penguin is visible on every path tile.
- Idle and run frames do not change silhouette height or horizontal anchor.
- The centre of the background remains quiet behind policy text.
- Heat tint changes atmosphere, not legibility.
- Respawn shows the penguin at the checkpoint before input is accepted.
- The same palette reads consistently on Menu, Gameplay, Boss, and Report Card.
