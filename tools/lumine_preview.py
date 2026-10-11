"""Build lumine/lumine_preview.png - the portrait at 3x and 1x plus its palette.

A script rather than a throwaway command: derived review images built by hand
have gone stale twice this session. Also warns when lumine.png predates the
.aseprite it came from.
"""
import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, os.pardir, "lumine")
PAPER = (242, 240, 247, 255)
INK = (36, 30, 51, 255)
MUTED = (120, 124, 140, 255)
SCALE = 3
CELL = 34


def font(px, bold=True):
    # msyh first: the title carries 荧 and Arial renders it as a tofu box
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
    src = os.path.join(OUT, "lumine.aseprite")
    png = os.path.join(OUT, "lumine.png")
    if not os.path.exists(src):
        return ["lumine.aseprite is missing - run tools/lumine.lua"]
    if not os.path.exists(png) or os.path.getmtime(png) < os.path.getmtime(src):
        return ["lumine.png is older than lumine.aseprite - re-export it"]
    return []


def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def main():
    for warn in check_fresh():
        print("STALE:", warn)
    im = Image.open(os.path.join(OUT, "lumine.png")).convert("RGBA")
    big = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
    counts = Counter(p[:3] for p in im.getdata() if p[3] > 0)
    palette = sorted(counts, key=lambda c: -luminance(c))

    W = max(big.width + im.width + 96, len(palette) * CELL + 48)
    H = big.height + len(palette) // 8 * CELL + 190
    out = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(out)

    d.text((24, 14), "Lumine  \u8367", font=font(26), fill=INK)
    d.text((24, 48), f"{im.width}x{im.height}  ·  {SCALE}x and 1x  ·  "
                     f"{len(palette)} colours", font=font(12, False), fill=MUTED)
    out.alpha_composite(big, (24, 74))
    x1 = 24 + big.width + 40
    out.alpha_composite(im, (x1, 74))
    d.text((x1, 58), "1x", font=font(11, False), fill=MUTED)

    y = 74 + big.height + 26
    d.text((24, y - 16), "palette, brightest first", font=font(11, False), fill=MUTED)
    for i, rgb in enumerate(palette):
        cx = 24 + (i % 8) * CELL
        cy = y + (i // 8) * CELL
        d.rectangle([cx, cy, cx + CELL - 8, cy + 18], fill=rgb + (255,), outline=INK)
        d.text((cx + 1, cy + 20), f"#{'%02X%02X%02X' % rgb}  {counts[rgb]}",
               font=font(9, False), fill=MUTED)

    out.save(os.path.join(OUT, "lumine_preview.png"))
    print(f"lumine/lumine_preview.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
