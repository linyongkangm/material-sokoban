"""Build player_preview.png: bust, swatch, and one idle frame per direction.

A script rather than a throwaway command on purpose - derived previews built by
hand have twice gone stale against the sprite they came from. Reads the 4x sheet
so it always shows what is actually in player.aseprite.
"""
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, os.pardir, "player")
PAPER = (242, 240, 247, 255)
CELL = 128 + 1          # 4x frame plus the 1px sheet padding
DIRS = ["down", "left", "right", "up"]


DERIVED = ["sheet.png", "sheet.json", "avatar_64.png", "swatch.png",
           "walk_down.gif", "walk_left.gif", "walk_right.gif", "walk_up.gif"]


def check_fresh():
    """Warn if anything was exported before the sprite was last written.

    Twice this session a stale artifact looked completely valid: a failed
    saveCopyAs left the previous file in place, and a GIF predated the redraw.
    """
    src = os.path.join(P, "player.aseprite")
    if not os.path.exists(src):
        return ["player.aseprite is missing - run tools/player.lua"]
    mtime = os.path.getmtime(src)
    stale = [f for f in DERIVED
             if not os.path.exists(os.path.join(P, f))
             or os.path.getmtime(os.path.join(P, f)) < mtime]
    return [f"{f} is older than player.aseprite - re-export it" for f in stale]


def main():
    for warn in check_fresh():
        print("STALE:", warn)
    sheet = Image.open(os.path.join(P, "sheet.png")).convert("RGBA")
    av = Image.open(os.path.join(P, "avatar_64.png")).convert("RGBA")
    sw = Image.open(os.path.join(P, "swatch.png")).convert("RGBA")

    out = Image.new("RGBA", (560, 220), PAPER)
    out.alpha_composite(av.resize((128, 128), Image.NEAREST), (20, 46))
    out.alpha_composite(sw.resize((sw.width * 2, sw.height * 2), Image.NEAREST), (20, 186))
    for i in range(len(DIRS)):
        fr = sheet.crop((i * 4 * CELL, 0, i * 4 * CELL + 128, 128))
        out.alpha_composite(fr.resize((64, 64), Image.NEAREST), (200 + i * 88, 78))
    dest = os.path.join(P, "player_preview.png")
    out.save(dest)
    print(f"player/player_preview.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
