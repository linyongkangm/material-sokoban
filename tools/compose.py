"""Compose MCP-exported tiles into a contact sheet and a mock level.

Visual feedback is the step that decides whether the art is actually good:
contact.png shows every tile at 8x, scene.png tiles them into a real layout so
seam and palette cohesion problems show up.
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# compose.py [subdir] -- "murdoku" renders the flat-outline variant
SUB = sys.argv[1] if len(sys.argv) > 1 else ""
TILES_DIR = os.path.join(ROOT, "tiles", SUB) if SUB else os.path.join(ROOT, "tiles")
SUFFIX = f"_{SUB}" if SUB else ""
N = 32
ORDER = ["floor", "wall", "box", "goal", "player"]

MAP = [
    "############",
    "#.........o#",
    "#..$$......#",
    "#...##..o..#",
    "#...##.....#",
    "#..$....$..#",
    "#....@.....#",
    "#.o........#",
    "############",
]


def load(name, scale):
    p = os.path.join(TILES_DIR, f"{name}_1x.png")
    if not os.path.exists(p):
        sys.exit(f"missing {p} - run the MCP draw calls first")
    im = Image.open(p).convert("RGBA")
    return im.resize((N * scale, N * scale), Image.NEAREST)


def _bg():
    # the flat pastel set is shown on their paper tone, the shaded set on dark
    return (242, 240, 247, 255) if SUB == "murdoku" else (18, 20, 26, 255)


def is_surface(im):
    """A tile with no transparent pixel is a floor/wall surface.

    Surfaces keep their ink grid on one edge only so tiling yields a single
    line, which makes a lone tile look like it has a stray black border.
    2x2 is how they actually read in game, so that is how they get shown.
    """
    return im.getextrema()[3][0] == 255


def contact():
    scale, gap = 8, 8
    tiles = []
    for name in ORDER:
        im = load(name, 1)
        rep = 2 if is_surface(im) else 1
        if rep == 2:
            patch = Image.new("RGBA", (N * rep, N * rep))
            for ry in range(rep):
                for rx in range(rep):
                    patch.alpha_composite(im, (rx * N, ry * N))
            im = patch
        tiles.append((name, im.resize((im.width * scale, im.height * scale), Image.NEAREST)))

    w = sum(t.width for _, t in tiles) + gap * (len(tiles) + 1)
    tall = N * 2 * scale
    sheet = Image.new("RGBA", (w, tall + 2 * gap), _bg())
    x = gap
    for _, t in tiles:
        sheet.alpha_composite(t, (x, gap + (tall - t.height) // 2))
        x += t.width + gap
    sheet.save(os.path.join(TILES_DIR, f"contact{SUFFIX}.png"))
    marks = " ".join(n + ("[2x2]" if t.width == tall else "") for n, t in tiles)
    print(f"contact{SUFFIX}.png {sheet.width}x{sheet.height}  {marks}")


def scene():
    scale = 6
    cols, rows = len(MAP[0]), len(MAP)
    out = Image.new("RGBA", (cols * N * scale, rows * N * scale), _bg())
    floor = load("floor", scale)
    parts = {
        "#": load("wall", scale),
        ".": floor,
        "$": [floor, load("box", scale)],
        "o": [floor, load("goal", scale)],
        "@": [floor, load("player", scale)],
    }
    for r, line in enumerate(MAP):
        for c, ch in enumerate(line):
            p = parts.get(ch, floor)
            px, py = c * N * scale, r * N * scale
            for layer in (p if isinstance(p, list) else [p]):
                out.alpha_composite(layer, (px, py))
    out.save(os.path.join(TILES_DIR, f"scene{SUFFIX}.png"))
    print(f"scene{SUFFIX}.png {out.width}x{out.height}")


if __name__ == "__main__":
    contact()
    scene()
