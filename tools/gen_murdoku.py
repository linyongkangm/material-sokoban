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
    # The 2px ink grid this tile used to carry on its top and left edges is
    # gone on purpose: the wall is a grid edge now, so a black line means
    # "there is a wall here" and nothing else. A floor that draws its own black
    # frame re-creates the graph-paper read the redesign was for.
    return g


# ------------------------------------------------------------------- wall
# No wall cell here either -- see the note in gen_sokoban.py. The flat set's
# walls are the same seven edge pieces, drawn by tools/gen_walls.py under the
# flat rules (one fill, one lighter band, 2px ink, no ramps).

# -------------------------------------------------------------------- box
def tile_box():
    g = Grid()
    # 18px of fill, because this style adds a 2px ink ring *outside* the shape:
    # the drawn footprint lands on 5..26, i.e. 22px with a 5px margin, which is
    # exactly how far an edge wall reaches into the cell. The shaded crate needs
    # no such allowance -- its outline sits inside its own silhouette.
    g.round_rect(7, 7, 24, 24, 3, OCHRE)
    g.rect(7, 7, 24, 9, OCHRE_HI)                # one flat highlight band
    g.border(10, 10, 21, 21, INK)                # inset plank frame in ink
    g.rect(14, 14, 17, 17, INK)                  # centre plate
    for nx, ny in ((10, 10), (21, 10), (10, 21), (21, 21)):
        g.rect(nx, ny, nx + 1, ny + 1, INK)      # nail heads
    return g


# ------------------------------------------------------------------- goal
def tile_goal():
    g = tile_floor()
    # darken the floor tones in place so the plank seams survive on the marked
    # plate; overwriting the whole cell would erase them. It used to start at
    # (2, 2) to leave the tile's ink frame alone -- that frame is gone now.
    for y in range(N):
        for x in range(N):
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


def emit_lua(only=None):
    """Batch-Lua builder for the flat cell tiles (the stdio call-plan path
    stalls on this machine; one dofile draws the whole subset)."""
    rows = []
    for name in TILES:
        if only and name not in only:
            continue
        outline, body = paint(name)
        rows.append((name, body, outline))

    def tbl(px):
        return ",\n    ".join('{%d,%d,"%s"}' % (p["x"], p["y"], p["color"]) for p in px)

    out = ["-- generated by tools/gen_murdoku.py -- do not edit by hand.",
           "-- Flat pastel set, Murdoku rules: ink outlines, flat fills, one",
           "-- lighter band at most, no ramps. The floor no longer draws an ink",
           "-- grid: the wall is a grid edge, so a black line means a wall.",
           "local DIR = 'E:/Material/material-sokoban/tiles/murdoku/'",
           "local function col(h)",
           "  return Color(tonumber(string.sub(h, 2, 3), 16),",
           "               tonumber(string.sub(h, 4, 5), 16),",
           "               tonumber(string.sub(h, 6, 7), 16), 255)",
           "end",
           "-- saveCopyAs does not abort on a failed write: delete, then prove it.",
           "local function save_png(spr, path)",
           "  pcall(os.remove, path)",
           "  spr:saveCopyAs(path)",
           "  local fh = io.open(path, 'rb')",
           "  if not fh then error('failed to write ' .. path) end",
           "  fh:close()",
           "end",
           "local TILES = {"]
    for name, body, outline in rows:
        out.append('  { name="%s", flat={\n    %s },\n    ink={\n    %s } },'
                   % (name, tbl(body), tbl(outline) or "0"))
    out.append("}")
    out.append(r"""
local done = 0
for _, t in ipairs(TILES) do
  local spr = Sprite(32, 32)
  spr.layers[1].name = 'flat'
  local img = spr.cels[1].image
  for _, e in ipairs(t.flat) do img:putPixel(e[1], e[2], col(e[3])) end
  if #t.ink > 1 then
    local lyr = spr:newLayer()
    lyr.name = 'ink'
    local im2 = Image(32, 32, spr.colorMode)
    for _, e in ipairs(t.ink) do im2:putPixel(e[1], e[2], col(e[3])) end
    spr:newCel(lyr, spr.frames[1], im2, Point(0, 0))
  end
  local stem = DIR .. t.name
  pcall(os.remove, stem .. '.aseprite')
  spr:saveAs(stem .. '.aseprite')
  save_png(spr, stem .. '_1x.png')
  spr:close()
  done = done + 1
end
print('TILES_FLAT_OK n=' .. done)""")
    p = os.path.join(HERE, "tiles_gen_flat.lua")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return p, [r[0] for r in rows]


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "tiles"
    if mode == "--lua":
        only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
        p, names = emit_lua(only)
        print(f"{os.path.basename(p)} written for {','.join(names)}")
        sys.exit(0)
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
