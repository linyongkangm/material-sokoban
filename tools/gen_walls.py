"""Wall as a grid EDGE instead of a grid cell.

The old wall tile filled a whole 32x32 cell with three courses of brick and a
mortar frame on all four sides. Tiled up, every join stacked two mortar lines,
so a wall read as a lattice of dark grid lines -- the *edges* of the grid --
rather than as solid masonry. This set moves the wall onto the line between two
cells: a 14px band centred on y = 15.5 / x = 15.5, so one instance spans the
join and butt-joined instances stay one band wide.

Pieces are named by the arms they carry out of the centre block, and **every
orientation is its own asset** -- 16 per style:

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


gs = _load("gen_sokoban")
gm = _load("gen_murdoku")

N = gs.N
Grid = gs.Grid
BAND = range(9, 23)                 # 14 px centred on the grid line at 15.5
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

# shaded: one key light from the top-left, same convention as the rest of the set
S_INK = gs.OUTL                     # #1B1F2A
S_HI = gs.WALL_HI                   # sunlit crest
S_LIGHT = gs.WALL_LIGHT             # lit flank
S_MID = gs.WALL_MID                 # stone face
S_DK = gs.WALL_DK                   # underside
S_DEEP = "#39404F"                  # the away-side face, one step under DK

# flat: Murdoku rules -- one fill, one lighter band, heavy ink, no ramps
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


def shaded(arms):
    """(base, shade, ink) pixel lists for the dusk-stone style."""
    mask = mask_of(arms)
    body, detail, ink = [], [], []

    def out(x, y, d):
        return flank_out(mask, arms, x, y, d)

    for x, y in sorted(mask):
        up, dn = out(x, y, (0, -2)), out(x, y, (0, 2))
        lf, rt = out(x, y, (-2, 0)), out(x, y, (2, 0))
        if up:
            detail.append(px(x, y, S_HI))
        elif lf:
            detail.append(px(x, y, S_LIGHT))
        elif dn:
            detail.append(px(x, y, S_DK))
        elif rt:
            detail.append(px(x, y, S_DEEP))
        else:
            body.append(px(x, y, S_MID))
            # speckle so the long stone faces do not go flat, as in tile_wall
            if (x * 13 + y * 7) % 29 == 0:
                detail.append(px(x, y, S_LIGHT))
            elif (x * 5 + y * 11) % 37 == 0:
                detail.append(px(x, y, S_DK))
    for x, y in ink_of(arms, mask):
        ink.append(px(x, y, S_INK))
    return body, detail, ink


def flat(arms):
    """(fill, one crest band, ink) pixel lists for the flat pastel style."""
    mask = mask_of(arms)
    body, crest, ink = [], [], []
    for x, y in sorted(mask):
        if flank_out(mask, arms, x, y, (0, -2)):
            crest.append(px(x, y, F_HI))
        else:
            body.append(px(x, y, F_FILL))
    for x, y in ink_of(arms, mask):
        ink.append(px(x, y, F_INK))
    return body, crest, ink


def build(style, pieces=None):
    """MCP call plans for the requested pieces in one style."""
    shaded_style = style == "shaded"
    out_dir = "tiles" if shaded_style else "tiles/murdoku"
    calls = []
    for name, arms in PIECES.items():
        if pieces and name not in pieces:
            continue
        fname = f"{out_dir}/{name}.aseprite"
        if shaded_style:
            body, detail, ink = shaded(arms)
            layers = [("base", body + ink), ("shade", detail)]
        else:
            body, crest, ink = flat(arms)
            layers = [("flat", body), ("ink", crest + ink)]
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


def emit_lua(styles):
    """Write a batch-Lua generator so the pieces can be drawn in ONE MCP call.

    The MCP stdio client path needs ~72 calls (one Aseprite launch each) and
    stalls on this machine; the repo's other half drives Aseprite through dofile'd
    Lua, which is one call for the whole set. Pixel lists are baked in here so
    the geometry stays defined in exactly one place.
    """
    rows = []
    for s in styles:
        d = "tiles" if s == "shaded" else "tiles/murdoku"
        for name, arms in PIECES.items():
            if s == "shaded":
                body, detail, ink = shaded(arms)
            else:
                body, detail, ink = flat(arms)
            base = body + ink
            rows.append((d, name, s == "shaded", base, detail))

    def tbl(pixels):
        return ",\n    ".join('{%d,%d,"%s"}' % (p["x"], p["y"], p["color"]) for p in pixels)

    out = ["-- generated by tools/gen_walls.py -- do not edit by hand.",
           "-- Wall as a grid edge: 14px band centred on the cell line, 2px ink,",
           "-- ink omitted where an arm continues into the neighbouring cell.",
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
    for d, name, shaded_style, base, detail in rows:
        out.append('  { dir="%s", name="%s", two=%s, base={\n    %s },\n    shade={\n    %s } },'
                   % (d, name, "true" if shaded_style else "false",
                      tbl(base), tbl(detail) or "0"))
    out.append("}")
    out.append(r"""
local done = 0
for _, p in ipairs(PIECES) do
  local spr = Sprite(32, 32)
  spr.layers[1].name = p.two and 'base' or 'flat'
  local img = spr.cels[1].image
  for _, e in ipairs(p.base) do img:putPixel(e[1], e[2], col(e[3])) end
  if p.two and #p.shade > 1 then
    local lyr = spr:newLayer()
    lyr.name = 'shade'
    local im2 = Image(32, 32, spr.colorMode)
    for _, e in ipairs(p.shade) do im2:putPixel(e[1], e[2], col(e[3])) end
    spr:newCel(lyr, spr.frames[1], im2, Point(0, 0))
  end
  local stem = ROOT .. p.dir .. '/' .. p.name
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


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    styles = args[0].split(",") if len(args) > 0 else ["shaded", "murdoku"]
    pieces = args[1].split(",") if len(args) > 1 else None
    if "--lua" in sys.argv:
        p, n = emit_lua(styles)
        print(f"{os.path.basename(p)} written for {n} pieces")
        sys.exit(0)
    calls = []
    for s in styles:
        calls += build(s, pieces)
    with open(os.path.join(HERE, "calls_walls.json"), "w", encoding="utf-8") as fh:
        json.dump(calls, fh)
    print(f"calls_walls.json -> {len(calls)} calls for {','.join(styles)}"
          + (f" [{','.join(pieces)}]" if pieces else ""))
    for s in ("shaded", "murdoku"):
        for name, arms in PIECES.items():
            if pieces and name not in pieces:
                continue
            body, detail, ink = shaded(arms) if s == "shaded" else flat(arms)
            cols = {p["color"] for p in body + detail + ink}
            print(f"  {s:7s} {name:11s} arms={arms or '-':4s} px={len(body)+len(detail)+len(ink):4d}"
                  f" colors={len(cols)}")
