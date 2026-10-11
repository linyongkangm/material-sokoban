"""Assemble the 5 tiles into one 160x32 master sheet through the MCP tools.

draw_pixels_at takes sprite-global coordinates, so the sheet is just the same
pixel lists shifted by 32px per column. The master .aseprite is the file to open
in Aseprite; the exported PNG is what a game engine consumes.
"""
import importlib.util
import json
import os

spec = importlib.util.spec_from_file_location(
    "gen_sokoban", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_sokoban.py"))
gs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gs)

ORDER = ["floor", "wall", "box", "goal", "player"]
MASTER = "tiles/master.aseprite"
N = gs.N


def build():
    calls = [["create_canvas", {"width": N * len(ORDER), "height": N, "filename": MASTER}]]
    calls.append(["add_layer", {"filename": MASTER, "layer_name": "base"}])
    calls.append(["add_layer", {"filename": MASTER, "layer_name": "shade"}])
    base, shade = [], []
    for i, name in enumerate(ORDER):
        g = gs.TILES[name]()
        dx = i * N
        b, s = gs.split(g)
        bpx = b.pixels()
        if name in gs.SILHOUETTE_OUTLINE:
            bpx = g.outline(gs.SILHOUETTE_OUTLINE[name]) + bpx
        for p in bpx:
            base.append({"x": p["x"] + dx, "y": p["y"], "color": p["color"]})
        for p in s.pixels():
            shade.append({"x": p["x"] + dx, "y": p["y"], "color": p["color"]})
        # a slice per tile so a game can address each one by name
        calls.append(["create_slice", {"filename": MASTER, "name": name,
                                       "x": dx, "y": 0, "width": N, "height": N}])
    calls.append(["draw_pixels_at", {"filename": MASTER, "layer_name": "base",
                                     "frame_index": 1, "pixels": base}])
    calls.append(["draw_pixels_at", {"filename": MASTER, "layer_name": "shade",
                                     "frame_index": 1, "pixels": shade}])
    calls.append(["export_frame", {"filename": MASTER, "frame_index": 1,
                                   "output_filename": "tiles/sokoban_sheet.png", "scale": 1}])
    calls.append(["export_frame", {"filename": MASTER, "frame_index": 1,
                                   "output_filename": "tiles/sokoban_sheet_4x.png", "scale": 4}])
    calls.append(["get_color_stats", {"filename": MASTER, "frame_index": 1, "top": 40}])
    calls.append(["list_slices", {"filename": MASTER}])
    return calls


if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "calls_sheet.json"),
              "w", encoding="utf-8") as fh:
        json.dump(build(), fh)
    print("calls_sheet.json written")
