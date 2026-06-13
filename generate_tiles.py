#!/usr/bin/env python3
"""
Panguin: The Great Melt — Enhanced Asset Generator v2
Larger tiles (200px) with rich surface detail + 4 Biome backgrounds.
100% original programmatic art — no copyright.
"""

from PIL import Image, ImageDraw, ImageFilter
import os, random, math

random.seed(42)

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "assets", "great_melt")

# ═══════════════════════════════════════════════════════════════
# TILE CONFIG  (larger than v1 — was 130×99, now 200×155)
# ═══════════════════════════════════════════════════════════════
W    = 200
SIDE = 55
TH   = W // 4   # = 50
H    = TH * 2 + SIDE  # = 155

tt = (W // 2,     0)
tr = (W - 1,      TH)
tb = (W // 2,     TH * 2)
tl = (0,          TH)
bl = (0,          TH + SIDE)
br = (W - 1,      TH + SIDE)
bc = (W // 2,     TH * 2 + SIDE - 1)

EDGES = [
    (tt, tr), (tt, tl),
    (tr, tb), (tl, tb),
    (tr, br), (tl, bl),
    (br, bc), (bl, bc),
    (tb, bc),
]

def new_tile():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))

def draw_base(d, top_c, left_c, right_c, outline_c=(15, 25, 40, 220)):
    d.polygon([tl, tb, bc, bl], fill=left_c)
    d.polygon([tr, br, bc, tb], fill=right_c)
    d.polygon([tt, tr, tb, tl], fill=top_c)
    for a, b in EDGES:
        d.line([a, b], fill=outline_c, width=1)

def pts_on_top(rng, n=12, margin=6):
    """Random points guaranteed to lie inside the top-face diamond."""
    pts = []
    attempts = 0
    while len(pts) < n and attempts < 300:
        attempts += 1
        y = rng.randint(margin, TH * 2 - margin)
        hw = (TH - abs(y - TH)) * 2 - margin  # half-width at this y
        if hw < 1:
            continue
        x = rng.randint(W // 2 - hw, W // 2 + hw)
        pts.append((x, y))
    return pts

def top_hw(y):
    """Half-width of the top-face diamond at height y."""
    return (TH - abs(y - TH)) * 2

# ═══════════════════════════════════════════════════════════════
# ICE TILES
# ═══════════════════════════════════════════════════════════════
def make_ice(seed=0):
    rng = random.Random(seed)
    img = new_tile()
    d   = ImageDraw.Draw(img)

    draw_base(d,
        top_c    = (185, 225, 250, 255),
        left_c   = (110, 175, 220, 255),
        right_c  = ( 70, 135, 195, 255),
        outline_c = (18,  55, 105, 210),
    )

    # — top-face texture —
    # 1. light sub-gradient (lighter strip across upper-left of top)
    for gy in range(2, TH * 2 - 2, 3):
        hw = top_hw(gy) - 4
        if hw < 2: continue
        alpha = max(0, 60 - abs(gy - TH // 2) * 3)
        if alpha > 0:
            d.line([(W//2 - hw, gy), (W//2 + hw, gy)],
                   fill=(230, 245, 255, alpha), width=1)

    # 2. 2–3 diagonal highlight streaks
    for _ in range(rng.randint(2, 3)):
        sx = rng.randint(W//2 - 40, W//2 + 20)
        sy = rng.randint(TH + 5, TH + 25)
        ex = sx + rng.randint(20, 40)
        ey = sy + rng.randint(10, 20)
        d.line([(sx, sy), (ex, ey)], fill=(255, 255, 255, 130), width=2)
        d.line([(sx+1, sy+1), (ex+1, ey+1)], fill=(255, 255, 255, 60), width=1)

    # 3. Snow crystal dots scattered on surface
    for px, py in pts_on_top(rng, n=18):
        sz = rng.randint(1, 3)
        d.ellipse([px-sz, py-sz, px+sz, py+sz],
                  fill=(255, 255, 255, rng.randint(100, 200)))

    # 4. Fine frost pattern along top edge
    for ex in range(W//2 - 2, W - 5, 6):
        ey = TH - (ex - W//2) // 2
        if 0 <= ey < TH:
            d.ellipse([ex-1, ey-1, ex+1, ey+1], fill=(255, 255, 255, 80))

    # 5. Thin crack lines (vary by seed)
    if seed % 2 == 0:
        cx = W//2 + rng.randint(-20, 20)
        cy = TH + rng.randint(5, 20)
        pts_c = [(cx, cy)]
        for _ in range(3):
            lx, ly = pts_c[-1]
            nx = lx + rng.randint(-15, 20)
            ny = ly + rng.randint( 8,  18)
            if abs(nx - W//2) < top_hw(ny) - 3:
                pts_c.append((nx, ny))
        if len(pts_c) > 1:
            d.line(pts_c, fill=(90, 150, 200, 160), width=1)
            if len(pts_c) >= 2:
                bx, by = pts_c[1]
                d.line([(bx, by),
                        (bx + rng.randint(-15,-5), by + rng.randint(8,15))],
                       fill=(90, 150, 200, 120), width=1)

    # 6. Edge shimmer
    d.line([tt, tr], fill=(255, 255, 255, 140), width=2)
    d.line([tt, tl], fill=(255, 255, 255, 100), width=1)

    # 7. Subtle left-face shading stripe
    d.line([tl, bl], fill=(255, 255, 255, 30), width=3)

    # Redraw outlines on top
    for a, b in EDGES:
        d.line([a, b], fill=(18, 55, 105, 210), width=1)

    return img

# ═══════════════════════════════════════════════════════════════
# DROUGHT TILES
# ═══════════════════════════════════════════════════════════════
def make_drought(seed=0):
    rng = random.Random(seed)
    img = new_tile()
    d   = ImageDraw.Draw(img)

    draw_base(d,
        top_c    = (205, 155, 70, 255),
        left_c   = (158, 108, 30, 255),
        right_c  = (115,  72, 12, 255),
        outline_c = ( 55,  25,  5, 225),
    )

    # 1. Mottled surface via tiny tone-variation dots
    for px, py in pts_on_top(rng, n=30):
        shade = rng.choice([(225,175,90,50),(180,130,45,60),(240,195,100,40)])
        d.ellipse([px-2, py-2, px+2, py+2], fill=shade)

    # 2. Complex crack network
    def crack_path(start_x, start_y, steps=4):
        pts = [(start_x, start_y)]
        for _ in range(steps):
            lx, ly = pts[-1]
            nx = lx + rng.randint(-10, 18)
            ny = ly + rng.randint(  6, 15)
            if abs(nx - W//2) < top_hw(ny) - 4 and ny < TH*2 - 4:
                pts.append((nx, ny))
        return pts

    crack_c = (72, 38, 8, 240)
    shadow_c = (45, 20, 2, 120)
    for _ in range(3):
        sx = W//2 + rng.randint(-25, 25)
        sy = TH   + rng.randint(  2, 15)
        path = crack_path(sx, sy, steps=rng.randint(3, 5))
        if len(path) > 1:
            d.line(path, fill=shadow_c, width=3)   # shadow
            d.line(path, fill=crack_c,  width=1)   # crack line
        # Add 1-2 branches
        if len(path) >= 2:
            bx, by = path[rng.randint(1, max(1, len(path)-1))]
            branch = crack_path(bx, by, steps=2)
            if len(branch) > 1:
                d.line(branch, fill=shadow_c, width=2)
                d.line(branch, fill=crack_c,  width=1)

    # 3. Small rock pebbles
    for _ in range(8):
        ppts = pts_on_top(rng, n=1)
        if ppts:
            px, py = ppts[0]
            psz = rng.randint(2, 5)
            d.ellipse([px-psz, py-psz//2, px+psz, py+psz//2],
                      fill=(95, 55, 18, 180))

    # 4. Dust shimmer on top-right edge
    d.line([tt, tr], fill=(240, 200, 120, 70), width=2)

    # 5. Side-face vertical stress lines
    for i in range(0, SIDE, 8):
        sx = rng.randint(10, W//2 - 10)
        d.line([(sx, TH + i), (sx - 2, TH + i + 6)],
               fill=(100, 58, 12, 80), width=1)

    for a, b in EDGES:
        d.line([a, b], fill=(55, 25, 5, 225), width=1)

    return img

# ═══════════════════════════════════════════════════════════════
# FLOOD TILES
# ═══════════════════════════════════════════════════════════════
def make_flood(seed=0):
    rng = random.Random(seed)
    img = new_tile()
    d   = ImageDraw.Draw(img)

    draw_base(d,
        top_c    = ( 15,  58,  98, 255),
        left_c   = (  6,  32,  58, 255),
        right_c  = (  3,  18,  40, 255),
        outline_c = (  3,  12,  28, 225),
    )

    # 1. Depth gradient overlay (lighter near surface edge)
    for gy in range(TH + 2, TH * 2 - 2, 2):
        hw = top_hw(gy) - 4
        if hw < 1: continue
        dist_from_center = abs(gy - (TH + (TH * 2 - TH) // 2))
        alpha = max(0, 20 - dist_from_center)
        if alpha > 0:
            d.line([(W//2 - hw, gy), (W//2 + hw, gy)],
                   fill=(40, 110, 180, alpha), width=1)

    # 2. Multiple ripple lines (3 layers, varying opacity + width)
    for i in range(4):
        ry  = TH + 8 + i * 11 + rng.randint(-3, 3)
        hw  = top_hw(ry) - 8
        if hw < 5: continue
        rxs = W//2 - hw + rng.randint(0, 15)
        rxe = W//2 + hw - rng.randint(0, 15)
        alpha = rng.randint(100, 170)
        d.line([(rxs, ry), (W//2, ry + 2), (rxe, ry)],
               fill=(90, 165, 220, alpha), width=1)
        # Faint echo line below
        if ry + 3 < TH * 2 - 2:
            d.line([(rxs + 5, ry + 3), (rxe - 5, ry + 3)],
                   fill=(70, 135, 190, alpha // 2), width=1)

    # 3. Small bubbles (white circles with no fill)
    for px, py in pts_on_top(rng, n=10, margin=8):
        bsz = rng.randint(1, 4)
        d.ellipse([px-bsz, py-bsz, px+bsz, py+bsz],
                  outline=(160, 215, 240, 150), fill=(0,0,0,0))
        # Tiny white highlight on bubble
        d.ellipse([px-bsz//2, py-bsz, px, py-bsz+2],
                  fill=(255, 255, 255, 120))

    # 4. Light reflection diagonal streak
    sx = W//2 - 15 + rng.randint(-5, 5)
    sy = TH + rng.randint(5, 12)
    d.line([(sx, sy), (sx + 30, sy + 15)], fill=(140, 200, 240, 110), width=3)
    d.line([(sx, sy), (sx + 30, sy + 15)], fill=(200, 235, 255,  60), width=5)

    # 5. Foam flecks near surface edge (top face edge)
    for i in range(0, W - 10, 8):
        ex = i
        ey = TH + abs(i - W//2) // 2
        if abs(ex - W//2) < top_hw(ey) - 2:
            fsz = rng.randint(1, 2)
            d.ellipse([ex-fsz, ey-fsz, ex+fsz, ey+fsz],
                      fill=(200, 230, 245, rng.randint(60, 120)))

    # 6. Cold shimmer top edge
    d.line([tt, tr], fill=(100, 185, 235, 100), width=2)
    d.line([tt, tl], fill=(80,  160, 210,  60), width=1)

    # 7. Side face — subtle wavy waterline
    wy = TH + 3
    d.line([(0, wy), (W//4, wy - 2), (W//2, wy), (W - 1, wy - 2)],
           fill=(50, 120, 180, 60), width=1)

    for a, b in EDGES:
        d.line([a, b], fill=(3, 12, 28, 225), width=1)

    return img

# ═══════════════════════════════════════════════════════════════
# WILDFIRE TILES
# ═══════════════════════════════════════════════════════════════
def make_wildfire(seed=0):
    rng = random.Random(seed)
    img = new_tile()
    d   = ImageDraw.Draw(img)

    draw_base(d,
        top_c    = (30, 26, 22, 255),
        left_c   = (16, 13, 10, 255),
        right_c  = ( 9,  7,  5, 255),
        outline_c = ( 8,  6,  4, 255),
    )

    ember  = (255,  85, 10, 255)
    glow1  = (255, 160, 55, 180)
    glow2  = (255, 200, 80, 80)

    # 1. Crack network — 2-3 main cracks with branches
    def fire_crack(sx, sy, steps=4):
        path = [(sx, sy)]
        for _ in range(steps):
            lx, ly = path[-1]
            nx = lx + rng.randint(-8, 15)
            ny = ly + rng.randint(7, 16)
            if abs(nx - W//2) < top_hw(ny) - 3 and ny < TH * 2 - 3:
                path.append((nx, ny))
        return path

    for _ in range(2):
        sx = W//2 + rng.randint(-28, 28)
        sy = TH   + rng.randint(  2, 12)
        path = fire_crack(sx, sy, steps=rng.randint(3, 5))
        if len(path) > 1:
            d.line(path, fill=glow2,  width=5)  # outer glow
            d.line(path, fill=glow1,  width=3)  # mid glow
            d.line(path, fill=ember,  width=1)  # core bright
            # Glowing nodes at crack intersections
            for px, py in path[1:]:
                d.ellipse([px-3, py-3, px+3, py+3], fill=glow1)
                d.ellipse([px-1, py-1, px+1, py+1], fill=ember)
        # Branch
        if len(path) >= 2:
            bi = rng.randint(1, max(1, len(path)-1))
            bx, by = path[bi]
            branch = fire_crack(bx, by, steps=2)
            if len(branch) > 1:
                d.line(branch, fill=glow1, width=2)
                d.line(branch, fill=ember, width=1)

    # 2. Ash particle dots scattered across surface
    for px, py in pts_on_top(rng, n=25):
        shade = rng.choice([(65,60,55,130),(80,75,70,110),(50,46,42,150)])
        sz = rng.randint(1, 2)
        d.ellipse([px-sz, py-sz, px+sz, py+sz], fill=shade)

    # 3. Ember spots (tiny bright orange circles)
    for px, py in pts_on_top(rng, n=8, margin=8):
        if rng.random() > 0.5:
            d.ellipse([px-2, py-2, px+2, py+2], fill=(255, 130, 30, 160))
            d.ellipse([px-1, py-1, px+1, py+1], fill=(255, 200, 50, 200))

    # 4. Orange edge glow on top ridge
    d.line([tt, tr], fill=(255, 65, 8, 110), width=3)
    d.line([tt, tl], fill=(255, 55, 6,  70), width=2)

    # 5. Faint heat shimmer lines on sides
    for i in range(0, SIDE, 7):
        xoff = rng.randint(-2, 2)
        d.line([(5 + xoff, TH + i), (12 + xoff, TH + i + 4)],
               fill=(255, 80, 10, 35), width=1)

    for a, b in EDGES:
        d.line([a, b], fill=(8, 6, 4, 255), width=1)

    return img

# ═══════════════════════════════════════════════════════════════
# CHASER BLOCK  (menacing red enemy)
# ═══════════════════════════════════════════════════════════════
def make_chaser():
    img = new_tile()
    d   = ImageDraw.Draw(img)

    draw_base(d,
        top_c    = (215,  30,  30, 255),
        left_c   = (145,   6,   6, 255),
        right_c  = ( 95,   2,   2, 255),
        outline_c = ( 35,   0,   0, 255),
    )

    # 1. Cracked surface veins on top face
    vein_glow = (255, 100, 50, 140)
    vein_core = (255, 200, 80, 200)
    for _ in range(3):
        vx = W//2 + random.randint(-30, 30)
        vy = TH + random.randint(5, 20)
        pts_v = [(vx, vy)]
        for _ in range(3):
            lx, ly = pts_v[-1]
            nx = lx + random.randint(-10, 15)
            ny = ly + random.randint(8, 18)
            if abs(nx - W//2) < top_hw(ny) - 3 and ny < TH*2 - 3:
                pts_v.append((nx, ny))
        if len(pts_v) > 1:
            d.line(pts_v, fill=vein_glow, width=3)
            d.line(pts_v, fill=vein_core, width=1)

    # 2. Energy glow on top edges
    d.line([tt, tr], fill=(255, 140, 140, 200), width=3)
    d.line([tt, tl], fill=(255, 110, 110, 150), width=2)
    d.line([tt, tr], fill=(255, 200, 200, 100), width=5)

    # 3. ANGRY FACE on right face
    # Right face spans: tr(199,50) → br(199,105) → bc(100,154) → tb(100,100)
    # Face center: approx (155, 118)
    fx = W * 3 // 4 + 5   # ~155
    fy = TH + SIDE // 2 + 5  # ~83

    # Angry brow (V-shape above eyes) — dark red
    brow_c = (50, 0, 0, 255)
    d.line([(fx - 18, fy - 14), (fx - 8, fy - 8)], fill=brow_c, width=3)
    d.line([(fx + 5,  fy - 14), (fx - 2, fy - 8)], fill=brow_c, width=3)

    # Eyes (white rectangles with dark pupils)
    eye_w, eye_h = 11, 9
    # Left eye
    ex1 = fx - 20
    d.rectangle([ex1, fy - eye_h//2, ex1 + eye_w, fy + eye_h//2],
                fill=(255, 255, 255, 255))
    d.rectangle([ex1 + 2, fy - eye_h//4, ex1 + 5, fy + eye_h//4],
                fill=(30, 0, 0, 255))
    # Right eye
    ex2 = fx + 3
    d.rectangle([ex2, fy - eye_h//2, ex2 + eye_w, fy + eye_h//2],
                fill=(255, 255, 255, 255))
    d.rectangle([ex2 + 2, fy - eye_h//4, ex2 + 5, fy + eye_h//4],
                fill=(30, 0, 0, 255))

    # Jagged mouth
    mouth_y = fy + 12
    mouth_pts = [(fx - 16, mouth_y),
                 (fx - 10, mouth_y + 5),
                 (fx -  4, mouth_y + 1),
                 (fx +  2, mouth_y + 6),
                 (fx +  8, mouth_y + 1),
                 (fx + 14, mouth_y + 5)]
    d.line(mouth_pts, fill=(30, 0, 0, 255), width=2)

    # 4. Dark shadow under the block
    shadow = Image.new('RGBA', (W, H), (0,0,0,0))
    ds = ImageDraw.Draw(shadow)
    ds.ellipse([W//4, H - 8, W * 3//4, H + 4], fill=(0, 0, 0, 80))
    img = Image.alpha_composite(img, shadow)

    d2 = ImageDraw.Draw(img)
    for a, b in EDGES:
        d2.line([a, b], fill=(35, 0, 0, 255), width=1)

    return img

# ═══════════════════════════════════════════════════════════════
# GEM  (ice-crystal collectible)
# ═══════════════════════════════════════════════════════════════
def make_gem():
    sz = 64
    img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx, cy = sz // 2, sz // 2
    R = sz // 2 - 4

    def poly(r, cx=cx, cy=cy, offset=0.0, n=8):
        pts = []
        for i in range(n):
            a = math.pi / n + offset + i * 2 * math.pi / n
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        return pts

    # Shadow
    d.polygon([(x+2, y+3) for x,y in poly(R)], fill=(0, 90, 80, 70))

    # Outer body — teal gradient via two polygons
    d.polygon(poly(R),       fill=(  0, 200, 175, 255))
    d.polygon(poly(R - 6),   fill=( 55, 235, 210, 230))
    d.polygon(poly(R - 13),  fill=(130, 250, 230, 200))

    # Inner facets — 4 triangles to suggest faceting
    for i in range(4):
        a1 = math.pi / 8 + i * math.pi / 2
        a2 = a1 + math.pi / 4
        p1 = (cx + int(R * math.cos(a1)),       cy + int(R * math.sin(a1)))
        p2 = (cx + int(R * math.cos(a2)),       cy + int(R * math.sin(a2)))
        facet_alpha = 60 if i % 2 == 0 else 30
        d.polygon([p1, p2, (cx, cy)], fill=(200, 255, 245, facet_alpha))

    # Sparkle dots around gem
    for i in range(6):
        a = i * math.pi / 3
        sx = int(cx + (R + 4) * math.cos(a))
        sy = int(cy + (R + 4) * math.sin(a))
        if 0 <= sx < sz and 0 <= sy < sz:
            d.ellipse([sx-2, sy-2, sx+2, sy+2], fill=(200, 255, 245, 160))
            d.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(255, 255, 255, 220))

    # Main highlight
    d.ellipse([cx - 14, cy - 16, cx - 4, cy - 8],  fill=(255, 255, 255, 200))
    d.ellipse([cx - 12, cy - 14, cx - 7, cy - 10], fill=(255, 255, 255, 255))

    # Outline
    d.polygon(poly(R), outline=(0, 140, 120, 220))

    return img

# ═══════════════════════════════════════════════════════════════
# BIOME BACKGROUNDS
# ═══════════════════════════════════════════════════════════════
BW, BH = 1920, 1080

def lerp(a, b, t):
    return int(a + (b - a) * t)

def lerp_col(c1, c2, t):
    return (lerp(c1[0],c2[0],t), lerp(c1[1],c2[1],t), lerp(c1[2],c2[2],t))

def bg_arctic():
    """Deep arctic night sky with detailed aurora and ice landscape."""
    img = Image.new('RGB', (BW, BH), (10, 15, 45))
    d   = ImageDraw.Draw(img)
    rng = random.Random(1)

    # — Sky gradient —
    for y in range(BH):
        t = y / BH
        c = lerp_col((8, 12, 50), (20, 40, 90), min(t * 2, 1.0))
        if y > BH * 0.6:
            c = lerp_col(c, (130, 175, 210), (t - 0.6) / 0.4)
        d.line([(0, y), (BW, y)], fill=c)

    # — Stars (3 sizes) —
    for _ in range(320):
        sx = rng.randint(0, BW)
        sy = rng.randint(0, int(BH * 0.55))
        br = rng.randint(140, 255)
        sz = rng.choices([0, 1, 2], weights=[6, 3, 1])[0]
        if sz == 0:
            d.point((sx, sy), fill=(br, br, br+20))
        elif sz == 1:
            d.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(br, br, br+20))
        else:
            d.ellipse([sx-2, sy-2, sx+2, sy+2], fill=(br, br, br+15))
            d.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(255, 255, 255))

    # — Aurora borealis (wavy layered ribbons) —
    aurora_colors = [
        [(20, 200, 120, 0), (20, 200, 120, 60), (20, 200, 120, 0)],
        [(50, 150, 220, 0), (50, 150, 220, 45), (50, 150, 220, 0)],
        [(120, 220, 180, 0),(120, 220, 180, 35),(120, 220, 180, 0)],
    ]
    for band_i, colors in enumerate(aurora_colors):
        base_y   = int(BH * (0.08 + band_i * 0.05))
        amplitude = rng.randint(20, 45)
        period    = rng.randint(500, 900)
        thickness = rng.randint(18, 40)
        phase     = rng.uniform(0, math.pi * 2)

        aurora_layer = Image.new('RGBA', (BW, BH), (0,0,0,0))
        da = ImageDraw.Draw(aurora_layer)

        for x in range(0, BW, 2):
            wave_y = base_y + int(amplitude * math.sin(2 * math.pi * x / period + phase))
            for dy in range(-thickness, thickness):
                ay = wave_y + dy
                if 0 <= ay < BH:
                    t  = 1 - abs(dy) / thickness
                    alpha = int(colors[1][3] * t * t)
                    base_c = lerp_col(colors[0][:3], colors[1][:3], t)
                    da.point((x, ay), fill=(*base_c, alpha))
                    if x + 1 < BW:
                        da.point((x+1, ay), fill=(*base_c, alpha))

        img = Image.alpha_composite(img.convert('RGBA'), aurora_layer).convert('RGB')
        d   = ImageDraw.Draw(img)

    # — Distant mountain silhouettes (layered) —
    horizon_y = int(BH * 0.62)
    for layer in range(3):
        mtn_color = lerp_col((15, 30, 70), (80, 120, 170), layer / 3)
        rng2 = random.Random(layer + 10)
        pts  = [(0, BH), (0, horizon_y + rng2.randint(-20, 20))]
        x    = 0
        while x < BW:
            peak_h = rng2.randint(60, 180) - layer * 30
            pts.append((x + rng2.randint(40, 100), horizon_y - peak_h))
            x = pts[-1][0]
            pts.append((x + rng2.randint(30, 80), horizon_y + rng2.randint(-10, 10)))
            x = pts[-1][0]
        pts += [(BW, BH)]
        d.polygon(pts, fill=mtn_color)

    # — Snow on mountain peaks —
    d2 = ImageDraw.Draw(img)
    rng3 = random.Random(99)
    for _ in range(12):
        px = rng3.randint(50, BW - 50)
        py = rng3.randint(int(BH * 0.38), int(BH * 0.55))
        pw = rng3.randint(20, 55)
        ph = rng3.randint(12, 28)
        d2.ellipse([px-pw, py-ph, px+pw, py+ph], fill=(220, 235, 245))

    # — Ice ground with crack texture —
    ground_y = int(BH * 0.68)
    for y in range(ground_y, BH):
        t = (y - ground_y) / (BH - ground_y)
        c = lerp_col((140, 185, 215), (200, 225, 240), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Ground crack lines
    rng4 = random.Random(77)
    for _ in range(18):
        cx_g = rng4.randint(0, BW)
        cy_g = rng4.randint(ground_y, BH - 10)
        length = rng4.randint(60, 220)
        angle  = rng4.uniform(-0.3, 0.3)
        ex_g   = cx_g + int(length * math.cos(angle))
        ey_g   = cy_g + int(length * math.sin(angle) * 0.3)
        d.line([(cx_g, cy_g), (ex_g, ey_g)], fill=(100, 145, 180, 160), width=1)

    # — Distant icebergs —
    for i in range(4):
        ix = int(BW * (0.1 + i * 0.25)) + rng.randint(-60, 60)
        iy = ground_y - rng.randint(30, 80)
        iw = rng.randint(40, 110)
        ih = rng.randint(25, 60)
        d.polygon([(ix, iy+ih), (ix+iw//2, iy), (ix+iw, iy+ih)],
                  fill=(170, 210, 235))
        d.polygon([(ix+5, iy+ih), (ix+iw//2, iy+8), (ix+iw-5, iy+ih)],
                  fill=(200, 228, 245))

    return img

def bg_drought():
    """Scorched orange wasteland under blazing sky."""
    img = Image.new('RGB', (BW, BH), (200, 130, 50))
    d   = ImageDraw.Draw(img)
    rng = random.Random(2)

    # Sky gradient — pale yellow-white at top, orange haze below
    for y in range(int(BH * 0.6)):
        t = y / (BH * 0.6)
        c = lerp_col((245, 230, 180), (210, 155, 60), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Sun
    sun_x, sun_y = int(BW * 0.72), int(BH * 0.12)
    for r_sun in range(80, 0, -4):
        alpha_t = (80 - r_sun) / 80
        sc = lerp_col((255, 240, 150), (255, 220, 80), alpha_t)
        d.ellipse([sun_x-r_sun, sun_y-r_sun, sun_x+r_sun, sun_y+r_sun],
                  fill=sc)
    d.ellipse([sun_x-35, sun_y-35, sun_x+35, sun_y+35], fill=(255, 255, 200))

    # Heat haze lines
    for i in range(20):
        hx = rng.randint(0, BW)
        hy = rng.randint(int(BH * 0.3), int(BH * 0.6))
        d.line([(hx, hy), (hx + rng.randint(40, 120), hy + rng.randint(-3, 3))],
               fill=(240, 200, 120, 60), width=1)

    # Distant dead trees silhouettes
    horizon_y = int(BH * 0.58)
    for i in range(8):
        tx = rng.randint(0, BW)
        ty = horizon_y - rng.randint(20, 80)
        d.line([(tx, horizon_y), (tx, ty)], fill=(80, 45, 15), width=rng.randint(2, 5))
        # Bare branches
        for _ in range(rng.randint(2, 4)):
            blen = rng.randint(15, 40)
            bdir = rng.choice([-1, 1])
            by2  = ty + rng.randint(5, 25)
            d.line([(tx, by2), (tx + bdir*blen, by2 - rng.randint(5, 20))],
                   fill=(80, 45, 15), width=2)

    # Ground — cracked earth
    for y in range(horizon_y, BH):
        t = (y - horizon_y) / (BH - horizon_y)
        c = lerp_col((185, 130, 50), (155, 100, 30), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Crack network on ground
    rng5 = random.Random(55)
    for _ in range(35):
        cx_g = rng5.randint(0, BW)
        cy_g = rng5.randint(horizon_y + 20, BH - 30)
        pts_cg = [(cx_g, cy_g)]
        for _ in range(4):
            lx, ly = pts_cg[-1]
            pts_cg.append((lx + rng5.randint(-40, 60), ly + rng5.randint(-8, 20)))
        d.line(pts_cg, fill=(100, 60, 18), width=1)

    return img

def bg_flood():
    """Grey storm sky above dark rising floodwaters."""
    img = Image.new('RGB', (BW, BH), (18, 45, 75))
    d   = ImageDraw.Draw(img)
    rng = random.Random(3)

    # Storm sky gradient
    for y in range(int(BH * 0.55)):
        t = y / (BH * 0.55)
        c = lerp_col((35, 42, 58), (60, 72, 90), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Storm clouds (dark layered)
    for ci in range(6):
        cx_c = rng.randint(-100, BW + 100)
        cy_c = rng.randint(10,   int(BH * 0.4))
        cw   = rng.randint(200, 500)
        ch   = rng.randint(50,  140)
        shade = rng.randint(30, 65)
        d.ellipse([cx_c, cy_c, cx_c+cw, cy_c+ch], fill=(shade, shade+5, shade+12))
        d.ellipse([cx_c+50, cy_c-20, cx_c+cw-50, cy_c+ch-10],
                  fill=(shade+10, shade+15, shade+22))

    # Flooded city silhouette (partially submerged buildings)
    horizon_y = int(BH * 0.52)
    rng6 = random.Random(66)
    for i in range(15):
        bx = rng6.randint(0, BW - 60)
        bh = rng6.randint(60, 220)
        bw = rng6.randint(30, 80)
        by = horizon_y - bh + rng6.randint(-20, 20)
        d.rectangle([bx, by, bx+bw, horizon_y], fill=(20, 30, 50))
        # Windows (some lit)
        for wy_b in range(by + 8, horizon_y - 10, 18):
            for wx_b in range(bx + 5, bx + bw - 5, 14):
                wc = (200, 185, 100) if rng6.random() > 0.6 else (25, 35, 55)
                d.rectangle([wx_b, wy_b, wx_b+6, wy_b+8], fill=wc)

    # Water surface (dark navy with reflections)
    water_y = horizon_y + 20
    for y in range(water_y, BH):
        t = (y - water_y) / (BH - water_y)
        c = lerp_col((12, 35, 65), (5, 18, 38), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Water ripples / waves
    rng7 = random.Random(77)
    for i in range(25):
        wy_w = rng7.randint(water_y + 5, BH - 20)
        wxs  = rng7.randint(0, BW - 100)
        wlen = rng7.randint(80, 300)
        wal  = rng7.randint(50, 100)
        d.arc([(wxs, wy_w - 5), (wxs + wlen, wy_w + 5)], 0, 180,
              fill=(60, 120, 175, wal), width=1)

    # Floating debris (small ice chunks)
    for _ in range(10):
        dx = rng.randint(0, BW)
        dy = rng.randint(water_y + 10, BH - 50)
        dw = rng.randint(15, 45)
        dh = rng.randint(8, 18)
        d.polygon([(dx, dy+dh), (dx+dw//2, dy), (dx+dw, dy+dh)],
                  fill=(130, 165, 195))

    return img

def bg_wildfire():
    """Red-orange sky choked with smoke above charred wasteland."""
    img = Image.new('RGB', (BW, BH), (20, 10, 5))
    d   = ImageDraw.Draw(img)
    rng = random.Random(4)

    # Sky — dark red to orange gradient
    for y in range(int(BH * 0.65)):
        t = y / (BH * 0.65)
        c = lerp_col((30, 8, 2), (160, 60, 10), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Smoke clouds (dark, billowing)
    for ci in range(8):
        cx_s = rng.randint(-50, BW + 50)
        cy_s = rng.randint(0, int(BH * 0.5))
        cw   = rng.randint(150, 400)
        ch   = rng.randint(60, 150)
        shade = rng.randint(20, 50)
        d.ellipse([cx_s, cy_s, cx_s+cw, cy_s+ch], fill=(shade, shade//2, shade//3))
        d.ellipse([cx_s+40, cy_s-15, cx_s+cw-40, cy_s+ch-10],
                  fill=(shade+15, shade//2+5, shade//3+3))

    # Ember particles in sky
    for _ in range(80):
        ex = rng.randint(0, BW)
        ey = rng.randint(0, int(BH * 0.65))
        ea = rng.randint(80, 200)
        ec = rng.choice([(255, 120, 20), (255, 180, 40), (255, 80, 10)])
        sz = rng.randint(1, 3)
        d.ellipse([ex-sz, ey-sz, ex+sz, ey+sz], fill=(*ec, ea))

    # Horizon glow (fire on the horizon)
    horizon_y = int(BH * 0.58)
    for dy in range(60):
        t = dy / 60
        alpha = int(180 * (1 - t))
        gc = lerp_col((255, 120, 10), (160, 60, 5), t)
        d.line([(0, horizon_y - dy), (BW, horizon_y - dy)],
               fill=(*gc,))

    # Burnt tree silhouettes
    rng8 = random.Random(88)
    for i in range(12):
        tx  = rng8.randint(0, BW)
        ty  = horizon_y - rng8.randint(40, 130)
        d.line([(tx, horizon_y), (tx, ty)], fill=(15, 10, 5), width=rng8.randint(3, 7))
        for _ in range(rng8.randint(2, 5)):
            blen = rng8.randint(12, 35)
            bdir = rng8.choice([-1, 1])
            by2  = ty + rng8.randint(10, 35)
            d.line([(tx, by2), (tx + bdir*blen, by2 - rng8.randint(3, 15))],
                   fill=(15, 10, 5), width=2)

    # Ash ground
    for y in range(horizon_y, BH):
        t = (y - horizon_y) / (BH - horizon_y)
        c = lerp_col((32, 26, 22), (18, 14, 10), t)
        d.line([(0, y), (BW, y)], fill=c)

    # Glowing cracks on ground
    rng9 = random.Random(99)
    for _ in range(20):
        gc_x = rng9.randint(0, BW)
        gc_y = rng9.randint(horizon_y + 10, BH - 20)
        pts_g = [(gc_x, gc_y)]
        for _ in range(4):
            lx, ly = pts_g[-1]
            pts_g.append((lx + rng9.randint(-50, 70), ly + rng9.randint(-5, 15)))
        d.line(pts_g, fill=(255, 100, 15), width=2)
        d.line(pts_g, fill=(255, 180, 50), width=1)

    return img

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    paths = {
        'ice':       os.path.join(BASE, "tiles_new", "ice"),
        'drought':   os.path.join(BASE, "tiles_new", "drought"),
        'flood':     os.path.join(BASE, "tiles_new", "flood"),
        'wildfire':  os.path.join(BASE, "tiles_new", "wildfire"),
        'objects':   os.path.join(BASE, "tiles_new"),
        'bg':        os.path.join(BASE, "background"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)

    print("Generating tiles (200×155px with detail)...")
    for i in range(1, 11):
        make_ice(seed=i).save(os.path.join(paths['ice'], f"ice_tile_{i}.png"))
    for i in range(1, 6):
        make_drought(seed=i).save(  os.path.join(paths['drought'],  f"drought_tile_{i}.png"))
        make_flood(seed=i).save(    os.path.join(paths['flood'],    f"flood_tile_{i}.png"))
        make_wildfire(seed=i).save( os.path.join(paths['wildfire'], f"wildfire_tile_{i}.png"))
    print("  ✓ 25 biome tiles")

    make_chaser().save(os.path.join(paths['objects'], "chaser_block.png"))
    make_gem().save(   os.path.join(paths['objects'], "gem.png"))
    print("  ✓ chaser_block + gem")

    print("Generating backgrounds (1920×1080)...")
    bg_arctic().save(  os.path.join(paths['bg'], "arctic_bg.png"))
    bg_drought().save( os.path.join(paths['bg'], "drought_bg.png"))
    bg_flood().save(   os.path.join(paths['bg'], "flood_bg.png"))
    bg_wildfire().save(os.path.join(paths['bg'], "wildfire_bg.png"))
    print("  ✓ 4 biome backgrounds")

    print(f"\nAll assets saved to: {BASE}/tiles_new/ and background/")
