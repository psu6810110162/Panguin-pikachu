"""
Generate the two report diagrams that were placeholders:
  - fig_biome_progression.png  (รูปที่ 7.1) — uses real game tiles
  - fig_storyboard_flow.png    (รูปที่ 7.2) — scene flow diagram
"""
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

mpl.rcParams.update({
    'font.family': 'DejaVu Sans',
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILES = os.path.join(ROOT, "assets", "great_melt", "tiles_new")
OUT   = os.path.join(ROOT, "assets", "report_figures")
os.makedirs(OUT, exist_ok=True)

# ════════════════════════════════════════════════════════════
#  รูปที่ 7.1 — Biome Progression  (real tiles)
# ════════════════════════════════════════════════════════════
def biome_progression():
    biomes = [
        ("ice/ice_tile_1.png",           "ARCTIC ICE",  "0–249 m",   "#3a6a9a"),
        ("drought/drought_tile_1.png",   "DROUGHT ZONE","250–549 m", "#a8702a"),
        ("flood/flood_tile_1.png",       "FLOOD SURGE", "550–899 m", "#1a4f72"),
        ("wildfire/wildfire_tile_1.png", "WILDFIRE",    "900+ m",    "#7a2a10"),
    ]

    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 1)
    ax.axis('off')

    for i, (path, name, dist, col) in enumerate(biomes):
        img = mpimg.imread(os.path.join(TILES, path))
        oi = OffsetImage(img, zoom=0.85)
        ab = AnnotationBbox(oi, (i + 0.5, 0.60), frameon=False)
        ax.add_artist(ab)
        # Biome name
        ax.text(i + 0.5, 0.26, name, ha='center', va='center',
                fontsize=12, fontweight='bold', color=col)
        # Distance band
        ax.text(i + 0.5, 0.15, dist, ha='center', va='center',
                fontsize=10, color='#444')
        # Arrow to next
        if i < 3:
            arr = FancyArrowPatch((i + 0.92, 0.60), (i + 1.08, 0.60),
                                  arrowstyle='-|>', mutation_scale=20,
                                  color='#888', lw=2)
            ax.add_artist(arr)

    # Bottom distance axis
    ax.annotate('', xy=(4, 0.04), xytext=(0, 0.04),
                arrowprops=dict(arrowstyle='-|>', color='#333', lw=1.5))
    ax.text(2, -0.02, 'Awareness Index (distance, m)  →',
            ha='center', va='top', fontsize=10, color='#333', style='italic')

    ax.set_title('Biome Progression — environmental crisis sequence',
                 fontsize=13, fontweight='bold', pad=12)

    p = os.path.join(OUT, "fig_biome_progression.png")
    plt.savefig(p, facecolor='white')
    plt.close()
    print("saved:", p)


# ════════════════════════════════════════════════════════════
#  รูปที่ 7.2 — Storyboard Flow Diagram
# ════════════════════════════════════════════════════════════
def storyboard_flow():
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')

    navy   = "#16273f"
    accent = "#2f6f9f"

    # node positions (x, y)
    nodes = [
        ("Main Menu",     2.0, 3.6),
        ("Gameplay",      5.0, 3.6),
        ("Quiz Popup",    8.0, 3.6),
        ("Game Over",     8.0, 1.4),
        ("Climate\nReport", 5.0, 1.4),
        ("Skin Shop",     2.0, 1.4),
    ]
    W, H = 2.0, 1.0
    centers = {}
    for name, x, y in nodes:
        box = FancyBboxPatch((x - W/2, y - H/2), W, H,
                             boxstyle="round,pad=0.08,rounding_size=0.15",
                             linewidth=2, edgecolor=accent, facecolor=navy)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center',
                fontsize=11, fontweight='bold', color='white')
        centers[name] = (x, y)

    def arrow(a, b, label=None, rad=0.0, color=accent, ls='-',
              lx=None, ly=0.22):
        (x1, y1), (x2, y2) = centers[a], centers[b]
        arr = FancyArrowPatch((x1, y1), (x2, y2),
                              connectionstyle=f"arc3,rad={rad}",
                              arrowstyle='-|>', mutation_scale=18,
                              color=color, lw=1.8, linestyle=ls,
                              shrinkA=42, shrinkB=42)
        ax.add_artist(arr)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if lx is not None:
                mx = lx
            ax.text(mx, my + ly, label, ha='center', va='center',
                    fontsize=8.5, color='#555', style='italic')

    # main forward flow
    arrow("Main Menu", "Gameplay",   "start")
    arrow("Gameplay",  "Quiz Popup", "every 50–100 m", ly=-0.30)   # label below
    arrow("Quiz Popup","Gameplay",   "resume", rad=0.45, ly=0.75)  # label high above curve
    arrow("Gameplay",  "Game Over",  "caught / fall", rad=-0.3)
    arrow("Game Over", "Climate\nReport", "review")
    arrow("Climate\nReport", "Skin Shop", "spend gems")
    arrow("Skin Shop", "Main Menu",  "new run")

    # cyclic: any scene can return to Main Menu (dashed)
    arrow("Game Over", "Main Menu", color="#aaa", ls='--', rad=0.55)

    ax.set_title('Storyboard Flow — 6 scenes via Kivy Screen Manager (cyclic)',
                 fontsize=13, fontweight='bold', pad=14, color=navy)

    p = os.path.join(OUT, "fig_storyboard_flow.png")
    plt.savefig(p, facecolor='white')
    plt.close()
    print("saved:", p)


if __name__ == '__main__':
    biome_progression()
    storyboard_flow()
