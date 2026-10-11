"""Build lumine/lumine_walk_showcase.png - the walk cycle in one picture.

GIFs do not animate in a still viewer, so each direction is a 4-frame
filmstrip. The sheet is a single row of 16 frames at 2x, one row per direction
here, plus a 1x strip at the bottom because that is the size the game draws
at. A script rather than a throwaway command: derived previews built by hand
have gone stale twice this session.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, os.pardir, "lumine")
PAPER = (242, 240, 247, 255)
INK = (36, 30, 51, 255)
MUTED = (120, 124, 140, 255)
CELL, FW, FH = 129, 128, 200          # 2x frame plus the 1px sheet padding
DIRS = ["down", "left", "right", "up"]


def font(px, bold=True):
    for name in ("msyhbd.ttc", "msyh.ttc") if bold else ("msyh.ttc",):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, px)
        except OSError:
            continue
    for name in ("arialbd.ttf" if bold else "arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def check_fresh():
    src = os.path.join(OUT, "lumine_walk.aseprite")
    if not os.path.exists(src):
        return ["lumine_walk.aseprite is missing - run tools/lumine_walk.lua"]
    mtime = os.path.getmtime(src)
    derived = ["lumine_walk_sheet.png", "lumine_walk.json"] + [
        f"walk_{d}.gif" for d in DIRS]
    out = []
    for f in derived:
        p = os.path.join(OUT, f)
        if not os.path.exists(p) or os.path.getmtime(p) < mtime:
            out.append(f"{f} is older than lumine_walk.aseprite - re-export it")
    return out


def main():
    for warn in check_fresh():
        print("STALE:", warn)
    sheet = Image.open(os.path.join(OUT, "lumine_walk_sheet.png")).convert("RGBA")
    fr = lambda i: sheet.crop((i * CELL, 0, i * CELL + FW, FH))

    label = 26
    W = 200 + 4 * (FW + 12)
    H = 90 + len(DIRS) * (FH + label) + FH + 60
    out = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(out)
    d.text((24, 16), "Lumine  \u8367  walk", font=font(24), fill=INK)
    d.text((24, 48), "64x100 \u00b7 4 directions \u00b7 4 frames \u00b7 2x", font=font(12, False),
           fill=MUTED)

    for i, name in enumerate(DIRS):
        y = 90 + i * (FH + label)
        d.text((24, y + 4), f"walk_{name}", font=font(13, False), fill=MUTED)
        for ph in range(4):
            out.alpha_composite(fr(i * 4 + ph), (200 + ph * (FW + 12), y))

    y1 = 90 + len(DIRS) * (FH + label) + 10
    d.text((24, y1 + 4), "1x", font=font(12, False), fill=MUTED)
    for i in range(16):
        out.alpha_composite(fr(i).resize((64, 100), Image.NEAREST),
                            (200 + i * 70, y1))

    out.save(os.path.join(OUT, "lumine_walk_showcase.png"))
    print(f"lumine/lumine_walk_showcase.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
