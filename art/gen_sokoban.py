"""Generate a 32x32 Sokoban tile set as MCP tool-call plans.

Art direction (dusk warehouse, top-left key light, <=8 colors per tile):
  floor  cool stone plate, raised bevel -> tiles seamlessly into a grid
  wall   warm stone brick, running-bond mortar, sunlit top face
  box    wooden crate, border planks + X bands, nails
  goal   recessed plate (inverted bevel) + red ring marker
  player cap + overalls, teal clothes to pop against warm crates

The lit-side convention is consistent everywhere: y=0 / x=0 rows are the
light edges, so the set reads as one scene.

Emits calls.json for mcp_client.py: [[tool, args], ...]
"""
import json
import math
import os
import sys

N = 32
ART = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- palette
FLOOR_BASE, FLOOR_HI, FLOOR_DK, FLOOR_EDGE = "#4A5262", "#636D80", "#3A414F", "#2A303B"
WALL_OUT, WALL_DK, WALL_MID = "#232A36", "#4C5666", "#78839A"
WALL_LIGHT, WALL_HI, WALL_MORTAR = "#9AA6BC", "#C3CCDC", "#2F3644"
CR_OUT, CR_DK, CR_MID, CR_LIGHT, CR_HI = "#2E1D10", "#7A4A22", "#A9682F", "#C9813D", "#E8AC6B"
GOAL_BASE, GOAL_HI = "#3A414F", "#4A5262"
RING, RING_DK, RING_HI = "#E0685A", "#A64436", "#F79B86"
SKIN, SKIN_D = "#E8B48C", "#C58A62"
CAP, CAP_L, CAP_D = "#2E6B7E", "#4399B2", "#1E4A58"
SH, SH_L, SH_D = "#3E7C8C", "#5FA3B4", "#2A5A68"
PANTS, PANTS_D = "#46536A", "#2E3846"
BOOT, OUTL = "#2A2F3A", "#1B1F2A"


class Grid:
    """32x32 paint buffer; None stays transparent."""

    def __init__(self):
        self.c = [[None] * N for _ in range(N)]

    def set(self, x, y, col):
        if 0 <= x < N and 0 <= y < N:
            self.c[y][x] = col
        return self

    def at(self, x, y):
        return self.c[y][x] if (0 <= x < N and 0 <= y < N) else None

    def rect(self, x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, col)
        return self

    def border(self, x0, y0, x1, y1, col):
        for x in range(x0, x1 + 1):
            self.set(x, y0, col).set(x, y1, col)
        for y in range(y0, y1 + 1):
            self.set(x0, y, col).set(x1, y, col)
        return self

    def round_rect(self, x0, y0, x1, y1, r, col):
        self.rect(x0, y0, x1, y1, col)
        for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            for dy in range(r):
                for dx in range(r):
                    self.set(cx + (dx if cx == x0 else -dx),
                             cy + (dy if cy == y0 else -dy), None)
        return self

    def ring_px(self, cx, cy, rad, tol, col):
        for y in range(N):
            for x in range(N):
                if abs(math.hypot(x + 0.5 - cx, y + 0.5 - cy) - rad) <= tol:
                    self.set(x, y, col)
        return self

    def pixels(self):
        return [{"x": x, "y": y, "color": self.c[y][x]}
                for y in range(N) for x in range(N) if self.c[y][x]]

    def outline(self, col):
        """1px ring of pixels just outside the silhouette (8-neighbours).

        Computed from the whole sprite rather than a single cel, so parts that
        live only on the shade layer (brim, arms) still get an even border.
        """
        ring = []
        for y in range(N):
            for x in range(N):
                if self.c[y][x] is not None:
                    continue
                if any(self.at(x + dx, y + dy) is not None
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                       if (dx, dy) != (0, 0)):
                    ring.append({"x": x, "y": y, "color": col})
        return ring


def split(g, keep_light=True):
    """Return (base, shade) grids: base = bulk fill, shade = lit + dark detail."""
    base, shade = Grid(), Grid()
    for y in range(N):
        for x in range(N):
            col = g.at(x, y)
            if col is None:
                continue
            (shade if col in (FLOOR_HI, FLOOR_DK, FLOOR_EDGE, WALL_HI, WALL_LIGHT,
                              WALL_DK, WALL_OUT, WALL_MORTAR, CR_HI, CR_LIGHT, CR_DK,
                              CR_OUT, RING_HI, RING_DK, CAP_L, CAP_D, SH_L, SH_D,
                              SKIN_D, PANTS_D, OUTL, BOOT) else base).set(x, y, col)
    return base, shade


# ------------------------------------------------------------------ floor
def tile_floor():
    g = Grid()
    g.rect(0, 0, N - 1, N - 1, FLOOR_BASE)
    # raised plate: light along top/left, hard dark along bottom/right
    for i in range(N):
        g.set(i, 0, FLOOR_HI).set(0, i, FLOOR_HI)
        g.set(i, N - 1, FLOOR_EDGE).set(N - 1, i, FLOOR_EDGE)
    for i in range(1, N - 1):
        g.set(i, 1, FLOOR_HI).set(1, i, FLOOR_HI)
        g.set(i, N - 2, FLOOR_DK).set(N - 2, i, FLOOR_DK)
    # sparse grit so the plate is not clinically clean
    for y in range(N):
        for x in range(N):
            if 3 <= x <= N - 4 and 3 <= y <= N - 4:
                if (x * 7 + y * 13) % 43 == 0:
                    g.set(x, y, FLOOR_DK)
                elif (x * 11 + y * 5) % 61 == 0:
                    g.set(x, y, FLOOR_HI)
    # three pits for character
    for px, py in ((9, 20), (22, 8), (17, 25)):
        g.set(px, py, FLOOR_DK).set(px + 1, py, FLOOR_DK).set(px, py + 1, FLOOR_EDGE)
    return g


# ------------------------------------------------------------------- wall
# Three courses of staggered stone bricks over a mortar bed. Each brick is
# individually bevelled (light top/left, dark bottom/right) so the wall reads
# as raised masonry rather than a flat panel.
COURSES = (
    (0, 9, (15,)),
    (11, 20, (7, 23)),
    (22, 31, (15,)),
)


def tile_wall():
    g = Grid()
    g.rect(0, 0, N - 1, N - 1, WALL_MORTAR)
    for y0, y1, joints in COURSES:
        spans = []
        lo = 0
        for j in joints:
            spans.append((lo, j - 1))
            lo = j + 1
        spans.append((lo, N - 1))
        for bx0, bx1 in spans:
            if bx1 < bx0:
                continue
            g.rect(bx0, y0, bx1, y1, WALL_MID)
            g.rect(bx0, y0, bx1, y0, WALL_HI)          # sunlit top edge
            for y in range(y0, y1 + 1):                # lit left edge
                g.set(bx0, y, WALL_LIGHT)
            g.rect(bx0, y1, bx1, y1, WALL_DK)          # shadowed bottom edge
            for y in range(y0, y1 + 1):                # dark right edge
                g.set(bx1, y, WALL_OUT)
    # speckle keeps the large stone faces from going flat
    for y in range(N):
        for x in range(N):
            col = g.at(x, y)
            if col == WALL_MID and (x * 13 + y * 7) % 29 == 0:
                g.set(x, y, WALL_LIGHT)
            elif col == WALL_MID and (x * 5 + y * 11) % 37 == 0:
                g.set(x, y, WALL_DK)
    return g


# -------------------------------------------------------------------- box
def tile_box():
    g = Grid()
    x0, y0, x1, y1 = 2, 2, 29, 29
    g.round_rect(x0, y0, x1, y1, 2, CR_MID)
    w, h = x1 - x0, y1 - y0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g.at(x, y) is None:
                continue
            edge = min(x - x0, y - y0, x1 - x, y1 - y)
            dx, dy = x - x0, y - y0
            on_band = abs(dx - dy) <= 1 or abs(dx + dy - w) <= 1
            near_band = abs(dx - dy) <= 2 or abs(dx + dy - w) <= 2
            if edge <= 3:                       # frame planks
                g.set(x, y, CR_HI if edge == 3 and y <= y0 + 3 else
                      (CR_LIGHT if edge >= 2 else CR_MID))
                if y >= y1 - 3:
                    g.set(x, y, CR_DK)
            elif on_band:                       # crossed braces
                g.set(x, y, CR_LIGHT if y - x <= 0 else CR_MID)
                if y - x <= 0 and y < y1 - 4:
                    g.set(x, y, CR_HI)
            elif near_band:
                g.set(x, y, CR_DK)              # shadow cast by the braces
            else:                               # recessed panel with grain
                g.set(x, y, CR_DK if (x - x0) % 5 == 0 and (y % 2) else CR_MID)
    # nails in the four frame corners
    for nx, ny in ((5, 5), (26, 5), (5, 26), (26, 26)):
        g.set(nx, ny, CR_HI)
    return g


# ------------------------------------------------------------------- goal
def tile_goal():
    g = Grid()
    g.rect(0, 0, N - 1, N - 1, GOAL_BASE)
    # inverted bevel -> reads as a depression in the floor
    for i in range(N):
        g.set(i, 0, FLOOR_EDGE).set(0, i, FLOOR_EDGE)
        g.set(i, N - 1, GOAL_HI).set(N - 1, i, GOAL_HI)
    g.rect(1, 1, N - 2, N - 2, GOAL_BASE)
    g.border(3, 3, N - 4, N - 4, FLOOR_EDGE)
    g.border(4, 4, N - 5, N - 5, "#333A47")
    # ring marker, lit from the top-left
    cx, cy = 15.5, 15.5
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 6.8 <= d <= 9.6:
                if x < 15 and y < 15:
                    g.set(x, y, RING_HI)
                elif x > 16 and y > 16:
                    g.set(x, y, RING_DK)
                else:
                    g.set(x, y, RING)
    g.rect(15, 15, 16, 16, RING)
    # inward corner ticks
    for sx, sy in ((6, 6), (25, 6), (6, 25), (25, 25)):
        for k in range(4):
            g.set(sx + (k if sx < 16 else -k), sy + (k if sy < 16 else -k), RING_DK)
    return g


# ----------------------------------------------------------------- player
def tile_player():
    g = Grid()
    BROW = "#3B2A20"
    # cap: crown with a lit top-left, brim sitting in its own shadow
    g.round_rect(9, 3, 22, 6, 2, CAP)
    g.rect(11, 3, 20, 3, CAP_L)
    g.rect(9, 4, 10, 6, CAP_L)
    g.rect(9, 6, 22, 6, CAP_L)
    g.rect(8, 7, 23, 8, CAP_D)
    g.rect(21, 7, 23, 8, "#163947")
    # head
    g.rect(10, 9, 21, 16, SKIN)
    g.rect(10, 9, 21, 9, SKIN_D)                # brim shadow across the brow
    g.rect(20, 10, 21, 16, SKIN_D)              # form shadow on the away side
    g.set(9, 12, SKIN).set(9, 13, SKIN)         # ears
    g.set(22, 12, SKIN_D).set(22, 13, SKIN_D)
    g.rect(12, 11, 13, 11, BROW).rect(18, 11, 19, 11, BROW)
    g.rect(12, 12, 13, 13, OUTL).rect(18, 12, 19, 13, OUTL)
    g.rect(15, 14, 16, 14, SKIN_D)              # nose
    g.rect(14, 15, 17, 15, BROW)                # mouth
    g.rect(12, 17, 19, 17, SKIN_D)              # neck
    # torso
    g.rect(7, 18, 24, 19, SH)                   # shoulders
    g.rect(8, 18, 23, 26, SH)
    g.rect(8, 18, 23, 18, SH_L)
    g.rect(22, 19, 23, 26, SH_D)                # away-side shadow
    g.rect(12, 19, 13, 22, SH_L)                # overall straps
    g.rect(18, 19, 19, 22, SH_L)
    g.rect(12, 23, 19, 26, SH_L)                # bib
    g.rect(15, 24, 16, 25, SH_D)                # pocket
    g.rect(8, 26, 23, 26, PANTS_D)              # belt
    # arms and hands
    g.rect(5, 19, 7, 25, SH_D)
    g.rect(5, 19, 5, 25, SH)
    g.rect(24, 19, 26, 25, SH_D)
    g.rect(5, 26, 7, 27, SKIN)
    g.rect(24, 26, 26, 27, SKIN_D)
    # legs
    g.rect(10, 27, 14, 29, PANTS)
    g.rect(17, 27, 21, 29, PANTS)
    g.rect(10, 27, 11, 29, "#556480")
    g.rect(20, 27, 21, 29, PANTS_D)
    # boots
    g.rect(9, 30, 14, 31, BOOT)
    g.rect(17, 30, 22, 31, BOOT)
    g.rect(9, 30, 14, 30, "#3A4150")
    g.rect(17, 30, 22, 30, "#333A46")
    g.rect(9, 31, 22, 31, "#171B22")
    return g


TILES = {
    "floor": tile_floor,
    "wall": tile_wall,
    "box": tile_box,
    "goal": tile_goal,
    "player": tile_player,
}

OUTLINE_ONLY = {"box"}
SILHOUETTE_OUTLINE = {"player": OUTL}


def build_calls(only=None):
    calls = []
    for name, fn in TILES.items():
        if only and name not in only:
            continue
        fn_res = fn()
        base, shade = split(fn_res)
        base_px = base.pixels()
        if name in SILHOUETTE_OUTLINE:
            base_px = fn_res.outline(SILHOUETTE_OUTLINE[name]) + base_px
        fname = f"tiles/{name}.aseprite"
        calls.append(["create_canvas", {"width": N, "height": N, "filename": fname}])
        calls.append(["add_layer", {"filename": fname, "layer_name": "base"}])
        calls.append(["add_layer", {"filename": fname, "layer_name": "shade"}])
        calls.append(["draw_pixels_at", {"filename": fname, "layer_name": "base",
                                         "frame_index": 1, "pixels": base_px}])
        calls.append(["draw_pixels_at", {"filename": fname, "layer_name": "shade",
                                         "frame_index": 1, "pixels": shade.pixels()}])
        if name in OUTLINE_ONLY:
            oc = CR_OUT if name == "box" else OUTL
            # outline both cels so the silhouette border is complete
            calls.append(["outline_cel", {"filename": fname, "layer_name": "base",
                                          "frame_index": 1, "color": oc}])
        calls.append(["export_frame", {"filename": fname, "frame_index": 1,
                                       "output_filename": f"tiles/{name}_1x.png",
                                       "scale": 1}])
    return calls


if __name__ == "__main__":
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 and sys.argv[1] != "--all" else None
    calls = build_calls(only)
    with open(os.path.join(ART, "calls.json"), "w", encoding="utf-8") as fh:
        json.dump(calls, fh)
    os.makedirs(os.path.join(ART, "tiles"), exist_ok=True)
    names = [n for n in TILES if not only or n in only]
    print(f"calls={len(calls)} for {','.join(names)}")
    for name in names:
        g = TILES[name]()
        cols = {}
        for p in g.pixels():
            cols[p["color"]] = cols.get(p["color"], 0) + 1
        print(f"  {name:7s} pixels={sum(cols.values()):5d} colors={len(cols)}")
