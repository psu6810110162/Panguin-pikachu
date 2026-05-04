#!/usr/bin/env python3
"""
Generate all original game assets for "The Great Melt"
Run from project root: python scripts/generate_assets.py
Requires: Pillow  (pip install Pillow)
"""
import os
import math
import random
from PIL import Image, ImageDraw

BASE = "assets/great_melt"

DIRS = [
    f"{BASE}/background",
    f"{BASE}/tiles",
    f"{BASE}/characters/classic",
    f"{BASE}/characters/arctic",
    f"{BASE}/characters/emperor",
    f"{BASE}/characters/crystal",
    f"{BASE}/obstacles",
    f"{BASE}/gems",
]


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ─── 1. PENGUIN SPRITES (32×32 per frame, RGBA) ──────────────────────────────

def _draw_penguin_frame(d, x, frame_num, body, belly, beak, accent):
    bob = int(math.sin(frame_num * math.pi * 2 / 11) * 1.5)

    def px(v): return x + v
    def py(v): return v + bob

    d.ellipse([px(8),  py(8),  px(24), py(26)], fill=body)
    d.ellipse([px(11), py(12), px(21), py(24)], fill=belly)
    d.ellipse([px(10), py(1),  px(22), py(13)], fill=body)
    d.ellipse([px(12), py(3),  px(15), py(6)],  fill=(255, 255, 255, 255))
    d.ellipse([px(17), py(3),  px(20), py(6)],  fill=(255, 255, 255, 255))
    d.ellipse([px(13), py(4),  px(14), py(5)],  fill=(15, 15, 15, 255))
    d.ellipse([px(18), py(4),  px(19), py(5)],  fill=(15, 15, 15, 255))
    d.polygon([px(15), py(7), px(17), py(10), px(13), py(10)], fill=beak)
    d.ellipse([px(3),  py(11), px(11), py(21)], fill=body)
    d.ellipse([px(21), py(11), px(29), py(21)], fill=body)
    d.ellipse([px(4),  py(12), px(10), py(20)],
              fill=tuple(max(0, c - 25) for c in body[:3]) + (255,))
    d.ellipse([px(22), py(12), px(28), py(20)],
              fill=tuple(max(0, c - 25) for c in body[:3]) + (255,))
    d.ellipse([px(10), py(25), px(16), py(31)], fill=beak)
    d.ellipse([px(16), py(25), px(22), py(31)], fill=beak)
    if accent:
        d.polygon([px(13), py(1), px(16), py(-4), px(19), py(1)], fill=accent)


def _draw_fall_frame(d, x, body, belly, beak):
    d.ellipse([x + 8,  5,  x + 24, 23], fill=body)
    d.ellipse([x + 11, 9,  x + 21, 21], fill=belly)
    d.ellipse([x + 10, 0,  x + 22, 11], fill=body)
    d.ellipse([x + 12, 2,  x + 15, 5],  fill=(255, 255, 255, 255))
    d.ellipse([x + 17, 2,  x + 20, 5],  fill=(255, 255, 255, 255))
    d.ellipse([x + 13, 3,  x + 14, 4],  fill=(15, 15, 15, 255))
    d.ellipse([x + 18, 3,  x + 19, 4],  fill=(15, 15, 15, 255))
    d.polygon([x + 15, 6, x + 17, 9, x + 13, 9], fill=beak)
    d.ellipse([x + 1,  10, x + 9,  19], fill=body)
    d.ellipse([x + 23, 10, x + 31, 19], fill=body)
    d.ellipse([x + 10, 24, x + 16, 31], fill=beak)
    d.ellipse([x + 16, 24, x + 22, 31], fill=beak)


def generate_penguin(name, body, belly, beak, accent=None):
    idle = Image.new("RGBA", (352, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(idle)
    for i in range(11):
        _draw_penguin_frame(d, i * 32, i, body, belly, beak, accent)
    idle.save(f"{BASE}/characters/{name}/idle.png")

    fall = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    df = ImageDraw.Draw(fall)
    _draw_fall_frame(df, 0, body, belly, beak)
    fall.save(f"{BASE}/characters/{name}/fall.png")
    print(f"  ✓ {name}")


# ─── 2. ICE TILES (130×130, RGBA) ────────────────────────────────────────────

def generate_ice_tile(n, crack_level):
    img = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    r = random.Random(n * 17 + 3)
    br = r.randint(175, 215)
    bg = r.randint(220, 242)
    surface = (br, bg, 255, 255)
    left_f  = (br - 55, bg - 45, 215, 255)
    right_f = (br - 75, bg - 65, 195, 255)

    d.polygon([(65, 65), (130, 32), (130, 97), (65, 130)], fill=right_f)
    d.polygon([(0, 32),  (65, 65),  (65, 130), (0, 97)],   fill=left_f)
    d.polygon([(65, 0),  (130, 32), (65, 65),  (0, 32)],   fill=surface)

    shimmer = (min(255, br + 35), min(255, bg + 20), 255, 160)
    d.line([(68, 6), (125, 35)], fill=shimmer, width=1)
    d.line([(65, 12), (118, 39)], fill=shimmer, width=1)

    cr = random.Random(n * 31 + crack_level)
    for _ in range(crack_level):
        x1 = cr.randint(38, 92)
        y1 = cr.randint(14, 52)
        x2 = x1 + cr.randint(-22, 22)
        y2 = y1 + cr.randint(4, 20)
        crack_c = (90, 155, 210, 210)
        d.line([(x1, y1), (x2, y2)], fill=crack_c, width=1)
        if cr.random() > 0.4:
            mx, my = (x1 + x2) // 2, (y1 + y2) // 2
            d.line([(mx, my), (mx + cr.randint(-9, 9), my + cr.randint(3, 12))],
                   fill=crack_c, width=1)

    edge_top   = (115, 175, 230, 255)
    edge_left  = (80, 130, 195, 255)
    edge_right = (60, 100, 165, 255)
    d.line([(65, 0),  (130, 32)], fill=edge_top, width=1)
    d.line([(130, 32),(65, 65)],  fill=edge_top, width=1)
    d.line([(65, 65), (0, 32)],   fill=edge_top, width=1)
    d.line([(0, 32),  (65, 0)],   fill=edge_top, width=1)
    d.line([(0, 32),  (0, 97)],   fill=edge_left, width=1)
    d.line([(65, 65), (65, 130)], fill=edge_left, width=1)
    d.line([(65, 130),(0, 97)],   fill=edge_left, width=1)
    d.line([(130, 32),(130, 97)], fill=edge_right, width=1)
    d.line([(65, 130),(130, 97)], fill=edge_right, width=1)

    img.save(f"{BASE}/tiles/ice_tile_{n}.png")


# ─── 3. ICE BLOCK OBSTACLE ───────────────────────────────────────────────────

def _block_body(d, x, y, w, h, cracks, alpha=220):
    ice = (180, 220, 255, alpha)
    border = (100, 160, 225, 255)
    d.rectangle([x + 2, y + 2, x + w - 3, y + h - 3], fill=ice)
    d.rectangle([x + 2, y + 2, x + w - 3, y + h - 3], outline=border)
    d.line([(x + 4, y + 4), (x + 10, y + 4)], fill=(225, 245, 255, 160), width=1)
    d.line([(x + 4, y + 4), (x + 4, y + 10)], fill=(225, 245, 255, 160), width=1)
    cr = random.Random(cracks * 13)
    for _ in range(cracks * 2):
        ax = cr.randint(x + 3, x + w - 5)
        ay = cr.randint(y + 3, y + h - 4)
        bx = ax + cr.randint(-6, 6)
        by = ay + cr.randint(-4, 4)
        d.line([(ax, ay), (bx, by)], fill=(75, 140, 205, 200), width=1)


def generate_ice_block():
    idle = Image.new("RGBA", (28, 24), (0, 0, 0, 0))
    _block_body(ImageDraw.Draw(idle), 0, 0, 28, 24, cracks=0)
    idle.save(f"{BASE}/obstacles/ice_idle.png")

    hit = Image.new("RGBA", (28 * 4, 24), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hit)
    for i in range(4):
        ox = (1 if i % 2 else -1) if i > 0 else 0
        _block_body(dh, i * 28 + ox, 0, 28, 24, cracks=i + 1)
    hit.save(f"{BASE}/obstacles/ice_hit.png")

    brk = Image.new("RGBA", (28 * 4, 24), (0, 0, 0, 0))
    db = ImageDraw.Draw(brk)
    for i in range(4):
        alpha = max(0, 220 - i * 60)
        if alpha == 0:
            continue
        margin = i * 3
        x, y, w, h = i * 28, 0, 28, 24
        if w - 2 * margin > 4 and h - 2 * margin > 4:
            db.rectangle([x + margin, y + margin, x + w - margin - 1, y + h - margin - 1],
                         fill=(180, 220, 255, alpha), outline=(100, 160, 225, alpha))
        if i < 3:
            frag_size = max(2, 5 - i)
            for fx, fy in [(x + w - margin - frag_size - 1, y + margin),
                           (x + margin, y + h - margin - frag_size - 1)]:
                db.rectangle([fx, fy, fx + frag_size, fy + frag_size],
                             fill=(200, 235, 255, alpha // 2))
    brk.save(f"{BASE}/obstacles/ice_break.png")
    print("  ✓ ice block (idle / hit / break)")


# ─── 4. ICE CRYSTAL GEM (64×16, RGBA, 4 frames) ──────────────────────────────

def generate_gem():
    img = Image.new("RGBA", (64, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cores   = [(155, 225, 255, 255), (185, 240, 255, 255),
               (210, 250, 255, 255), (165, 230, 255, 255)]
    shines  = [(200, 245, 255, 200), (220, 250, 255, 210),
               (240, 255, 255, 220), (210, 248, 255, 200)]
    outlines= [(85, 155, 210, 255), (95, 165, 220, 255),
               (105, 175, 230, 255), (90, 160, 215, 255)]

    for f in range(4):
        fx = f * 16
        c, sh, ol = cores[f], shines[f], outlines[f]
        d.polygon([fx+8, 0, fx+15, 5, fx+15, 11, fx+8, 16, fx+1, 11, fx+1, 5], fill=c)
        d.polygon([fx+8, 1, fx+13, 5, fx+8,  9,  fx+3,  5], fill=sh)
        d.polygon([fx+8, 0, fx+15, 5, fx+15, 11, fx+8, 16, fx+1, 11, fx+1, 5], outline=ol)

    img.save(f"{BASE}/gems/ice_crystal_strip4.png")
    print("  ✓ ice crystal gem")


# ─── 5. ARCTIC BACKGROUND (1920×1080, RGB) ───────────────────────────────────

def generate_background():
    img = Image.new("RGB", (1920, 1080), (10, 30, 80))
    d = ImageDraw.Draw(img)

    sky_top  = (10, 30, 80)
    sky_mid  = (35, 95, 175)
    sky_hor  = (125, 190, 238)
    hor_y    = 680

    for y in range(hor_y):
        t = y / hor_y
        c = lerp_color(sky_top, sky_mid, min(1, t * 2)) if t < 0.5 \
            else lerp_color(sky_mid, sky_hor, (t - 0.5) * 2)
        d.rectangle([0, y, 1920, y + 1], fill=c)

    ar = random.Random(7)
    aurora_bands = [
        (50, 200, 150, 28), (70, 140, 215, 22), (100, 215, 175, 18),
        (60, 180, 130, 20), (80, 160, 220, 15),
    ]
    for _ in range(9):
        ay  = ar.randint(40, 330)
        aw  = ar.randint(280, 720)
        ax  = ar.randint(0, max(0, 1920 - aw))
        col = ar.choice(aurora_bands)
        for dy in range(24):
            alpha = int(col[3] * max(0, 1 - abs(dy - 12) / 12))
            if alpha == 0:
                continue
            line_c = lerp_color(
                lerp_color(img.getpixel((ax, ay + dy))[:3], col[:3], alpha / 255),
                (255, 255, 255), 0
            )
            d.rectangle([ax, ay + dy, ax + aw, ay + dy + 1], fill=line_c)

    sr = random.Random(99)
    for _ in range(220):
        sx = sr.randint(0, 1920)
        sy = sr.randint(0, 380)
        sz = sr.choice([1, 1, 1, 2])
        bri = sr.randint(175, 255)
        d.ellipse([sx, sy, sx + sz, sy + sz], fill=(bri, bri, bri))

    for y in range(hor_y, 1080):
        t = (y - hor_y) / (1080 - hor_y)
        c = lerp_color(sky_hor, (200, 228, 252), t)
        d.rectangle([0, y, 1920, y + 1], fill=c)

    br = random.Random(55)
    for _ in range(7):
        bx = br.randint(-80, 1900)
        bw = br.randint(90, 260)
        bh = br.randint(35, 110)
        by = hor_y - bh
        pts = [(bx, by + bh), (bx + bw // 2, by), (bx + bw, by + bh)]
        d.polygon(pts, fill=(215, 238, 255))
        d.polygon(
            [(bx + bw // 4, by + bh // 2),
             (bx + bw // 2, by + 6),
             (bx + 3 * bw // 4, by + bh // 2)],
            fill=(235, 248, 255)
        )

    cr = random.Random(23)
    for _ in range(18):
        cx  = cr.randint(0, 1920)
        cy  = cr.randint(hor_y + 40, 1060)
        cx2 = cx + cr.randint(-110, 110)
        cy2 = cy + cr.randint(-15, 15)
        d.line([(cx, cy), (cx2, cy2)], fill=(135, 182, 220), width=cr.randint(1, 3))

    img.save(f"{BASE}/background/arctic_bg.png")
    print("  ✓ arctic background (1920×1080)")


# ─── 6. BIOME TILES (130×130, RGBA) ──────────────────────────────────────────

def _biome_tile(biome_id, n, surface_fn, left_f, right_f, edge_t, edge_l, edge_r,
                crack_color, crack_width=1, surface_detail_fn=None):
    """Generic isometric tile generator reused by all biomes."""
    img = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = random.Random(n * 17 + 3 + sum(ord(c) for c in biome_id))
    surface = surface_fn(r)

    d.polygon([(65,65),(130,32),(130,97),(65,130)], fill=right_f)
    d.polygon([(0,32),(65,65),(65,130),(0,97)],    fill=left_f)
    d.polygon([(65,0),(130,32),(65,65),(0,32)],    fill=surface)

    if surface_detail_fn:
        surface_detail_fn(d, r, surface)

    cr = random.Random(n * 31 + 7)
    n_cracks = 2 + n % 4
    for _ in range(n_cracks):
        x1 = cr.randint(38, 92); y1 = cr.randint(14, 52)
        x2 = x1 + cr.randint(-20, 20); y2 = y1 + cr.randint(4, 18)
        d.line([(x1,y1),(x2,y2)], fill=crack_color, width=crack_width)
        if cr.random() > 0.45:
            mx, my = (x1+x2)//2, (y1+y2)//2
            d.line([(mx,my),(mx+cr.randint(-8,8),my+cr.randint(3,10))], fill=crack_color, width=crack_width)

    for pts, col in [
        ([(65,0),(130,32),(65,65),(0,32)], edge_t),
        ([(0,32),(0,97),(65,130),(65,65)], edge_l),
        ([(130,32),(130,97),(65,130),(65,65)], edge_r),
    ]:
        for i in range(len(pts)-1):
            d.line([pts[i], pts[i+1]], fill=col, width=1)

    out_dir = f"{BASE}/tiles/{biome_id}"
    os.makedirs(out_dir, exist_ok=True)
    img.save(f"{out_dir}/{biome_id}_tile_{n}.png")


def generate_drought_tiles():
    def surface(r): return (200+r.randint(0,25), 162+r.randint(0,20), 72+r.randint(0,18), 255)
    def detail(d, r, surf):
        # sand shimmer
        sh = (min(255,surf[0]+40), min(255,surf[1]+30), min(255,surf[2]+15), 100)
        d.line([(70,8),(122,36)], fill=sh, width=1)
        # sand grain dots
        for _ in range(8):
            sx=r.randint(40,120); sy=r.randint(10,55)
            d.point((sx,sy), fill=(min(255,surf[0]+55),min(255,surf[1]+40),min(255,surf[2]+10),140))
    for i in range(1, 6):
        _biome_tile('drought', i,
            surface_fn=surface,
            left_f=(152,112,42,255), right_f=(118,82,25,255),
            edge_t=(175,138,65,255), edge_l=(125,92,30,255), edge_r=(95,68,18,255),
            crack_color=(88,52,12,235), crack_width=2,
            surface_detail_fn=detail)
    print("  ✓ drought tiles x5")


def generate_flood_tiles():
    def surface(r): return (32+r.randint(0,18), 95+r.randint(0,22), 142+r.randint(0,18), 255)
    def detail(d, r, surf):
        # water shimmer / ripple lines
        for _ in range(4):
            ry = r.randint(12, 55); rx = r.randint(42, 75)
            rw = r.randint(12, 30)
            sh = (min(255,surf[0]+70),min(255,surf[1]+80),min(255,surf[2]+70),150)
            d.line([(rx,ry),(rx+rw,ry+1)], fill=sh, width=1)
        # bubbles
        for _ in range(3):
            bx=r.randint(50,110); by=r.randint(15,50)
            d.ellipse([bx,by,bx+2,by+2], outline=(160,220,245,180))
    for i in range(1, 6):
        _biome_tile('flood', i,
            surface_fn=surface,
            left_f=(22,65,105,255), right_f=(14,46,80,255),
            edge_t=(65,140,185,255), edge_l=(35,88,135,255), edge_r=(22,60,105,255),
            crack_color=(115,195,235,170), crack_width=1,
            surface_detail_fn=detail)
    print("  ✓ flood tiles x5")


def generate_wildfire_tiles():
    def surface(r): return (58+r.randint(0,14), 50+r.randint(0,10), 45+r.randint(0,8), 255)
    def detail(d, r, surf):
        # ember dots
        for _ in range(5):
            ex=r.randint(42,115); ey=r.randint(12,52)
            ec=(210+r.randint(0,45), 70+r.randint(0,35), r.randint(0,15), 220)
            d.ellipse([ex,ey,ex+2,ey+2], fill=ec)
        # ash shimmer
        d.line([(68,8),(118,34)], fill=(85,78,72,90), width=1)
    for i in range(1, 6):
        _biome_tile('wildfire', i,
            surface_fn=surface,
            left_f=(38,32,29,255), right_f=(26,21,18,255),
            edge_t=(80,68,60,255), edge_l=(52,44,38,255), edge_r=(36,28,24,255),
            crack_color=(218+random.randint(0,30), 78+random.randint(0,25), 8, 230),
            crack_width=2,
            surface_detail_fn=detail)
    print("  ✓ wildfire tiles x5")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=== The Great Melt — Asset Generator ===\n")
    for directory in DIRS:
        os.makedirs(directory, exist_ok=True)

    print("Penguin sprites...")
    generate_penguin(
        "classic",
        body=(30, 30, 40, 255), belly=(245, 245, 248, 255),
        beak=(238, 138, 28, 255)
    )
    generate_penguin(
        "arctic",
        body=(175, 210, 238, 255), belly=(238, 246, 255, 255),
        beak=(110, 175, 220, 255)
    )
    generate_penguin(
        "emperor",
        body=(22, 22, 32, 255), belly=(255, 228, 95, 255),
        beak=(252, 188, 0, 255), accent=(255, 218, 0, 255)
    )
    generate_penguin(
        "crystal",
        body=(140, 198, 238, 215), belly=(200, 233, 255, 205),
        beak=(160, 218, 255, 255), accent=(195, 242, 255, 255)
    )

    print("\nIce tiles...")
    for i in range(1, 11):
        generate_ice_tile(i, crack_level=(i - 1))
    print("  ✓ ice_tile_1.png … ice_tile_10.png")

    print("\nIce block obstacle...")
    generate_ice_block()

    print("\nIce crystal gem...")
    generate_gem()

    print("\nArctic background...")
    generate_background()

    print("\nDrought tiles...")
    generate_drought_tiles()

    print("\nFlood tiles...")
    generate_flood_tiles()

    print("\nWildfire tiles...")
    generate_wildfire_tiles()

    print("\n=== Done! Assets saved to assets/great_melt/ ===")


if __name__ == "__main__":
    main()
