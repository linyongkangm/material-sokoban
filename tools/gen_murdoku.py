"""Sokoban tile set redrawn in the Murdoku.com art style.

Style spec lifted from https://murdoku.com/play/puzzle-book-club-very-easy:
  - ink #191922 outlines, heavy (2px at 32px) around every object and between
    tiles -- their board reads as flat pastel rooms separated by thick black
  - FLAT fills: no bevels, no light/shadow ramps, at most one lighter band
  - muted pastel room palette (periwinkle / lilac / mint / blush / teal /
    purple / brick), white for highlights
  - simple rounded geometry + thin ink line detail instead of texture
This is the opposite of the shaded set in ../gen_sokoban.py, so shading is
deliberately absent -- do not "fix" it by adding ramps back.
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("gen_sokoban", os.path.join(HERE, "gen_sokoban.py"))
gs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gs)

N = gs.N
Grid = gs.Grid
OUT = "tiles/murdoku"

INK = "#191922"
INK_SOFT = "#2F2E3D"
INK_DARK = "#0E0E15"
PAPER = "#F2F0F7"
LILAC = "#E3DCF0"
LILAC_SEAM = "#CFC3E2"
PERI = "#A3ABD2"
MINT = "#B1E2DE"
MINT_DK = "#8FCBC6"
BLUSH = "#E0AFAF"
OCHRE = "#E0A93F"
OCHRE_HI = "#F1CB72"
BRICK = "#A55142"
TEAL = "#5CACB5"
TEAL_HI = "#7CC3CB"
PURPLE = "#68497F"
HAIR = "#33302E"
SKIN = "#E8B48C"
WHITE = "#FEFEFE"
GRAY = "#A9A9A9"


def outline_n(g, col, n=2):
    """Chebyshev-distance ring of width n around the whole silhouette."""
    solid = {(x, y) for y in range(N) for x in range(N) if g.at(x, y) is not None}
    ring = []
    for y in range(N):
        for x in range(N):
            if (x, y) in solid:
                continue
            best = min((max(abs(x - sx), abs(y - sy)) for sx, sy in solid), default=99)
            if best <= n:
                ring.append({"x": x, "y": y, "color": col})
    return ring


def stamp_outline(g, shape, col, n=1):
    """Outline one shape *in place* over whatever g already holds.

    Used for markers that sit on a filled tile, where the silhouette trick in
    outline_n cannot reach. Only paints over existing pixels, so the shape's
    border never spills into transparent space.
    """
    solid = {(x, y) for y in range(N) for x in range(N) if shape.at(x, y) is not None}
    for y in range(N):
        for x in range(N):
            if (x, y) in solid or g.at(x, y) is None:
                continue
            best = min((max(abs(x - sx), abs(y - sy)) for sx, sy in solid), default=99)
            if best <= n:
                g.set(x, y, col)


# ------------------------------------------------------------------ floor
def tile_floor():
    g = Grid()
    g.rect(0, 0, N - 1, N - 1, LILAC)
    # one-direction planks: seams run full height so they stay continuous when
    # tiled. Cross-hatching here fought the 2px ink grid and made every cell
    # read as a window pane.
    for x in (10, 21):
        for y in range(N):
            g.set(x, y, LILAC_SEAM)
    # thick ink grid: top and left only, so tiling yields one 2px line
    g.rect(0, 0, N - 1, 1, INK)
    g.rect(0, 0, 1, N - 1, INK)
    return g


# ------------------------------------------------------------------- wall
def tile_wall():
    g = Grid()
    g.rect(0, 0, N - 1, N - 1, INK)
    g.rect(0, 0, N - 1, 2, INK_SOFT)             # flat cap band, the only 2nd tone
    g.rect(0, 29, N - 1, 31, INK_DARK)
    return g


# -------------------------------------------------------------------- box
def tile_box():
    g = Grid()
    g.round_rect(3, 3, 28, 28, 3, OCHRE)
    g.rect(3, 3, 28, 5, OCHRE_HI)                # one flat highlight band
    g.border(6, 6, 25, 25, INK)                  # inset plank frame in ink
    g.rect(14, 14, 17, 17, INK)                  # centre plate
    for nx, ny in ((6, 6), (25, 6), (6, 25), (25, 25)):
        g.rect(nx, ny, nx + 1, ny + 1, INK)      # nail heads
    return g


# ------------------------------------------------------------------- goal
def tile_goal():
    g = tile_floor()
    # darken the floor tones in place so the plank seams survive on the marked
    # plate; overwriting the whole cell would erase them
    for y in range(2, N):
        for x in range(2, N):
            c = g.at(x, y)
            if c == LILAC:
                g.set(x, y, "#DCD3EA")
            elif c == LILAC_SEAM:
                g.set(x, y, "#C6B9DC")
    ring = Grid()
    cx = cy = 15.5
    for y in range(N):
        for x in range(N):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= 9.0:
                ring.set(x, y, BRICK)
    stamp_outline(g, ring, INK, 1)
    for y in range(N):
        for x in range(N):
            if ring.at(x, y):
                g.set(x, y, ring.at(x, y))
    # a white centre block reads as a target and avoids the stair-step nubs a
    # drawn ring gets at its four cardinal points
    hole = Grid()
    hole.rect(13, 13, 18, 18, WHITE)
    stamp_outline(g, hole, INK, 1)
    for y in range(N):
        for x in range(N):
            if hole.at(x, y):
                g.set(x, y, hole.at(x, y))
    return g


# ----------------------------------------------------------------- player
def tile_player():
    """Arms and legs are split from the body by 1px of *transparency*: outline_n
    floods those gaps with ink, which is how Murdoku keeps flat same-colour
    limbs readable. Painting the seam directly would double its width.
    """
    g = Grid()
    g.round_rect(9, 8, 22, 17, 3, SKIN)                        # head
    g.round_rect(10, 4, 21, 9, 3, HAIR)                        # hair, narrower than the head
    g.rect(10, 10, 11, 11, HAIR).rect(20, 10, 21, 11, HAIR)    # sideburns tie it down
    g.rect(12, 13, 13, 14, INK).rect(18, 13, 19, 14, INK)      # dot eyes
    g.rect(15, 16, 16, 16, INK)                                # mouth
    g.round_rect(10, 19, 21, 27, 2, TEAL)                      # torso
    g.rect(6, 20, 25, 21, TEAL)                                # shoulder bar ties arms to body
    g.rect(6, 20, 25, 20, TEAL_HI)                             # one flat highlight band
    g.rect(5, 22, 8, 26, TEAL).rect(23, 22, 26, 26, TEAL)      # arms, ink gap at x=9 / x=22
    g.rect(5, 27, 8, 28, SKIN).rect(23, 27, 26, 28, SKIN)      # hands
    g.rect(12, 28, 14, 30, PURPLE).rect(17, 28, 19, 30, PURPLE)
    g.rect(10, 31, 15, 31, HAIR).rect(16, 31, 21, 31, HAIR)    # shoes
    return g


TILES = {
    "floor": tile_floor,
    "wall": tile_wall,
    "box": tile_box,
    "goal": tile_goal,
    "player": tile_player,
}
# objects that float on transparency get an ink border; tiles that fill the
# whole cell already carry their own grid line
OUTLINED = {"box", "player"}


def paint(name):
    """Return (ink_outline_pixels, flat_pixels) for one tile."""
    g = TILES[name]()
    outline = outline_n(g, INK, 2) if name in OUTLINED else []
    return outline, g.pixels()


def build(only=None):
    calls = []
    for name, fn in TILES.items():
        if only and name not in only:
            continue
        fname = f"{OUT}/{name}.aseprite"
        outline, body = paint(name)
        calls.append(["create_canvas", {"width": N, "height": N, "filename": fname}])
        calls.append(["add_layer", {"filename": fname, "layer_name": "ink"}])
        calls.append(["add_layer", {"filename": fname, "layer_name": "flat"}])
        calls.append(["draw_pixels_at", {"filename": fname, "layer_name": "ink",
                                         "frame_index": 1, "pixels": outline}])
        calls.append(["draw_pixels_at", {"filename": fname, "layer_name": "flat",
                                         "frame_index": 1, "pixels": body}])
        calls.append(["export_frame", {"filename": fname, "frame_index": 1,
                                       "output_filename": f"{OUT}/{name}_1x.png",
                                       "scale": 1}])
    return calls


def build_sheet():
    master = f"{OUT}/master.aseprite"
    calls = [["create_canvas", {"width": N * len(TILES), "height": N, "filename": master}]]
    calls.append(["add_layer", {"filename": master, "layer_name": "ink"}])
    calls.append(["add_layer", {"filename": master, "layer_name": "flat"}])
    ink, flat = [], []
    for i, name in enumerate(TILES):
        dx = i * N
        outline, body = paint(name)
        ink += [{"x": p["x"] + dx, "y": p["y"], "color": p["color"]} for p in outline]
        flat += [{"x": p["x"] + dx, "y": p["y"], "color": p["color"]} for p in body]
        calls.append(["create_slice", {"filename": master, "name": name,
                                       "x": dx, "y": 0, "width": N, "height": N}])
    calls.append(["draw_pixels_at", {"filename": master, "layer_name": "ink",
                                     "frame_index": 1, "pixels": ink}])
    calls.append(["draw_pixels_at", {"filename": master, "layer_name": "flat",
                                     "frame_index": 1, "pixels": flat}])
    calls.append(["export_frame", {"filename": master, "frame_index": 1,
                                   "output_filename": f"{OUT}/murdoku_sheet.png", "scale": 1}])
    calls.append(["export_frame", {"filename": master, "frame_index": 1,
                                   "output_filename": f"{OUT}/murdoku_sheet_4x.png", "scale": 4}])
    calls.append(["get_color_stats", {"filename": master, "frame_index": 1, "top": 30}])
    return calls


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "tiles"
    only = None
    os.makedirs(os.path.join(ROOT, OUT), exist_ok=True)
    if mode == "sheet":
        calls = build_sheet()
        out = os.path.join(HERE, "calls_murdoku_sheet.json")
    else:
        only = None if mode == "all" else set(mode.split(","))
        calls = build(only)
        out = os.path.join(HERE, "calls_murdoku.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(calls, fh)
    print(f"{out} -> {len(calls)} calls")
    for name in TILES:
        if only and name not in only:
            continue
        g = TILES[name]()
        cols = {}
        for p in g.pixels():
            cols[p["color"]] = cols.get(p["color"], 0) + 1
        print(f"  {name:7s} pixels={sum(cols.values()):5d} colors={len(cols)}")
