"""Furniture and fittings for the flat floor-plan set.

Scale: one cell is 32px and stands for one metre, so a piece's pixel size IS its
real footprint -- bed_double is 64x64 because a double bed is 1.8 x 2.0 m and
takes two cells either way. That is what makes a plan readable rather than a
grid of icons. There are two size classes: furniture, sized from the real
object, and the 摆件 (vase / bowl / books / cushion / mat) at half a cell, which
exist to sit ON a surface or on the floor and are drawn on their own z layer by
`gen_flatplan.py`. A 摆件 that is not on something is a bug, and that file's
`audit()` says so rather than leaving it to the eye.

Style: the Murdoku rules the tiles already follow -- flat fills, one lighter
band, 2px ink, no ramps, and nothing outside `gen_murdoku`'s palette. Every
piece is drawn into its own `Piece` buffer, then emitted as an editable
.aseprite plus a 1x PNG by one dofile'd Lua script (the stdio call-plan path
launches an Aseprite per call and stalls on this machine).

Run:  python tools/gen_furniture.py --lua        # writes furniture_gen.lua
      ...then dofile it through the aseprite MCP, and
      python tools/gen_furniture.py --contact    # a review sheet of every piece
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CELL = 32
OUT = "tiles/furniture"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gm = _load("gen_murdoku")

INK = gm.INK
WOOD, WOOD_HI = gm.OCHRE, gm.OCHRE_HI
CLOTH, CLOTH_HI = gm.TEAL, gm.TEAL_HI
METAL, METAL_HI = gm.PERI, "#BFC6E2"
CERAMIC, STONE = gm.WHITE, gm.GRAY
LEAF, BLUSH = gm.MINT, gm.BLUSH
DARK, PLUM = gm.PURPLE, gm.BRICK
FLOOR = gm.LILAC


class Piece:
    """A variable-size sprite buffer with the house's ink pass."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def set(self, x, y, col):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[(x, y)] = col
        return self

    def rect(self, x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, col)
        return self

    def frame(self, x0, y0, x1, y1, col):
        for x in range(x0, x1 + 1):
            self.set(x, y0, col).set(x, y1, col)
        for y in range(y0, y1 + 1):
            self.set(x0, y, col).set(x1, y, col)
        return self

    def disc(self, cx, cy, rx, ry, col):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1:
                    self.set(x, y, col)
        return self

    def arc(self, cx, cy, r, lo, hi, col, thick=2):
        """Part of a ring, `lo`..`hi` in degrees -- the door swing."""
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if abs(d - r) <= thick / 2.0:
                    a = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx)) % 360
                    if lo <= a <= hi:
                        self.set(x, y, col)
        return self

    def ink(self, col=INK, width=2):
        """Dilate `width` px of ink outward from the silhouette.

        Scans each filled pixel's neighbourhood rather than testing every empty
        pixel against every filled one -- the latter is O(n^2) and a 96x32 sofa
        takes minutes that way. Same square 5x5 growth the wall pieces use.
        """
        occ = set(self.px)
        ring = {}
        for ox, oy in occ:
            for dy in range(-width, width + 1):
                for dx in range(-width, width + 1):
                    if not dx and not dy:
                        continue
                    x, y = ox + dx, oy + dy
                    k = (x, y)
                    # clamp to this piece's own box: a piece that touches its
                    # edge is butting against a neighbour, and the neighbour
                    # supplies the ink on its side -- same rule as a wall arm
                    # that leaves its cell without a cap
                    if 0 <= x < self.w and 0 <= y < self.h and k not in occ:
                        ring[k] = col
        self.px.update(ring)
        return self

    def pixels(self):
        return [{"x": x, "y": y, "color": c} for (x, y), c in sorted(self.px.items())]

    def box(self):
        xs = [x for x, _ in self.px]
        ys = [y for _, y in self.px]
        return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------- beds
def bed_double():
    p = Piece(64, 64)
    p.rect(2, 2, 61, 61, WOOD)                    # frame
    p.rect(2, 2, 61, 5, WOOD_HI)                  # headboard side, lit
    p.rect(6, 8, 57, 58, CERAMIC)                 # mattress
    for x0, x1 in ((6, 30), (33, 57)):            # two pillows
        p.rect(x0, 10, x1, 19, BLUSH)
        p.rect(x0, 10, x1, 12, LEAF)
    p.rect(6, 26, 57, 58, CLOTH)                  # duvet
    p.rect(6, 26, 57, 28, CLOTH_HI)               # its turned-down edge
    p.ink()
    return p


def bed_single():
    p = Piece(32, 64)
    p.rect(2, 2, 29, 61, WOOD)
    p.rect(2, 2, 29, 5, WOOD_HI)
    p.rect(5, 8, 26, 58, CERAMIC)
    p.rect(5, 10, 26, 19, BLUSH)
    p.rect(5, 10, 26, 12, LEAF)
    p.rect(5, 26, 26, 58, CLOTH)
    p.rect(5, 26, 26, 28, CLOTH_HI)
    p.ink()
    return p


# ------------------------------------------------------------ storage
def wardrobe():
    p = Piece(64, 32)
    p.rect(2, 2, 61, 29, WOOD)
    p.rect(2, 2, 61, 5, WOOD_HI)
    p.rect(31, 5, 32, 29, INK)                    # the split between doors
    for x in (28, 35):
        p.rect(x, 14, x + 1, 19, METAL)           # handles
    p.ink()
    return p


def shelf_unit():
    p = Piece(64, 32)
    p.rect(2, 2, 61, 29, WOOD)
    p.rect(2, 2, 61, 4, WOOD_HI)
    for y in (11, 20):
        p.rect(4, y, 59, y + 1, INK)              # shelf boards
    for x, c in ((8, CLOTH), (16, BLUSH), (24, LEAF), (40, METAL), (50, PLUM)):
        p.rect(x, 6, x + 5, 10, c)                # books above the first board
        p.rect(x + 2, 15, x + 7, 19, c)
    p.ink()
    return p


def dresser():
    p = Piece(64, 32)
    p.rect(2, 2, 61, 29, WOOD)
    p.rect(2, 2, 61, 4, WOOD_HI)
    for y in (10, 18, 26):
        p.rect(3, y, 60, y + 1, INK)              # drawer gaps
    for y in (6, 14, 22):
        p.rect(28, y + 1, 35, y + 2, METAL)       # pulls
    p.ink()
    return p


# --------------------------------------------------------- living room
def sofa():
    """A two-seater: 64x32 = two cells. It was 96x32 (three cells) until the user
    asked for two, which is why the seam count is one and not two."""
    p = Piece(64, 32)
    p.rect(2, 2, 61, 29, CLOTH)
    p.rect(2, 2, 61, 9, CLOTH_HI)                 # backrest
    p.rect(2, 2, 11, 29, CLOTH)                   # arms
    p.rect(52, 2, 61, 29, CLOTH)
    p.frame(2, 2, 11, 29, INK)
    p.frame(52, 2, 61, 29, INK)
    p.rect(30, 11, 31, 28, INK)                   # the seam between the two seats
    p.rect(13, 11, 50, 12, CLOTH_HI)
    p.ink()
    return p


def coffee_table():
    p = Piece(48, 32)
    p.rect(2, 2, 45, 29, WOOD)
    p.rect(2, 2, 45, 6, WOOD_HI)
    p.frame(8, 9, 39, 22, INK)                    # the inlay
    p.rect(9, 10, 38, 21, METAL)
    p.ink()
    return p


def tv_cabinet():
    p = Piece(64, 32)
    p.rect(2, 14, 61, 29, WOOD)                   # the stand
    p.rect(2, 14, 61, 16, WOOD_HI)
    p.rect(10, 2, 53, 13, DARK)                   # screen
    p.frame(10, 2, 53, 13, INK)
    for i in range(4):
        p.set(14 + i, 4 + i, METAL_HI)            # a glint
    p.ink()
    return p


def rug():
    p = Piece(96, 64)
    p.rect(1, 1, 94, 62, LEAF)
    p.frame(4, 4, 91, 59, BLUSH)
    p.frame(8, 8, 87, 55, BLUSH)
    for x in range(12, 86, 6):
        p.rect(x, 30, x + 2, 33, CERAMIC)         # a woven band
    p.ink()
    return p


def plant():
    p = Piece(32, 32)
    p.rect(9, 22, 22, 29, PLUM)                   # pot
    p.rect(9, 22, 22, 23, DARK)                   # its rim, in shadow
    p.disc(16, 13, 10, 10, LEAF)                  # foliage
    p.disc(10, 10, 5, 5, CLOTH_HI)                # catching the light
    p.rect(15, 6, 16, 21, WOOD)                   # stem
    p.ink()
    return p


# ------------------------------------------------------------ dining
def dining_table():
    p = Piece(64, 64)
    p.rect(4, 4, 59, 59, WOOD)
    p.rect(4, 4, 59, 10, WOOD_HI)
    p.frame(10, 10, 53, 53, INK)
    p.rect(11, 11, 52, 52, WOOD)
    p.ink()
    return p


def chair():
    p = Piece(32, 32)
    p.rect(6, 6, 25, 25, WOOD)                    # seat
    p.rect(6, 6, 25, 9, DARK)                     # backrest along the top
    p.rect(6, 11, 25, 12, WOOD_HI)
    p.ink()
    return p


# ----------------------------------------------------------- kitchen
def stove():
    p = Piece(32, 32)
    p.rect(2, 2, 29, 29, METAL)
    p.rect(2, 2, 29, 5, METAL_HI)
    for cx, cy in ((10, 12), (21, 12), (10, 22), (21, 22)):
        p.disc(cx, cy, 4, 4, DARK)
        p.disc(cx, cy, 2, 2, STONE)
    p.ink()
    return p


def sink():
    p = Piece(32, 32)
    p.rect(2, 2, 29, 29, METAL)
    p.rect(2, 2, 29, 5, METAL_HI)
    p.rect(7, 10, 24, 25, CERAMIC)
    p.frame(7, 10, 24, 25, INK)
    p.rect(14, 5, 17, 9, STONE)                   # tap
    p.ink()
    return p


def fridge():
    p = Piece(32, 32)
    p.rect(2, 2, 29, 29, METAL)
    p.rect(2, 2, 29, 6, METAL_HI)
    p.rect(2, 14, 29, 15, INK)                    # freezer split
    p.rect(25, 8, 26, 12, CERAMIC)                # handles
    p.rect(25, 18, 26, 22, CERAMIC)
    p.ink()
    return p


# ---------------------------------------------------------- bathroom
def bathtub():
    p = Piece(64, 32)
    p.rect(2, 2, 61, 29, CERAMIC)
    p.rect(2, 2, 61, 5, METAL_HI)
    p.rect(7, 8, 56, 24, LEAF)                    # water
    p.frame(7, 8, 56, 24, INK)
    p.rect(28, 2, 35, 4, STONE)                   # taps at the wide end
    p.ink()
    return p


def toilet():
    p = Piece(32, 32)
    p.rect(4, 2, 27, 9, CERAMIC)                  # cistern
    p.disc(16, 19, 9, 10, CERAMIC)
    p.disc(16, 19, 6, 7, LEAF)
    p.ink()
    return p


def basin():
    p = Piece(32, 32)
    p.rect(5, 12, 26, 27, CERAMIC)
    p.rect(5, 12, 26, 14, METAL_HI)
    p.rect(14, 5, 17, 12, STONE)                  # pillar tap
    p.disc(16, 21, 4, 3, LEAF)
    p.ink()
    return p


# Doors and windows used to be defined here. They are wall-mounted, not
# furniture, so they now live with the wall generator (`gen_walls.OPENINGS`),
# which draws them in both styles -- kept in one place is the whole reason the
# flat set was the only one that had them.

def vase():
    """A 摆件: half a cell, meant to be drawn on top of a surface, not on the floor."""
    p = Piece(16, 16)
    p.rect(5, 8, 10, 13, CERAMIC)                  # the jug
    p.rect(5, 8, 10, 8, METAL_HI)                  # its lit rim
    p.rect(7, 3, 8, 7, LEAF)                       # stems
    p.disc(8, 3, 2, 2, BLUSH)                      # the bloom
    p.ink(width=1)
    return p


def bowl():
    p = Piece(16, 16)
    p.disc(8, 10, 5, 3, CERAMIC)
    p.disc(8, 9, 3, 2, METAL_HI)
    p.disc(6, 8, 1, 1, LEAF)                       # fruit
    p.disc(9, 8, 1, 1, PLUM)
    p.ink(width=1)
    return p


def books():
    """A stack, brightest on top so it reads with the key light."""
    p = Piece(16, 16)
    p.rect(3, 9, 12, 11, DARK)
    p.rect(2, 6, 13, 8, CLOTH)
    p.rect(4, 3, 11, 5, BLUSH)
    p.rect(4, 3, 11, 3, CERAMIC)
    p.ink(width=1)
    return p


def cushion():
    """Contrasts with the sofa it lies on: same-colour read as a recess, not a cushion."""
    p = Piece(16, 16)
    p.rect(2, 2, 13, 13, BLUSH)
    p.rect(4, 4, 11, 11, CERAMIC)                  # the lit face of the pad
    p.rect(4, 9, 11, 11, BLUSH)                    # its lower half back in shade
    p.ink(width=1)
    return p


def mat():
    """A floor covering like `rug`: it goes under the furniture, not over it.

    The first pass drew it as a row of ribs and it read as a radiator on the wall
    -- same colour, same spacing as the wall band's crest. It now speaks the rug's
    language (fill plus two inset frames) so the two floor textiles are clearly
    the same kind of object.
    """
    p = Piece(48, 16)
    p.rect(2, 2, 45, 13, CLOTH)
    p.frame(4, 4, 43, 11, CLOTH_HI)
    p.frame(7, 6, 40, 9, BLUSH)
    p.ink(width=1)
    return p


PIECES = {
    "bed_double": bed_double, "bed_single": bed_single,
    "wardrobe": wardrobe, "dresser": dresser, "shelf_unit": shelf_unit,
    "sofa": sofa, "coffee_table": coffee_table, "tv_cabinet": tv_cabinet,
    "rug": rug, "plant": plant,
    "dining_table": dining_table, "chair": chair,
    "stove": stove, "sink": sink, "fridge": fridge,
    "bathtub": bathtub, "toilet": toilet, "basin": basin,
    # the 摆件 class: half a cell, and by contract drawn ON TOP of a surface
    "vase": vase, "bowl": bowl, "books": books, "cushion": cushion, "mat": mat,
}


def emit_lua():
    rows = []
    for name, fn in PIECES.items():
        p = fn()
        rows.append((name, p.w, p.h, p.pixels()))
    out = ["-- generated by tools/gen_furniture.py -- do not edit by hand.",
           "-- Floor-plan furniture: 32px = 1 metre, so each piece's size is its",
           "-- real footprint. Flat fills, one lighter band, 2px ink, Murdoku palette.",
           "local DIR = 'E:/Material/material-sokoban/tiles/furniture/'",
           "local function col(h)",
           "  return Color(tonumber(string.sub(h, 2, 3), 16),",
           "               tonumber(string.sub(h, 4, 5), 16),",
           "               tonumber(string.sub(h, 6, 7), 16), 255)",
           "end",
           "local function save_png(spr, path)",
           "  pcall(os.remove, path)",
           "  spr:saveCopyAs(path)",
           "  local fh = io.open(path, 'rb')",
           "  if not fh then error('failed to write ' .. path) end",
           "  fh:close()",
           "end",
           "local PIECES = {"]

    def tbl(px):
        return ",\n      ".join('{%d,%d,"%s"}' % (p["x"], p["y"], p["color"]) for p in px)

    for name, w, h, px in rows:
        out.append('  { name="%s", w=%d, h=%d, px={\n      %s } },' % (name, w, h, tbl(px)))
    out.append("}")
    out.append(r"""
pcall(os.mkdir, DIR)
local done = 0
for _, t in ipairs(PIECES) do
  local spr = Sprite(t.w, t.h)
  spr.layers[1].name = 'art'
  local img = spr.cels[1].image
  for _, e in ipairs(t.px) do img:putPixel(e[1], e[2], col(e[3])) end
  local stem = DIR .. t.name
  pcall(os.remove, stem .. '.aseprite')
  spr:saveAs(stem .. '.aseprite')
  save_png(spr, stem .. '_1x.png')
  spr:close()
  done = done + 1
end
print('FURNITURE_OK pieces=' .. done)""")
    p = os.path.join(HERE, "furniture_gen.lua")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return p, len(rows)


def raster(piece):
    """A piece as an RGBA image at 1x -- the same pixels the .aseprite holds."""
    from PIL import Image
    img = Image.new("RGBA", (piece.w, piece.h), (0, 0, 0, 0))
    for q in piece.pixels():
        img.putpixel((q["x"], q["y"]),
                     tuple(int(q["color"][j:j + 2], 16) for j in (1, 3, 5)) + (255,))
    return img


# What a piece stands on. This is a property of the piece, not of one floor plan,
# so it lives beside the roster: -2 goes under the furniture (a rug, a mat), 0 is
# furniture, 1 is a small thing lying on a surface. `gen_flatplan` imports it.
FLOOR_LEVEL, SURFACE = -2, 1
LAYER_NAME = {FLOOR_LEVEL: "floor covering, drawn under the furniture",
              0: "furniture, placed on the floor",
              SURFACE: "ornament, drawn on top of a surface piece"}
LAYER = {"rug": FLOOR_LEVEL, "mat": FLOOR_LEVEL,
         "vase": SURFACE, "bowl": SURFACE, "books": SURFACE, "cushion": SURFACE}


def layer_of(name):
    return LAYER.get(name, 0)


def manifest():
    """One resource per piece: a JSON index, and a byte check that each file on
    disk is what the generator draws.

    Furniture is not an atlas -- an engine places each piece as its own object, so
    the deliverable is one `.aseprite` + one PNG per piece plus an index saying
    what each is. The check is the point of running it: a stale PNG on disk looks
    exactly like a current one, and this repo has been fooled by that before.
    """
    from PIL import Image
    dirpath = os.path.join(ROOT, OUT)
    pieces, stale = {}, []
    for name, fn in sorted(PIECES.items()):
        p = fn()
        png, src = f"{name}_1x.png", f"{name}.aseprite"
        for f in (png, src):
            if not os.path.exists(os.path.join(dirpath, f)):
                stale.append(f"{name}: {f} missing -- run the emitted Lua through the MCP")
        if os.path.exists(os.path.join(dirpath, png)):
            disk = Image.open(os.path.join(dirpath, png)).convert("RGBA")
            want = raster(p)
            if disk.size != want.size or disk.tobytes() != want.tobytes():
                stale.append(f"{name}: {png} is not what the generator draws")
        cols = {c for c in p.px.values()}
        pieces[name] = {
            "png": png, "aseprite": src,
            "px": [p.w, p.h],
            "cells": [round(p.w / CELL, 2), round(p.h / CELL, 2)],
            "layer": layer_of(name), "layer_means": LAYER_NAME[layer_of(name)],
            "colours": len(cols),
        }
        print("  %-14s %-12s cells %-9s layer %+d  colours=%d"
              % (name, png, "%sx%s" % tuple(pieces[name]["cells"]),
                 layer_of(name), len(cols)))
    doc = {
        "cell_px": CELL, "cell_metres": 1,
        "anchor": "top-left of the footprint, placed on the cell grid",
        "ink": "2px house outline, dilated inside the piece's own box, so a piece "
               "never bleeds ink into the neighbouring cell",
        "layers": {str(k): v for k, v in LAYER_NAME.items()},
        "piece_count": len(pieces),
        "pieces": pieces,
    }
    with open(os.path.join(dirpath, "furniture.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f"{OUT}/furniture.json  pieces={len(pieces)}")
    if stale:
        for line in stale:
            print("STALE:", line)
        raise SystemExit(f"{len(stale)} furniture resource problem(s)")


def contact():
    """A review sheet: every piece at 2x on the paper tone, in a grid."""
    from PIL import Image
    scale, pad = 2, 10
    rendered = {n: fn() for n, fn in PIECES.items()}
    cols = 6
    rows = (len(rendered) + cols - 1) // cols
    cw = max(p.w for p in rendered.values()) * scale + pad * 2
    ch = max(p.h for p in rendered.values()) * scale + pad * 2 + 16
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (242, 240, 247, 255))
    for i, (name, p) in enumerate(sorted(rendered.items())):
        img = raster(p).resize((p.w * scale, p.h * scale), Image.NEAREST)
        r, c = divmod(i, cols)
        sheet.alpha_composite(img, (c * cw + pad, r * ch + pad))
    dest = os.path.join(ROOT, "tiles", "furniture_contact.png")
    sheet.save(dest)
    for name, p in sorted(rendered.items()):
        cols_used = {c for c in p.px.values()}
        print(f"  {name:14s} {p.w:3d}x{p.h:<3d} cells {p.w / CELL:.1f}x{p.h / CELL:.1f}"
              f"  colours={len(cols_used)}")
    print(f"furniture_contact.png {sheet.width}x{sheet.height}")


if __name__ == "__main__":
    if "--lua" in sys.argv:
        p, n = emit_lua()
        print(f"{os.path.basename(p)} written for {n} pieces")
    elif "--contact" in sys.argv:
        contact()
    elif "--manifest" in sys.argv:
        manifest()
    else:
        print(__doc__)
