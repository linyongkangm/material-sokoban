"""A two-bedroom, one-living-room flat, drawn as a furnished floor plan.

One cell is 32px and stands for one metre. Rooms are rectangles; walls are not
drawn by hand -- every edge between two cells that belong to different rooms (or
to the outside) becomes a wall segment, and the existing edge-wall set resolves
each grid node to exactly one of the 16 double-sided pieces via
`compose.arms_at` / `compose.piece_for`. A doorway is simply an absent segment:
the runs on either side already end in `wall_end_*`, which caps them.

So the plan is a *derived* artifact: change a room rectangle and the walls,
their corners, tees and caps all follow, which is the same parametric rule the
tiles and the sprites follow.

Stacking, bottom to top: floor -> floor coverings (rug, mat) -> furniture -> the
摆件 on the surface they sit on -> walls -> windows and door leaves -> labels.
Walls go over the furniture on purpose: in plan view the masonry is the fixed
structure and the pieces abut it. `LAYER` is the one place that says what stands
on what, and `audit()` refuses a surface piece with nothing under it.

    python tools/gen_flatplan.py            # writes tiles/flatplan.png
"""
import importlib.util
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TILES_DIR = os.path.join(ROOT, "tiles")


def _load(name, path=None):
    spec = importlib.util.spec_from_file_location(name, path or os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


c = _load("compose")                    # reuse the node -> piece resolution
gf = _load("gen_furniture")             # reuse the furniture footprints
N, CELL = c.N, c.N

# ---------------------------------------------------------------- rooms
# name, x0, y0, x1, y1 (inclusive, in cells). These tile the whole 11x9 grid:
# an unfurnished hole inside the bounding box reads as a drawing error, not as
# an L-shaped flat.
#
# The hall is a row, not a stub. It used to be 3 cells at the east end (x8..10,
# y3), which meant the front door opened into the corridor and the corridor's
# only way on was THROUGH THE KITCHEN -- the plan read "入户门进厨房". Taking the
# second bedroom's bottom row makes the hall run the width of the flat at y3, so
# the entrance reaches the living room directly and every other door hangs off
# the hall: bath, kitchen, 次卧.
ROOMS = [
    ("主卧", 0, 0, 3, 3),
    ("次卧", 4, 0, 7, 2),
    ("卫生间", 8, 0, 10, 2),
    ("过道", 4, 3, 10, 3),
    ("客厅", 0, 4, 6, 8),
    ("厨房", 7, 4, 10, 6),
    ("阳台", 7, 7, 10, 8),
]
COLS = max(r[3] for r in ROOMS) + 1
ROWS = max(r[4] for r in ROOMS) + 1


def room_of(x, y):
    if not (0 <= x < COLS and 0 <= y < ROWS):
        return None
    for name, x0, y0, x1, y1 in ROOMS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    return None


# ------------------------------------------------------------- wall graph
NEIGH = {"N": (0, -1), "S": (0, 1), "W": (-1, 0), "E": (1, 0)}


def seg_of(x, y, e):
    """The canonical id of the edge segment between this cell and its neighbour.

    Both cells see the same physical line, so doors and windows have to be keyed
    by the segment, not by (cell, edge) -- otherwise the neighbour re-adds the
    wall a doorway just removed. Node coordinates: an H segment sits above cell
    (x, y'), a V one to the left of cell (x', y).
    """
    if e == "N":
        return ("H", x, y)
    if e == "S":
        return ("H", x, y + 1)
    if e == "W":
        return ("V", x, y)
    return ("V", x + 1, y)


def node_of(seg):
    kind, a, b = seg
    return (a, b) if kind == "H" else (a, b)


# doorways: the segment is simply absent; the runs on either side end in
# wall_end_*, which already caps them. Each one is a room-to-room connection, so
# this list IS the flat's circulation graph -- read it as "you walk from A to B
# through here".
DOOR_SEGS = {seg_of(3, 3, "E"),      # 主卧 -> 过道（原来开在 (2,4) 那格，正对沙发背）
             seg_of(7, 3, "N"),      # 次卧 -> 过道
             seg_of(9, 3, "N"),      # 过道 -> 卫生间
             seg_of(9, 4, "N"),      # 过道 -> 厨房
             seg_of(7, 8, "W"),      # 阳台 -> 客厅
             seg_of(10, 3, "E")}     # 入户门 -> 过道
# openings: a gap in the wall with NO leaf. The hall and the living room are one
# space, so the way from the front door into the living room must not be a door
# you have to open -- and it is two cells wide, which is what a passage looks
# like. Only rooms that are really the same space get an opening; bedrooms, the
# bathroom and the kitchen keep doors.
OPEN_SEGS = {seg_of(4, 4, "N"),      # 过道 x4 -> 客厅
             seg_of(5, 4, "N")}      # 过道 x5 -> 客厅
# windows: the wall stays and the glass overlay goes on top of it
WINDOW_SEGS = [seg_of(1, 0, "N"), seg_of(2, 0, "N"), seg_of(0, 2, "W"),
               seg_of(5, 0, "N"), seg_of(6, 0, "N"),
               seg_of(9, 0, "N"), seg_of(10, 5, "E"),
               seg_of(0, 5, "W"), seg_of(0, 6, "W"),
               seg_of(2, 8, "S"), seg_of(4, 8, "S"),
               seg_of(8, 8, "S"), seg_of(9, 8, "S")]

H, V = set(), set()          # H[(x,y)] = line above cell (x,y); V[(x,y)] = left of it
for y in range(ROWS):
    for x in range(COLS):
        here = room_of(x, y)
        for e, (dx, dy) in NEIGH.items():
            seg = seg_of(x, y, e)
            if seg in DOOR_SEGS or seg in OPEN_SEGS:
                continue
            if room_of(x + dx, y + dy) == here:
                continue
            kind, a, b = seg
            (H if kind == "H" else V).add((a, b))

DOOR_LEAVES = list(DOOR_SEGS)

# ------------------------------------------------------------- furniture
# piece, anchor cell (top-left of its footprint). Sizes come from the asset, so
# a mistake here shows up as an overlap rather than a silent squeeze. Anchors may
# be fractional: a 摆件 is half a cell and has to land in the middle of the
# surface it belongs to.
# The layer a piece stands on belongs to the piece, not to this file, so it comes
# from gen_furniture -- `furniture.json` publishes the same table the plan obeys.
FLOOR_LEVEL, SURFACE = gf.FLOOR_LEVEL, gf.SURFACE
layer_of = gf.layer_of


FURNITURE = [
    # 主卧 (0..3, 0..3)
    ("bed_double", 0, 0), ("wardrobe", 2, 0), ("chair", 0, 3),
    ("plant", 0, 2),                              # under the west window
    ("cushion", 0.25, 3.25),
    ("books", 2.25, 0.25), ("vase", 3.25, 0.25),
    # 次卧 (4..7, 0..2): the dresser used to sit at (5,2) and the plant at (7,2),
    # both of which stood in the leaf of the doorway this room now shares with
    # the hall at x=7
    ("bed_single", 4, 0), ("shelf_unit", 5, 0), ("chair", 7, 0),
    ("dresser", 4, 2), ("plant", 7, 1),
    ("vase", 4.25, 2.25), ("cushion", 7.25, 0.25),
    # 卫生间 (8..10, 0..2)
    ("bathtub", 8, 0), ("toilet", 10, 0), ("basin", 10, 1),
    ("mat", 8.25, 1.25),                          # floor level: under, not over
    # 过道 (4..10, 3) is left clear: it is the entrance circulation, and the
    # first pass had a shelf blocking the front door
    # 客厅 (0..6, 4..8): lounge column on the west, dining block east of it
    ("rug", 0, 5),
    ("sofa", 0, 4), ("coffee_table", 1, 5), ("tv_cabinet", 0, 7),
    ("dining_table", 4, 5), ("chair", 3, 5), ("chair", 6, 5),
    ("chair", 3, 6), ("chair", 6, 6),
    ("shelf_unit", 3, 8), ("plant", 0, 8),          # plant moved off the 阳台 door
    ("cushion", 0.5, 4.25), ("cushion", 2.0, 4.25),
    ("books", 1.5, 5.25), ("vase", 4.75, 5.75), ("bowl", 0.25, 7.25),
    # 厨房 (7..10, 4..6)
    ("stove", 7, 4), ("sink", 8, 4), ("fridge", 10, 4), ("shelf_unit", 7, 6),
    ("bowl", 7.25, 6.25),
    # 阳台 (7..10, 7..8)
    ("plant", 7, 7), ("plant", 10, 7), ("coffee_table", 8, 7), ("chair", 8, 8),
    ("bowl", 8.25, 7.25),
]

SCALE = 4
# Every entry is a cell the room actually has free, so the type never lands on a
# bed or a shelf -- the first pass put 客厅 on top of the sofa and 过道 on the
# shelf. The render anchors on the cell centre, not its top-left corner; anchored
# on the corner, half of every label hung out over the cell to the west.
LABELS = {"主卧": (2, 2), "次卧": (6, 1), "卫生间": (9, 2), "过道": (7, 3),
          "客厅": (3, 7), "厨房": (9, 5), "阳台": (10, 8)}

def font(px):
    for name in ("msyhbd.ttc", "msyh.ttc", "arialbd.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def load_tile(name, scale):
    for d in (TILES_DIR, os.path.join(TILES_DIR, "furniture")):
        p = os.path.join(d, f"{name}_1x.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA")
            return im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    raise SystemExit(f"missing asset {name}_1x.png - run the generators first")


def area(name):
    for rname, x0, y0, x1, y1 in ROOMS:
        if rname == name:
            return (x1 - x0 + 1) * (y1 - y0 + 1)
    return 0


def footprint(name, ax, ay):
    """The piece's rect in cells, read out of the generated asset."""
    piece = gf.PIECES[name]()
    return (ax, ay, ax + piece.w / N, ay + piece.h / N)


def cells_of(x0, y0, x1, y1):
    """The cells a rect touches -- for the room containment and label checks."""
    for cy in range(int(math.floor(y0)), int(math.ceil(y1))):
        for cx in range(int(math.floor(x0)), int(math.ceil(x1))):
            yield cx, cy


def audit():
    """Catch the ways a plan lies.

    Furniture through a wall, two pieces on the same layer, a 摆件 with nothing
    under it, a doorway the furniture blocks, and a label sitting on any of those
    or outside the room it names. Footprints come from the assets, so an item that
    no longer fits its room fails here rather than quietly overlapping in the
    render. Overlap is judged per layer: a vase shares the dining table's cells on
    purpose, and two tables sharing them never is.
    """
    bad = []
    rects = []
    for name, ax, ay in FURNITURE:
        x0, y0, x1, y1 = footprint(name, ax, ay)
        rects.append((name, layer_of(name), x0, y0, x1, y1))
        home = room_of(int(math.floor(ax)), int(math.floor(ay)))
        for cx, cy in cells_of(x0, y0, x1, y1):
            if room_of(cx, cy) != home:
                bad.append(f"{name}@({ax},{ay}) leaves {home} into "
                           f"{room_of(cx, cy)} at ({cx},{cy})")
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if a[1] != b[1]:
                continue
            if a[2] < b[4] and b[2] < a[4] and a[3] < b[5] and b[3] < a[5]:
                bad.append(f"{a[0]}@({a[2]},{a[3]}) overlaps {b[0]}@({b[2]},{b[3]})")
    for name, layer, x0, y0, x1, y1 in rects:
        if layer != SURFACE:
            continue
        eps = 1e-9
        hosts = [o for o in rects
                 if o[1] == 0 and o[2] <= x0 + eps and o[3] <= y0 + eps
                 and o[4] >= x1 - eps and o[5] >= y1 - eps]
        if not hosts:
            bad.append(f"{name}@({x0},{y0}) is a surface piece with nothing under it")
    solid = {(cx, cy): name for name, layer, x0, y0, x1, y1 in rects if layer >= 0
             for cx, cy in cells_of(x0, y0, x1, y1)}
    # A doorway that the furniture blocks is the fifth way a plan lies. Three
    # cells have to be free: the two that the opening itself stands between, and
    # the extra one the leaf sweeps along the wall (it is 24px long, so it always
    # covers two cells, not the node's own one). Checking only the leaf side is
    # what let the 主卧 door pass while the living-room sofa sat in its way.
    for seg in sorted(DOOR_SEGS | OPEN_SEGS, key=str):
        kind, a, b = seg
        if kind == "H":                        # the line above cell (a, b-1)
            cells = [(a, b - 1), (a, b)]
        else:                                  # the line left of cell (a-1, b)
            cells = [(a - 1, b), (a, b)]
        if seg in DOOR_SEGS:                   # the leaf sweeps one cell further
            cells.append((a - 1, b - 1))
        for cell in cells:
            if cell in solid:
                word = "door" if seg in DOOR_SEGS else "opening"
                bad.append(f"{word}@{seg} is blocked by {solid[cell]} at {cell}")
    for name, (lx, ly) in LABELS.items():
        if room_of(lx, ly) != name:
            bad.append(f"label {name}@({lx},{ly}) is not inside {name}")
        if (lx, ly) in solid:
            bad.append(f"label {name}@({lx},{ly}) sits on furniture")
    return bad


def render():
    pad = 2                                   # room for the outer wall band
    w, h = (COLS + 2 * pad) * N * SCALE, (ROWS + 2 * pad) * N * SCALE
    out = Image.new("RGBA", (w, h), (242, 240, 247, 255))
    floor = load_tile("floor", SCALE)

    def at(cx, cy):
        # integer pixels: a half-cell offset is how a wall sits on the line, and
        # PIL refuses float paste boxes
        return (int((cx + pad) * N * SCALE), int((cy + pad) * N * SCALE))

    # 1. floors
    for y in range(ROWS):
        for x in range(COLS):
            out.alpha_composite(floor, at(x, y))
    # 2. everything standing on the floor, low layer first: floor coverings, then
    #    furniture, then the 摆件 on top of the surface they belong to
    for name, ax, ay in sorted(FURNITURE, key=lambda e: layer_of(e[0])):
        out.alpha_composite(load_tile(name, SCALE), at(ax, ay))
    # 3. walls: every node with segments resolves to one double-sided piece, and
    #    they land ON TOP of the furniture. In plan view the masonry is the fixed
    #    structure and the pieces abut it, so anything reaching the line has to be
    #    clipped by it -- drawing the pieces last let every bed, wardrobe and tub
    #    punch a hole in its own wall, and the frame read as broken segments with
    #    furniture in the gaps.
    unresolved = []
    for y in range(ROWS + 1):
        for x in range(COLS + 1):
            arms = c.arms_at(x, y, H, V)
            if not arms:
                continue
            nm = c.piece_for(arms)
            if nm is None:
                unresolved.append((x, y, "".join(sorted(arms))))
                continue
            px, py = at(x - 0.5, y - 0.5)
            out.alpha_composite(load_tile(nm, SCALE), (px, py))
    # 4. windows over the band, doors over the gaps -- both sit on the segment's
    # own node, i.e. centred on the grid line like the wall itself
    for seg in WINDOW_SEGS:
        kind, a, b = seg
        out.alpha_composite(load_tile("window_h" if kind == "H" else "window_v", SCALE),
                            at(a - 0.5, b - 0.5))
    for seg in DOOR_LEAVES:
        kind, a, b = seg
        # the two leaf assets are authored separately, not rotated: the leaf's
        # lit edge has to stay on the key-light side of whichever wall it lies on
        leaf = load_tile("door_leaf_h" if kind == "H" else "door_leaf_v", SCALE)
        out.alpha_composite(leaf, at(a - 0.5, b - 0.5))
    # 5. room labels, in the real UI font rather than a Latin placeholder
    d = ImageDraw.Draw(out)
    big, small = font(26), font(18)
    for name, (lx, ly) in LABELS.items():
        # centre of the cell: the wall band already owns its edges
        px, py = at(lx + 0.5, ly + 0.5)
        label, sub = name, f"{area(name)} m²"
        bb = d.textbbox((0, 0), label, font=big)
        d.text((px - (bb[2] - bb[0]) // 2, py - 30), label, font=big, fill=(25, 25, 34, 255))
        bb2 = d.textbbox((0, 0), sub, font=small)
        d.text((px - (bb2[2] - bb2[0]) // 2, py + 6), sub, font=small, fill=(90, 92, 110, 255))
    dest = os.path.join(TILES_DIR, "flatplan.png")
    out.convert("RGB").save(dest)
    total = sum(area(n) for n in LABELS)
    # plain ASCII on stdout: this box's console codec is GBK and chokes on m2's
    # superscript, which would otherwise look like a failed render
    print(f"flatplan.png {out.width}x{out.height}  {COLS}x{ROWS} cells = {total} m2"
          + (f"  UNRESOLVED={unresolved}" if unresolved else "  walls resolved"))


if __name__ == "__main__":
    problems = audit()
    for line in problems:
        print("LAYOUT:", line)
    render()
    if problems:
        raise SystemExit(f"{len(problems)} furniture placement problem(s)")
