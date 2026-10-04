"""Compose one overview sheet of every asset produced in this session.

Sections: the two tile styles in a mock level, the flat tile strip including
the shelf, the suspect roster, and the hero avatar. This is the artifact to
judge the whole set at once rather than tile by tile.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ART = os.path.dirname(os.path.abspath(__file__))
W = 980
PAD = 20
DARK_BG = (18, 20, 26, 255)
PAPER_BG = (242, 240, 247, 255)
INK = (25, 25, 34, 255)
MUTED = (120, 124, 140, 255)

TILES = ["floor", "wall", "box", "goal", "player", "shelf"]
ROSTER = [("ada", "Ada"), ("brigitte", "Brigitte"), ("cameron", "Cameron"),
          ("darlene", "Darlene"), ("edison", "Edison"), ("vinita", "Vinita")]


def font(px, bold=True):
    for name in ("arialbd.ttf" if bold else "arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def fit(img, width):
    r = width / img.width
    return img.resize((width, max(1, round(img.height * r))), Image.LANCZOS)


def panel(title, sub, bg):
    h = 74
    p = Image.new("RGBA", (W, h), bg)
    d = ImageDraw.Draw(p)
    d.text((PAD, 14), title, font=font(26), fill=INK if bg == PAPER_BG else (238, 240, 246, 255))
    d.text((PAD, 46), sub, font=font(15, False), fill=MUTED)
    return p


def main():
    parts = []
    head = Image.new("RGBA", (W, 96), PAPER_BG)
    hd = ImageDraw.Draw(head)
    hd.text((PAD, 20), "Sokoban  /  full render", font=font(38), fill=INK)
    hd.text((PAD, 66), "two tile styles, a shelf, one hero avatar, six suspects - all drawn through aseprite-mcp",
            font=font(16, False), fill=MUTED)
    parts.append(head)

    parts.append(panel("A", "shaded 32x32 set, tiled into a mock level - bevelled stone, cool walls, warm crates", PAPER_BG))
    parts.append(fit(Image.open(os.path.join(ART, "scene.png")).convert("RGB").convert("RGBA"), W))

    parts.append(panel("B", "Murdoku-style flat set, same level - pastel fills, 2px ink, no ramps", PAPER_BG))
    parts.append(fit(Image.open(os.path.join(ART, "scene_murdoku.png")).convert("RGB").convert("RGBA"), W))

    parts.append(panel("C", "flat set at 4x - surfaces shown as they actually tile (2x2), objects alone", DARK_BG))
    # floor and wall carry their ink grid on one edge only, so a single tile
    # looks like it has a stray black border; 2x2 shows the real read
    scale = 3
    surfaces = [("floor", 2), ("wall", 2), ("goal", 2)]
    objects = ["box", "player", "shelf"]
    cell = 32 * scale
    strip = Image.new("RGBA", (W, cell + 2 * 12), DARK_BG)
    x = 14
    for t, rep in surfaces:
        base = Image.open(os.path.join(ART, "murdoku", "tiles", f"{t}_1x.png")).convert("RGBA")
        patch = Image.new("RGBA", (32 * rep, 32 * rep))
        for ry in range(rep):
            for rx in range(rep):
                patch.alpha_composite(base, (rx * 32, ry * 32))
        strip.alpha_composite(patch.resize((patch.width * scale, patch.height * scale),
                                           Image.NEAREST), (x, 12))
        x += patch.width * scale + 16
    for t in objects:
        im = Image.open(os.path.join(ART, "murdoku", "tiles", f"{t}_1x.png")).convert("RGBA")
        strip.alpha_composite(im.resize((cell, cell), Image.NEAREST), (x, 12))
        x += cell + 16
    parts.append(strip)

    parts.append(panel("D", "suspect roster at 2x - each skull is its own authored (y, half-width) profile", DARK_BG))
    cell = 128
    row = Image.new("RGBA", (W, cell + 34), DARK_BG)
    rd = ImageDraw.Draw(row)
    gap = (W - len(ROSTER) * cell) // (len(ROSTER) + 1)
    x = gap
    for slug, name in ROSTER:
        im = Image.open(os.path.join(ART, "avatars", f"{slug}_1x.png")).convert("RGBA")
        row.alpha_composite(im.resize((cell, cell), Image.NEAREST), (x, 0))
        bb = rd.textbbox((0, 0), name, font=font(14, False))
        rd.text((x + (cell - bb[2] + bb[0]) // 2, cell + 6), name, font=font(14, False),
                fill=(226, 228, 236, 255))
        x += cell + gap
    parts.append(row)

    parts.append(panel("E", "hero avatar at 1x (64px) and 4x - featureless bust, the shape carries the read", PAPER_BG))
    av = Image.open(os.path.join(ART, "murdoku", "avatar_player_4x.png")).convert("RGBA")
    duo = Image.new("RGBA", (W, av.height + 2 * PAD), PAPER_BG)
    duo.alpha_composite(av, (PAD, PAD))
    duo.alpha_composite(av.resize((64, 64), Image.LANCZOS), (PAD * 2 + av.width + 40, av.height - 64 + PAD))
    duo.alpha_composite(av.resize((128, 128), Image.LANCZOS), (PAD * 2 + av.width + 150, PAD))
    parts.append(duo)

    total = sum(p.height for p in parts) + PAD * (len(parts) - 1)
    out = Image.new("RGBA", (W, total), (30, 32, 40, 255))
    y = 0
    for p in parts:
        out.alpha_composite(p, (0, y))
        y += p.height + PAD
    dest = os.path.join(ART, "overview.png")
    out.convert("RGB").save(dest)
    print(f"overview.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
