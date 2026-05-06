from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class BiomeDef:
    id: str
    name: str
    start_dist: int
    tile_paths: List[str]
    tile_tint: Tuple        # (r,g,b,a) — Color multiply for tiles
    atmo_tint: Tuple        # (r,g,b,a) — full-screen atmosphere overlay
    hud_color: Tuple        # (r,g,b,a) — HUD label color
    fork_color: Tuple       # (r,g,b,a) — fork tile highlight
    chaser_glow: Tuple      # (r,g,b) — chaser glow color
    facts: List[str]

BIOMES = [
    BiomeDef(
        id='arctic', name='❄  ARCTIC ICE', start_dist=0,
        tile_paths=[f'assets/great_melt/tiles/ice_tile_{i}.png' for i in range(1,11)],
        tile_tint=(1.0, 1.0, 1.0, 1.0),
        atmo_tint=(0.0, 0.0, 0.0, 0.0),
        hud_color=(0.70, 0.95, 1.0, 1.0),
        fork_color=(1.0, 0.90, 0.40, 1.0),
        chaser_glow=(1.0, 0.12, 0.0),
        facts=[
            "Arctic sea ice declines ~13% per decade.",
            "The Arctic warms 4x faster than the global average.",
            "Emperor penguins may vanish by 2100 without action.",
            "Greenland loses ~280 billion tonnes of ice per year.",
            "Every 0.5C of warming doubles the chance of ice-free summers.",
        ],
    ),
    BiomeDef(
        id='drought', name='🌵  DROUGHT ZONE', start_dist=100,
        tile_paths=[f'assets/great_melt/tiles/drought/drought_tile_{i}.png' for i in range(1,6)],
        tile_tint=(1.0, 0.88, 0.58, 1.0),
        atmo_tint=(0.28, 0.10, 0.0, 0.30),
        hud_color=(1.0, 0.85, 0.35, 1.0),
        fork_color=(1.0, 0.65, 0.10, 1.0),
        chaser_glow=(1.0, 0.45, 0.0),
        facts=[
            "Over 2/3 of the world faces severe water stress by 2040.",
            "Droughts have doubled in frequency since 2000.",
            "1 billion people lack reliable clean water access today.",
            "Soil moisture in drylands has dropped 30% since 1980.",
            "Heat waves now last twice as long as 50 years ago.",
        ],
    ),
    BiomeDef(
        id='flood', name='🌊  FLOOD SURGE', start_dist=250,
        tile_paths=[f'assets/great_melt/tiles/flood/flood_tile_{i}.png' for i in range(1,6)],
        tile_tint=(0.55, 0.90, 1.0, 1.0),
        atmo_tint=(0.0, 0.15, 0.35, 0.32),
        hud_color=(0.50, 1.0, 0.92, 1.0),
        fork_color=(0.20, 0.85, 1.0, 1.0),
        chaser_glow=(0.0, 0.45, 1.0),
        facts=[
            "Sea levels rise ~3.7 mm every year.",
            "Flooding affects 2 billion people annually.",
            "Coastal megacities like Bangkok and Jakarta face submersion.",
            "Extreme rainfall events have tripled since 1980.",
            "Climate floods displace 20 million people per year.",
        ],
    ),
    BiomeDef(
        id='wildfire', name='🔥  WILDFIRE', start_dist=450,
        tile_paths=[f'assets/great_melt/tiles/wildfire/wildfire_tile_{i}.png' for i in range(1,6)],
        tile_tint=(1.0, 0.68, 0.30, 1.0),
        atmo_tint=(0.40, 0.08, 0.0, 0.38),
        hud_color=(1.0, 0.55, 0.15, 1.0),
        fork_color=(1.0, 0.30, 0.0, 1.0),
        chaser_glow=(1.0, 0.20, 0.0),
        facts=[
            "Wildfire seasons are 20% longer than 30 years ago.",
            "Wildfires release more CO2 than most countries combined.",
            "Australia 2019-20 fires burned 18.6 million hectares.",
            "Warmer drier air causes fires to spread 2x faster.",
            "Forest loss from fire is now irreversible in some regions.",
        ],
    ),
]

class BiomeManager:
    def __init__(self):
        self._idx = 0

    def reset(self):
        self._idx = 0

    @property
    def current(self):
        return BIOMES[self._idx]

    def update(self, distance_m):
        """Returns (biome, just_changed). Call every frame."""
        new_idx = 0
        for i, b in enumerate(BIOMES):
            if distance_m >= b.start_dist:
                new_idx = i
        changed = (new_idx != self._idx)
        self._idx = new_idx
        return BIOMES[self._idx], changed
