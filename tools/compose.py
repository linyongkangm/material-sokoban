"""Compose MCP-exported tiles into a contact sheet and a mock level.

Visual feedback is the step that decides whether the art is actually good:
contact.png shows every tile at 8x, scene.png tiles them into a real layout so
seam and palette cohesion problems show up.

The mock level is EDGE based, because that is what the wall now is: walls are
not cells, they sit on the line between two cells. So the scene places wall
pieces at grid *nodes*, offset half a cell from the cell grid, and resolves each
node from the four wall segments that meet there. That render is the proof that
the joints line up -- a doubled line at a join shows up immediately.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gw = _load("gen_walls")

# One tile set now, so no subject argument: compose.py just writes the three
# review images next to the tiles it read.
TILES_DIR = os.path.join(ROOT, "tiles")
SUFFIX = ""
N = 32
ORDER = ["floor", "box", "goal", "player"] + list(gw.PIECES)

# ---- the mock level ----------------------------------------------------
# Cells hold only what stands *in* a cell. Walls are declared per cell-edge:
# DECL holds ((col, row), 'N'|'E'|'S'|'W'). **One kind of wall**: an edge any
# side declares is a wall, drawn as one 10px band centred on the line. Both
# neighbours declaring the same line is the common case and it collapses to one
# segment anyway, because the canonical key below is the line, not the (cell,
# edge) pair -- which is exactly why the old double/single split was never sound.
CELLS = [
    "............",
    "..o......o..",
    "...$$.......",
    "............",
    "..@....$$...",
    "............",
    "...oo.......",
    "............",
    "............",
]
COLS, ROWS = len(CELLS[0]), len(CELLS)
COL = {"#": "wall", ".": "floor", "$": "box", "o": "goal", "@": "player"}

DECL = set()


def declare(c, r, *edges):
    for e in edges:
        DECL.add(((c, r), e))


for c in range(COLS):                      # the frame: one declaration is enough,
    declare(c, 0, "N")                     # the band then straddles the boundary
    declare(c, ROWS - 1, "S")
for r in range(ROWS):
    declare(0, r, "W")
    declare(COLS - 1, r, "E")
for r in (2, 3, 4):                        # vertical run A, declared from both sides
    declare(3, r, "E")
    declare(4, r, "W")
for c in (4, 5, 6):                        # run B turning off A -> corner
    declare(c, 5, "N")
    declare(c, 4, "S")
for r in (4, 5, 6):                        # run C crossing B -> cross + tee
    declare(4, r, "E")
    declare(5, r, "W")
for c in (3, 4):                           # stub D meeting C
    declare(c, 6, "N")
    declare(c, 5, "S")
declare(6, 5, "N")                         # an interior wall one cell declares
declare(7, 5, "N")
declare(2, 7, "E", "S")
declare(3, 7, "W")

# H[(x, y)] is the line above cell (x, y) running east from node (x, y);
# V[(x, y)] is the line left of it running south. Both neighbours of a line
# canonicalise onto the same key, so a set is enough to deduplicate.
KEY = {"N": lambda c, r: (c, r), "S": lambda c, r: (c, r + 1),
       "W": lambda c, r: (c, r), "E": lambda c, r: (c + 1, r)}
H = {KEY[e](c, r) for (c, r), e in DECL if e in "NS"}
V = {KEY[e](c, r) for (c, r), e in DECL if e in "EW"}


def arms_at(x, y, hs=None, vs=None):
    """Which of the four doubled wall segments meet at grid node (x, y).

    A horizontal segment runs east from the node it starts at, so it feeds the
    E arm here and the W arm at its far end; a vertical segment runs south.
    Getting this the other way round turns the outer frame into a row of
    one-armed stubs, which is exactly what the first render showed.
    """
    hs = H if hs is None else hs
    vs = V if vs is None else vs
    a = set()
    if (x, y) in hs:
        a.add("E")
    if (x - 1, y) in hs:
        a.add("W")
    if (x, y) in vs:
        a.add("S")
    if (x, y - 1) in vs:
        a.add("N")
    return a


def piece_for(arms):
    """The one asset carrying exactly these arms.

    There used to be a second argument here -- a PIL transpose to apply -- and
    seven base pieces to rotate. That was the bug: the key light is baked into
    every asset, so a turned corner lights the wrong edge and reads as a groove.
    All 16 orientations are delivered now, so the mock just looks one up.
    """
    return gw.BY_ARMS.get(frozenset(arms))


def load(name, scale):
    p = os.path.join(TILES_DIR, f"{name}_1x.png")
    if not os.path.exists(p):
        sys.exit(f"missing {p} - run the MCP draw calls first")
    im = Image.open(p).convert("RGBA")
    return im.resize((N * scale, N * scale), Image.NEAREST)


def _bg():
    # the pastel set is shown on the paper tone its own floors use, so a review
    # sheet does not invent a background the tiles never sit on in game
    return (242, 240, 247, 255)


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
        if is_surface(im):
            patch = Image.new("RGBA", (N * 2, N * 2))
            for ry in range(2):
                for rx in range(2):
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
    # the cell field sits one cell inside the canvas so a wall centred on the
    # outer boundary line is not cropped; a node at (x, y) therefore lands half
    # a cell off the cell grid, which is the whole point of an edge wall
    out = Image.new("RGBA", ((COLS + 2) * N * scale, (ROWS + 2) * N * scale), _bg())
    floor = load("floor", scale)
    # three passes, back to front: floor, the goal plate (it IS the floor, so it
    # belongs under the wall), the wall bands, then the pieces that stand in
    # front of them -- crate and detective. The band reaches 5px into each cell
    # and the crate leaves exactly that much margin, so the two no longer fight.
    for r, line in enumerate(CELLS):
        for c in range(len(line)):
            out.alpha_composite(floor, ((c + 1) * N * scale, (r + 1) * N * scale))
    for r, line in enumerate(CELLS):
        for c, ch in enumerate(line):
            if ch == "o":
                out.alpha_composite(load("goal", scale),
                                    ((c + 1) * N * scale, (r + 1) * N * scale))
    unresolved = []
    for y in range(ROWS + 1):
        for x in range(COLS + 1):
            arms = arms_at(x, y)
            if not arms:
                continue
            name = piece_for(arms)
            if name is None:
                unresolved.append((x, y, "".join(sorted(arms))))
                continue
            out.alpha_composite(load(name, scale),
                                ((x * N + N // 2) * scale, (y * N + N // 2) * scale))
    for r, line in enumerate(CELLS):
        for c, ch in enumerate(line):
            name = COL.get(ch, "floor")
            if name in ("box", "player"):
                out.alpha_composite(load(name, scale),
                                    ((c + 1) * N * scale, (r + 1) * N * scale))
    out.save(os.path.join(TILES_DIR, f"scene{SUFFIX}.png"))
    print(f"scene{SUFFIX}.png {out.width}x{out.height} walled-nodes="
          f"{sum(1 for y in range(ROWS + 1) for x in range(COLS + 1) if arms_at(x, y))}"
          f" declared-edges={len(H) + len(V)}")
    if unresolved:
        print(f"UNRESOLVED nodes (no piece carries these arms): {unresolved}")


def junctions():
    """A proof sheet: every wall orientation assembled from real pieces.

    Each patch puts one arm-set on a centre node and runs every arm one segment
    outward, so the neighbour node has exactly one arm and resolves to an end
    cap. That judges a corner against the pieces it actually meets in a level --
    which is what a contact sheet cannot show, and what the shipped mock stopped
    covering after the per-cell rewrite (it only ever placed straight bands).
    """
    scale = 4
    names = list(gw.PIECES)
    cols, span = 4, 3
    hs, vs = set(), set()
    for i, name in enumerate(names):
        cx, cy = (i % cols) * span + 1, (i // cols) * span + 1
        for a in gw.PIECES[name]:
            if a == "E":
                hs.add((cx, cy))
            elif a == "W":
                hs.add((cx - 1, cy))
            elif a == "S":
                vs.add((cx, cy))
            else:
                vs.add((cx, cy - 1))
    gx = cols * span + 1
    gy = ((len(names) + cols - 1) // cols) * span + 1
    out = Image.new("RGBA", ((gx + 2) * N * scale, (gy + 2) * N * scale), _bg())
    bad = []
    placed = 0
    for y in range(gy + 1):
        for x in range(gx + 1):
            arms = arms_at(x, y, hs, vs)
            if not arms:
                continue
            placed += 1
            got = piece_for(arms)
            if got is None:
                bad.append((x, y, "".join(sorted(arms))))
                continue
            out.alpha_composite(load(got, scale),
                                ((x * N + N // 2) * scale, (y * N + N // 2) * scale))
    out.save(os.path.join(TILES_DIR, f"junctions{SUFFIX}.png"))
    print(f"junctions{SUFFIX}.png {out.width}x{out.height} nodes={placed}"
          + (f" UNRESOLVED={bad}" if bad else " all orientations resolved"))


if __name__ == "__main__":
    contact()
    scene()
    junctions()
