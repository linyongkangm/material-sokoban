"""Wall as a grid EDGE instead of a grid cell.

The old wall tile filled a whole 32x32 cell with three courses of brick and a
mortar frame on all four sides. Tiled up, every join stacked two mortar lines,
so a wall read as a lattice of dark grid lines -- the *edges* of the grid --
rather than as solid masonry. This set moves the wall onto the line between two
cells: a 10px band centred on y = 15.5 / x = 15.5, so one instance spans the
join and butt-joined instances stay one band wide. It reaches 5px into each
neighbouring cell, which is exactly the margin the cell pieces leave empty.

Pieces are named by the arms they carry out of the centre block, and **every
orientation is its own asset** -- 16 of them:

    wall_post (no arm)   wall_h EW   wall_v NS   wall_cross NSEW
    wall_end_{n,e,s,w}          one arm
    wall_corner_{nw,ne,se,sw}   two adjacent arms
    wall_tee_{n,e,s,w}          three arms, named for the arm that is MISSING

Rotating a piece is deliberately not allowed, and that is why the set is this
big: the key light sits at the top-left in every asset in this repo, so turning
a corner through 90 degrees turns the light with it -- the highlight lands on the
right or bottom edge and that piece reads as a groove instead of a ridge. The
first delivery shipped seven pieces plus a "just rotate it" instruction, and the
mock level showed the mixed convex/concave result immediately.

No ink is drawn where an arm leaves the cell, which is what keeps a join at a
single 2px line instead of 4px. The ink that runs *alongside* the band is left
in place, so the top and bottom outlines continue across joins.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gm = _load("gen_murdoku")

N = gm.N
Grid = gm.Grid
# 6 px of stone face, and the 2px ink ring on each side brings the drawn band to
# 10 px total -- which is the number that matters, because 10 px straddling the
# line reaches 5 px into each neighbouring cell and the cell pieces leave
# exactly 5 px of margin (the crate is drawn 22 px inside a 32 px cell). A 14 px
# band ate 7 px of the crate beside it, and drawing the wall *under* the crate
# only swapped that for a wall with a 52 px hole in it: two things that each
# fill their region cannot share one boundary line.
BAND = range(13, 19)
PIECES = {                          # arms carried out of the centre block
    "wall_post": "",                # an isolated node / cap
    "wall_h": "EW",
    "wall_v": "NS",
    "wall_cross": "NSEW",
    "wall_end_n": "N",              # a wall that stops at this node
    "wall_end_e": "E",
    "wall_end_s": "S",
    "wall_end_w": "W",
    "wall_corner_nw": "NW",
    "wall_corner_ne": "NE",
    "wall_corner_se": "SE",
    "wall_corner_sw": "SW",
    "wall_tee_n": "SEW",            # tees are named for the arm that is missing
    "wall_tee_e": "NWS",
    "wall_tee_s": "NEW",
    "wall_tee_w": "NES",
}
# what a map resolves to: the set of arms meeting at a node -> the one asset
# that carries exactly them. No rotation, no mirroring, see the module docstring.
BY_ARMS = {frozenset(arms): name for name, arms in PIECES.items()}

# ---- one kind of wall -----------------------------------------------------
# There used to be a second set: 15 `halfwall_*` pieces, a 5px band drawn flush
# inside the declaring cell, for the case where only one of the two cells sharing
# a line reported a wall. That distinction is gone (user's call: "不分单面墙和双面
# 墙，现在墙都是压在边的中间") -- a wall is an edge, an edge is shared by two cells,
# so "half an edge" was never a thing the level could mean. One declared edge now
# draws the same 10px band straddling the line, and each side of it loses the same
# 5px the cell pieces already leave empty.
ALL_PIECES = dict(PIECES)

# The band's three tones: Murdoku rules -- one fill, one lighter band, heavy ink,
# no ramps. The lighter row/column is the key-light side (north for a horizontal
# run, west for a vertical one), which is why every orientation is its own asset.
F_INK = gm.INK
F_FILL = gm.PERI
F_HI = "#BFC6E2"


def mask_of(arms):
    """Pixels the band occupies, for a piece carrying `arms` out of the centre."""
    m = set()
    for y in BAND:
        for x in BAND:
            m.add((x, y))
    for a in arms:
        if a == "N":
            m |= {(x, y) for x in BAND for y in range(0, BAND[-1] + 1)}
        elif a == "S":
            m |= {(x, y) for x in BAND for y in range(BAND[0], N)}
        elif a == "W":
            m |= {(x, y) for y in BAND for x in range(0, BAND[-1] + 1)}
        elif a == "E":
            m |= {(x, y) for y in BAND for x in range(BAND[0], N)}
    return m


def ink_of(arms, mask):
    """2px ring outside the silhouette, except where an arm leaves the cell."""
    ink = []
    for y in range(N):
        for x in range(N):
            if (x, y) in mask:
                continue
            if any(max(abs(x - mx), abs(y - my)) <= 2 for mx, my in mask):
                ink.append((x, y))
    # open the joint: strip the ink that would sit across a continuing arm
    cut = []
    for x, y in ink:
        if ("W" in arms and x <= 1 and y in BAND) or ("E" in arms and x >= N - 2 and y in BAND):
            continue
        if ("N" in arms and y <= 1 and x in BAND) or ("S" in arms and y >= N - 2 and x in BAND):
            continue
        cut.append((x, y))
    return cut


def px(x, y, col):
    return {"x": x, "y": y, "color": col}


# ---------------------------------------------------------------- openings
# Doors and windows are wall-mounted, not furniture: a window replaces the stone
# of a band and a leaf lies along the wall inside a gap, so both are placed on the
# grid line exactly like the wall tile under them. They live here, in the wall
# generator, beside the pieces they sit on -- they used to be defined under
# furniture/, which is how they ended up existing in one style only.
OPENINGS = ("window_h", "window_v", "door_leaf_h", "door_leaf_v")


def opening(name):
    """(base, detail) pixel lists for a wall-mounted opening.

    Three lessons are baked into these four shapes. A doorway is an **absent**
    wall segment capped by `wall_end_*`, so the leaf only has to be the panel
    lying against the wall -- the first version swept a radius-28 quarter circle
    for the swing, which leaves a 32px cell almost immediately and came out as a
    hook and a dot. The vertical pieces are authored, not rotated: rotating the
    leaf carried its hinge to the wrong end and it rendered as a bracket jutting
    outside the flat's outer wall. And the window is the one asset here with no
    directional highlight -- glass is a recessed hole, not a ridge, so a pane lit
    along its top edge read as a piece of wall with a crest instead of a hole in
    the wall. Its frame is also exactly the band's cross-section (rows 11..20),
    because a frame one pixel narrower notched the wall's outline at every window.
    """
    g = Grid()
    if name == "window_h":
        g.rect(0, 11, 31, 12, gm.INK).rect(0, 19, 31, 20, gm.INK)
        g.rect(0, 13, 31, 18, gm.WHITE)
    elif name == "window_v":
        g.rect(11, 0, 12, 31, gm.INK).rect(19, 0, 20, 31, gm.INK)
        g.rect(13, 0, 18, 31, gm.WHITE)
    elif name == "door_leaf_h":
        g.rect(2, 11, 28, 16, gm.INK)
        g.rect(3, 12, 27, 15, gm.OCHRE)
        g.rect(3, 12, 27, 12, gm.OCHRE_HI)
    elif name == "door_leaf_v":
        g.rect(11, 2, 16, 28, gm.INK)
        g.rect(12, 3, 15, 27, gm.OCHRE)
        g.rect(12, 3, 12, 27, gm.OCHRE_HI)
    body, detail = [], []
    for p in g.pixels():
        # the leaf's lit edge is the only thing that belongs on the shade layer
        (detail if p["color"] == gm.OCHRE_HI else body).append(p)
    return body, detail


def flank_out(mask, arms, x, y, d):
    """Is the mask absent 2px that way -- i.e. is this a lit or shaded flank?

    A flank only exists where the band actually stops. Where an arm leaves the
    cell the neighbour continues it, so that side must stay plain face: leaving
    it in put a light/dark pair on every join (shaded set) and a repeated crest
    dash every 32px down a vertical run (flat set) -- both re-create the
    grid-line read this redesign exists to remove.
    """
    if (x + d[0], y + d[1]) in mask:
        return False
    if d == (-2, 0) and "W" in arms and x <= 1:
        return False
    if d == (2, 0) and "E" in arms and x >= N - 2:
        return False
    if d == (0, -2) and "N" in arms and y <= 1:
        return False
    if d == (0, 2) and "S" in arms and y >= N - 2:
        return False
    return True


def flat(arms):
    """(fill, one crest band, ink) pixel lists for the band.

    The crest is the band's **lit long side**: rows 13,14 of a run that goes east
    or west, columns 13,14 of a run that goes north or south. It used to be found
    by asking "is the pixel two rows above outside the mask", which is never true
    down a vertical run -- the run continues there -- so every vertical wall
    shipped without the one lighter band the horizontals have. A turn then read as
    a lit ridge running straight into a flat rail and dead-ending, which is the
    same convex/concave split this set exists to avoid.

    The centre block belongs to whichever arms actually pass through it: taking
    both tests unconditionally put a 2x2 spur at rows 13,14 in the middle of every
    straight vertical run, i.e. the grid-line read back again.
    """
    mask = mask_of(arms)
    horiz = any(a in "EW" for a in arms)
    vert = any(a in "NS" for a in arms)
    lit_side = (BAND[0], BAND[0] + 1)
    body, crest, ink = [], [], []
    for x, y in sorted(mask):
        in_x, in_y = x in BAND, y in BAND
        if in_x and in_y:                       # the node where the arms meet
            take_y = horiz or not vert          # a post with no arms takes both
            take_x = vert or not horiz
            lit = (take_y and y in lit_side) or (take_x and x in lit_side)
        elif in_x:                              # an N/S arm
            lit = x in lit_side
        else:                                   # an E/W arm
            lit = y in lit_side
        (crest if lit else body).append(px(x, y, F_HI if lit else F_FILL))
    for x, y in ink_of(arms, mask):
        ink.append(px(x, y, F_INK))
    return body, crest, ink


def piece(name):
    """(body, detail, ink) for any wall asset: a band piece or an opening.

    An opening draws its own outline, so its ink list is empty.
    """
    if name in OPENINGS:
        body, detail = opening(name)
        return body, detail, []
    return flat(ALL_PIECES[name])


# everything the generator can draw, in the order the batch Lua emits it
ALL_ASSETS = list(ALL_PIECES) + list(OPENINGS)


def build(pieces=None):
    """MCP call plans for the requested assets -- the stdio fallback path."""
    out_dir = "tiles"
    calls = []
    for name in ALL_ASSETS:
        if pieces and name not in pieces:
            continue
        fname = f"{out_dir}/{name}.aseprite"
        body, detail, ink = piece(name)
        layers = [("flat", body), ("ink", detail + ink)]
        calls.append(["create_canvas", {"width": N, "height": N, "filename": fname}])
        for layer, _ in layers:
            calls.append(["add_layer", {"filename": fname, "layer_name": layer}])
        for layer, pixels in layers:
            calls.append(["draw_pixels_at", {"filename": fname, "layer_name": layer,
                                             "frame_index": 1, "pixels": pixels}])
        calls.append(["export_frame", {"filename": fname, "frame_index": 1,
                                       "output_filename": f"{out_dir}/{name}_1x.png",
                                       "scale": 1}])
    return calls


def emit_lua():
    """Write a batch-Lua generator so the pieces can be drawn in ONE MCP call.

    The MCP stdio client path needs ~70 calls (one Aseprite launch each) and
    stalls on this machine; the repo's other half drives Aseprite through dofile'd
    Lua, which is one call for the whole set. Pixel lists are baked in here so
    the geometry stays defined in exactly one place.
    """
    rows = []
    for name in ALL_ASSETS:
        body, detail, ink = piece(name)
        rows.append(("tiles", name, "flat", "ink", body, detail + ink))

    def tbl(pixels):
        return ",\n    ".join('{%d,%d,"%s"}' % (p["x"], p["y"], p["color"]) for p in pixels)

    out = ["-- generated by tools/gen_walls.py -- do not edit by hand.",
           "-- Double-sided wall: 10px band (6px face + 2px ink each side) centred on",
           "-- the cell line, ink omitted where an arm continues into the neighbour.",
           "-- One kind of wall: a declared edge is a wall, drawn as one 10px band",
           "-- straddling the line, whether or not the cell across declares it too.",
           "-- Openings (window/door_leaf, h and v): wall-mounted overlays, drawn after",
           "-- the band they sit on and centred on the same grid line.",
           "local ROOT = 'E:/Material/material-sokoban/'",
           "local function col(h)",
           "  return Color(tonumber(string.sub(h, 2, 3), 16),",
           "               tonumber(string.sub(h, 4, 5), 16),",
           "               tonumber(string.sub(h, 6, 7), 16), 255)",
           "end",
           "-- saveCopyAs does not abort on a failed write, so delete first and prove it.",
           "local function save_png(spr, path)",
           "  pcall(os.remove, path)",
           "  spr:saveCopyAs(path)",
           "  local fh = io.open(path, 'rb')",
           "  if not fh then error('failed to write ' .. path) end",
           "  fh:close()",
           "end",
           "local PIECES = {"]
    for d, name, lo, up, base, detail in rows:
        out.append('  { dir="%s", name="%s", lo="%s", up="%s", base={\n    %s },\n    shade={\n    %s } },'
                   % (d, name, lo, up, tbl(base), tbl(detail) or "0"))
    out.append("}")
    out.append(r"""
local done = 0
for _, p in ipairs(PIECES) do
  local spr = Sprite(32, 32)
  spr.layers[1].name = p.lo
  local img = spr.cels[1].image
  for _, e in ipairs(p.base) do img:putPixel(e[1], e[2], col(e[3])) end
  if #p.shade > 1 then
    local lyr = spr:newLayer()
    lyr.name = p.up
    local im2 = Image(32, 32, spr.colorMode)
    for _, e in ipairs(p.shade) do im2:putPixel(e[1], e[2], col(e[3])) end
    spr:newCel(lyr, spr.frames[1], im2, Point(0, 0))
  end
  local stem = ROOT .. p.dir .. '/' .. p.name
  pcall(os.remove, stem .. '.aseprite')
  spr:saveAs(stem .. '.aseprite')
  save_png(spr, stem .. '_1x.png')
  spr:close()
  done = done + 1
end
print('WALLS_OK pieces=' .. done)""")
    path = os.path.join(HERE, "walls_gen.lua")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return path, len(rows)


# ---------------------------------------------------------------- export
COLS = 4                    # 16 slots, one per arm subset: a 4x4 grid of tiles


def mask_order():
    """index -> piece name, laid out so the index IS the arm bitmask.

    N=1, E=2, S=4, W=8, so slots 0..15 are every subset of the four arms and 0 is
    `wall_post`, the node with no arm leaving it. An engine that resolved a node to
    a set of arms therefore needs arithmetic, not a lookup table, and the JSON
    manifest beside the atlas is only there to prove the picture matches the
    roster. It used to be 32 slots -- 16 bands plus 15 single-sided rails -- and
    slot 16 was the empty set of the rails, which is a thing that no longer exists.
    """
    order = {}
    for mask in range(16):
        arms = frozenset("NESW"[i] for i in range(4) if (mask >> i) & 1)
        order[mask] = BY_ARMS[arms]
    return order


def sheet():
    """Write the wall atlas, a 4x review copy and a JSON manifest."""
    from PIL import Image
    order = mask_order()
    rows = (len(order) + COLS - 1) // COLS
    d, stem = "tiles", "wallset"
    base = Image.new("RGBA", (COLS * N, rows * N), (0, 0, 0, 0))
    bad, filled = [], 0
    for idx, name in sorted(order.items()):
        src = Image.open(os.path.join(ROOT, d, f"{name}_1x.png")).convert("RGBA")
        x, y = (idx % COLS) * N, (idx // COLS) * N
        base.alpha_composite(src, (x, y))
        # a paste one pixel off is exactly the defect this repo keeps catching,
        # so compare the slot against the source byte for byte
        if base.crop((x, y, x + N, y + N)).tobytes() != src.tobytes():
            bad.append(name)
        filled += 1
    for scale in (1, 4):
        im = base if scale == 1 else base.resize((base.width * 4, base.height * 4),
                                                 Image.NEAREST)
        tag = "" if scale == 1 else "_4x"
        im.save(os.path.join(ROOT, d, f"{stem}{tag}.png"))
    manifest = {
        "tile": N, "cols": COLS, "rows": rows,
        "bits": {"N": 1, "E": 2, "S": 4, "W": 8},
        "index_of": "mask",
        # the facts that each cost a failed render in this repo
        "placement": "centred on the grid line, half a cell off the cell grid",
        "one_per_edge": "a walled edge is drawn once; twice stacks the band to 20px",
        "rotate": "never -- the key light is baked into every tile",
        "index": {str(i): {"name": n, "arms": sorted(ALL_PIECES[n])}
                  for i, n in sorted(order.items())},
    }
    with open(os.path.join(ROOT, d, f"{stem}.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(f"{d}/{stem}.png {base.width}x{base.height}  tiles={filled}/{COLS * rows}"
          + (f"  MISMATCH {bad}" if bad else "  slots verified"))
    if bad:
        raise SystemExit(f"{len(bad)} atlas slot(s) do not match their source tile")


BAND_EDGE = (BAND[0] - 2, BAND[-1] + 2)      # the band's outer ink rows/columns


def openings_sheet():
    """Export the wall-mounted overlays: a row atlas, a 4x copy and a manifest.

    The gate here is the one a loose-tile contact sheet cannot show: an opening is
    only correct if it shares the cross-section of the band it replaces. A window
    must span the full 32px and keep its ink on the band's own rows, or every run
    it is laid over gets a seam and a step in it; a leaf must stay inside the band
    plus its 2px outline, or it is a plank leaning on a wall.
    """
    from PIL import Image
    d, stem = "tiles", "openings"
    base = Image.new("RGBA", (N * len(OPENINGS), N), (0, 0, 0, 0))
    bad, checked = [], []
    for i, name in enumerate(OPENINGS):
        src = Image.open(os.path.join(ROOT, d, f"{name}_1x.png")).convert("RGBA")
        base.alpha_composite(src, (i * N, 0))
        if src.tobytes() != base.crop((i * N, 0, (i + 1) * N, N)).tobytes():
            bad.append(name)
        rows, cols = [], []
        for y in range(N):
            for x in range(N):
                if src.getpixel((x, y))[3]:
                    rows.append(y)
                    cols.append(x)
        lo, hi = BAND_EDGE
        # the cross-section is the axis the band is thin along: rows for an h
        # piece, columns for a v one. Reading the other axis is what made a
        # correct window_v look like it failed.
        horiz = name.endswith("_h")
        cross = rows if horiz else cols
        along = cols if horiz else rows
        inside = min(cross) >= lo and max(cross) <= hi
        if name.startswith("window"):
            # not merely "inside" the band: a window replaces the stone, so its
            # outline has to land on the band's own rows. The first version was
            # one pixel narrower on each side, which left a notch in the wall's
            # outline for the full width of every window.
            exact = (min(cross), max(cross)) == (lo, hi)
            full = min(along) == 0 and max(along) == N - 1
            checked.append("%s:band=%d..%d exact=%s full_span=%s"
                           % (name, min(cross), max(cross), exact, full))
            if not (exact and full):
                bad.append("%s does not match the band it replaces" % name)
        else:
            checked.append("%s:band=%d..%d" % (name, min(cross), max(cross)))
            if not inside:
                bad.append("%s reaches outside the wall band" % name)
    for scale in (1, 4):
        im = base if scale == 1 else base.resize((base.width * 4, base.height * 4),
                                                 Image.NEAREST)
        tag = "" if scale == 1 else "_4x"
        im.save(os.path.join(ROOT, d, f"{stem}{tag}.png"))
    manifest = {
        "tile": N, "cols": len(OPENINGS), "rows": 1,
        "index": {str(i): name for i, name in enumerate(OPENINGS)},
        "kind": {name: ("glass over the band" if name.startswith("window")
                        else "leaf inside a doorway gap") for name in OPENINGS},
        # the contract an engine has to honour, same as the wall set's
        "placement": "centred on the grid line, half a cell off the cell grid",
        "draw_order": ["wall band", "window", "door leaf"],
        "rotate": "never -- h and v are separate tiles, the key light is baked",
        "gap": "a doorway is an ABSENT wall segment, capped by wall_end_*",
    }
    with open(os.path.join(ROOT, d, f"{stem}.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(f"{d}/{stem}.png {base.width}x{base.height}  " + "  ".join(checked)
          + ("  MISMATCH " + str(bad) if bad else "  band-compatible"))
    if bad:
        raise SystemExit(f"{len(bad)} opening(s) do not sit on the wall band")


if __name__ == "__main__":
    pieces = [a for a in sys.argv[1:] if not a.startswith("--")]
    pieces = pieces[0].split(",") if pieces else None
    if "--openings" in sys.argv:
        openings_sheet()
        sys.exit(0)
    if "--sheet" in sys.argv:
        sheet()
        sys.exit(0)
    if "--lua" in sys.argv:
        p, n = emit_lua()
        print(f"{os.path.basename(p)} written for {n} pieces")
        sys.exit(0)
    calls = build(pieces)
    with open(os.path.join(HERE, "calls_walls.json"), "w", encoding="utf-8") as fh:
        json.dump(calls, fh)
    print(f"calls_walls.json -> {len(calls)} calls"
          + (f" [{','.join(pieces)}]" if pieces else ""))
    for name, arms in ALL_PIECES.items():
        if pieces and name not in pieces:
            continue
        body, detail, ink = piece(name)
        cols = {p["color"] for p in body + detail + ink}
        print(f"  {name:14s} arms={arms or '-':4s} px={len(body)+len(detail)+len(ink):4d}"
              f" colors={len(cols)}")
