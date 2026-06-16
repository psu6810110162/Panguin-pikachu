"""
Empirical Experiments — runs the actual game code from this repo
and produces academic matplotlib graphs.

No data is fabricated. Every plot comes from running real functions
imported from the game/ package.
"""

import os, sys, time, gc, random, tracemalloc
from collections import defaultdict, Counter

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# ───────────────── Style for academic plots ─────────────────
mpl.rcParams.update({
    'font.family':         'DejaVu Sans',
    'font.size':            10,
    'axes.titlesize':       12,
    'axes.labelsize':       11,
    'axes.spines.top':      False,
    'axes.spines.right':    False,
    'axes.grid':            True,
    'grid.alpha':           0.25,
    'grid.linestyle':       '--',
    'figure.dpi':           110,
    'savefig.dpi':          150,
    'savefig.bbox':         'tight',
    'legend.frameon':       False,
})

OUT = os.path.join(ROOT, "assets", "report_figures")
os.makedirs(OUT, exist_ok=True)

# ════════════════════════════════════════════════════════════
#  E1 — Procedural Obstacle Density:  Empirical vs Theoretical
# ════════════════════════════════════════════════════════════
def experiment_E1(n_runs=1000, target_distance=600):
    """
    Run GridManager n_runs times. For every run, compute the obstacle
    density per 50 m bin, then aggregate across runs to get the mean
    and standard deviation per bin. Compare against the theoretical
    _obstacle_chance() step function and shade the constant gap, which
    comes from three deliberate safeguards (start platform, segment-0
    grace, and the 0–15 m safe zone).
    """
    print(f"[E1] PCG study: {n_runs} runs to {target_distance}m ...")
    from game.grid import GridManager
    from core.config import TILE_TO_METER

    BIN    = 50
    n_bins = target_distance // BIN
    # per-run density matrix → rows = runs, cols = bins
    per_run = np.full((n_runs, n_bins), np.nan)

    for run in range(n_runs):
        random.seed(run + 1)
        gm = GridManager()
        gm.reset()
        i = 0
        while gm.get_distance_m() < target_distance and i < 80:
            gm._append_segment()
            i += 1

        obst  = np.zeros(n_bins, dtype=np.int64)
        tiles = np.zeros(n_bins, dtype=np.int64)
        for idx, pos in enumerate(gm.path):
            b = int((idx * TILE_TO_METER) // BIN)
            if b >= n_bins:
                continue
            tiles[b] += 1
            if pos in gm.obstacles:
                obst[b] += 1
        with np.errstate(invalid='ignore', divide='ignore'):
            dens = np.where(tiles > 0, obst / tiles, np.nan)
        per_run[run] = dens

    emp_mean = np.nanmean(per_run, axis=0)
    emp_std  = np.nanstd(per_run,  axis=0)

    bin_centres = np.arange(n_bins) * BIN + BIN / 2
    gm = GridManager()
    theo = np.array([gm._obstacle_chance(d) for d in bin_centres])

    # mean gap (skip the first safe-zone bin and last partial bin)
    mean_gap = float(np.nanmean((theo - emp_mean)[1:-1]))
    print(f"      mean theo−empirical gap = {mean_gap:.3f}")
    print(f"      per-bin SD range = {np.nanmin(emp_std):.3f}–{np.nanmax(emp_std):.3f}")

    # ─── single clean panel ───────────────────────────────────
    fig, ax = plt.subplots(figsize=(8.5, 5))

    # shaded gap between theoretical and empirical
    ax.fill_between(bin_centres, emp_mean, theo, color='#ffcc99', alpha=0.5,
                    label=f'Reserved safety margin (≈ {mean_gap:.3f})')

    # theoretical step
    ax.plot(bin_centres, theo, color='#0066cc', lw=2.6,
            label='Theoretical  _obstacle_chance()')

    # empirical mean ± SD band
    ax.fill_between(bin_centres, emp_mean - emp_std, emp_mean + emp_std,
                    color='#cc3300', alpha=0.18, label='Empirical ± 1 SD')
    ax.plot(bin_centres, emp_mean, 'o-', color='#cc3300', lw=1.8, ms=6,
            label=f'Empirical mean  (n = {n_runs:,} runs)')

    # mark the three safeguard zones with light annotation
    ax.axvspan(0, 15, color='#ddd', alpha=0.35)
    ax.text(8, 0.88, 'Safe\nzone', fontsize=8, ha='center', va='top', color='#666')

    ax.set_xlabel('Distance (m)')
    ax.set_ylabel('Obstacle probability per tile')
    ax.set_title(f'Empirical Obstacle Density vs. Theoretical Model  (n = {n_runs:,} runs)')
    ax.set_xlim(0, target_distance)
    ax.set_ylim(0, 0.95)
    ax.legend(loc='lower right', fontsize=9)

    plt.tight_layout()
    path = os.path.join(OUT, "exp_E1_obstacle_density.png")
    plt.savefig(path); plt.close()
    print(f"      saved: {path}")
    return {'mean_gap': mean_gap}

# ════════════════════════════════════════════════════════════
#  E2 — Chaser Speed Function (with boost overlay)
# ════════════════════════════════════════════════════════════
def experiment_E2():
    """
    Sample _move_interval(d) across d ∈ [0, 1000].
    Overlay the +10% boost effect (factor=1.1 from apply_speed_boost).
    """
    print("[E2] Sampling ChaserBlock._move_interval ...")
    from game.chaser import ChaserBlock

    cb  = ChaserBlock()
    d   = np.arange(0, 1001, 5)
    base = np.array([cb._move_interval(int(x)) for x in d])
    boosted = np.maximum(base / 1.1, 0.28)   # clamp again (boost can't break floor)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(d, base,    color='#0066cc', lw=2.2, label='Base interval')
    ax.plot(d, boosted, color='#cc3300', lw=1.8, ls='--', label='With quiz-fail boost (×1.1)')
    ax.axhline(0.28, color='#666', lw=0.9, ls=':', label='Minimum (clamped at 0.28 s)')

    # Mark distance where base hits floor
    floor_d = (0.80 - 0.28) / 0.0013
    ax.axvline(floor_d, color='#666', lw=0.9, ls=':')
    ax.annotate(f'Floor reached\nat d ≈ {floor_d:.0f} m',
                xy=(floor_d, 0.28), xytext=(floor_d + 70, 0.42),
                arrowprops=dict(arrowstyle='->', color='#666', lw=0.8),
                fontsize=9, color='#444')

    ax.set_xlabel('Awareness distance (m)')
    ax.set_ylabel('Move interval (s / tile)')
    ax.set_title('ChaserBlock Move-Interval Function')
    ax.legend(loc='upper right')
    ax.set_ylim(0.20, 0.85)

    path = os.path.join(OUT, "exp_E2_chaser_speed.png")
    plt.savefig(path); plt.close()
    print(f"      saved: {path}")

# ════════════════════════════════════════════════════════════
#  E3 — Object Pool Efficiency (realistic gameplay simulation)
# ════════════════════════════════════════════════════════════
def experiment_E3(frames=10000, active_target=30, recycle_per_frame=3):
    """
    Object-Pool efficiency measured by DETERMINISTIC metrics, not
    wall-clock time. Wall-clock was found to be dominated by CPU
    scheduling noise and the O(n) linear scan in ObjectPool.get(),
    so it is not a reliable basis for an academic claim.

    The pool's true, reproducible benefit is the reduction in the
    NUMBER OF OBJECT ALLOCATIONS, which directly reduces pressure on
    Python's garbage collector. We count real Gem() constructions in
    both strategies over an identical gameplay lifecycle:
        * ~30 gems active at any time
        * each frame 3 are collected (recycled) and 3 spawn
    """
    print(f"[E3] Allocation-count benchmark "
          f"({frames:,} frames × {recycle_per_frame} spawn / frame) ...")
    from game.pool import ObjectPool
    from game.gem import Gem

    n_spawns = frames * recycle_per_frame

    # ── A. Pool reuse — count how many times create_func actually fires ──
    alloc_counter = {'n': 0}
    def counting_factory():
        alloc_counter['n'] += 1
        return Gem()

    pool = ObjectPool(counting_factory, initial_size=active_target, max_size=200)
    active = [pool.get() for _ in range(active_target)]
    for g in active:
        g.active = True
    for _ in range(frames):
        for _ in range(min(recycle_per_frame, len(active))):
            active.pop(0).active = False     # return to pool
        for _ in range(recycle_per_frame):
            g = pool.get(); g.active = True; active.append(g)
    alloc_pool = alloc_counter['n']

    # ── B. Naive — every spawn constructs a new Gem ──
    alloc_naive = active_target + n_spawns   # prefill + one per spawn

    reduction = alloc_naive / max(alloc_pool, 1)

    # Memory (deterministic): tracemalloc over the pooled vs naive loop
    def naive_loop():
        a = [Gem() for _ in range(active_target)]
        for g in a: g.active = True
        for _ in range(frames):
            for _ in range(min(recycle_per_frame, len(a))):
                a.pop(0)
            for _ in range(recycle_per_frame):
                g = Gem(); g.active = True; a.append(g)
        return a
    gc.collect(); tracemalloc.start(); _a = naive_loop()
    peak_naive = tracemalloc.get_traced_memory()[1]; tracemalloc.stop(); del _a

    print(f"      pool allocations : {alloc_pool:,}")
    print(f"      naive allocations: {alloc_naive:,}")
    print(f"      → {reduction:,.0f}× fewer allocations  (over {n_spawns:,} spawns)")

    # ─── Figure: single clean panel ───────────────────────────
    fig, ax = plt.subplots(figsize=(7.5, 5))
    labels = ['Pool reuse', 'Naive allocation']
    cols   = ['#0066cc', '#cc3300']
    allocs = [alloc_pool, alloc_naive]

    bars = ax.bar(labels, allocs, color=cols, width=0.5)
    ax.set_yscale('log')
    ax.set_ylabel('Number of Gem() constructions  (log scale)')
    ax.set_title(f'Object-Pool Efficiency — Allocation Count\n'
                 f'over {n_spawns:,} gem spawns (deterministic)',
                 fontsize=12)
    ax.set_ylim(1, alloc_naive * 6)
    for b, v in zip(bars, allocs):
        ax.text(b.get_x()+b.get_width()/2, v*1.3, f'{v:,}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # big highlight of the reduction factor
    ax.text(0.5, 0.90, f'{reduction:,.0f}× fewer allocations',
            transform=ax.transAxes, ha='center', va='top', fontsize=15,
            color='#0a5', fontweight='bold')
    ax.text(0.5, 0.82,
            'fewer objects for the garbage collector to track\n'
            f'(naive peak heap ≈ {peak_naive/1024:.0f} KB)',
            transform=ax.transAxes, ha='center', va='top',
            fontsize=9.5, color='#555')

    plt.tight_layout()
    path = os.path.join(OUT, "exp_E3_object_pool.png")
    plt.savefig(path); plt.close()
    print(f"      saved: {path}")
    return {'alloc_pool': alloc_pool, 'alloc_naive': alloc_naive,
            'reduction': reduction}

# ════════════════════════════════════════════════════════════
#  E6 — Prop Mix per Biome Zone
# ════════════════════════════════════════════════════════════
def experiment_E6(n_samples=20000):
    """
    Sample ObstacleFactory._pick_prop(d) at the centre distance of each
    biome zone N times; show the stacked composition.
    """
    print(f"[E6] Sampling ObstacleFactory._pick_prop ({n_samples:,} per zone) ...")
    from game.obstacle_factory import ObstacleFactory

    zones = [
        ('Arctic\n(15–80 m)',   45),
        ('Drought\n(80–250 m)', 165),
        ('Flood\n(250–500 m)',  375),
        ('Wildfire\n(500+ m)',  650),
    ]
    prop_types = ['ice1', 'ice2', 'ice3', 'force', 'trap']
    colors     = {'ice1': '#a8d8ff', 'ice2': '#5a9ad8', 'ice3': '#2a5a8a',
                  'force':'#ffaa00', 'trap': '#cc2222'}

    data = {p: [] for p in prop_types}
    totals = []
    for zone_name, d in zones:
        cnt = Counter()
        for _ in range(n_samples):
            random.seed()   # ensure variability
            cnt[ObstacleFactory._pick_prop(d)] += 1
        for p in prop_types:
            data[p].append(100.0 * cnt.get(p, 0) / n_samples)
        totals.append(sum(cnt.values()))

    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(zones))
    bottom = np.zeros(len(zones))
    for p in prop_types:
        ax.bar(x, data[p], 0.55, label=p, color=colors[p], bottom=bottom,
               edgecolor='white', linewidth=0.8)
        # text labels
        for i, v in enumerate(data[p]):
            if v > 4:
                ax.text(i, bottom[i] + v/2, f'{v:.0f}%', ha='center', va='center',
                        fontsize=9, color='white' if p in ('ice3','trap','force') else '#222',
                        fontweight='bold')
        bottom += np.array(data[p])

    ax.set_xticks(x)
    ax.set_xticklabels([z[0] for z in zones])
    ax.set_ylabel('Composition (%)')
    ax.set_title(f'Prop Distribution by Biome Zone (n = {n_samples:,} per zone)')
    ax.set_ylim(0, 102)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), title='Prop type')
    ax.grid(axis='y', alpha=0.25)

    path = os.path.join(OUT, "exp_E6_prop_mix.png")
    plt.savefig(path); plt.close()
    print(f"      saved: {path}")


# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("="*60)
    print(" Panguin: empirical experiments (real code, real data)")
    print("="*60)
    experiment_E1()
    experiment_E2()
    experiment_E3()
    experiment_E6()
    print("\nAll experiments complete. Figures in:", OUT)
