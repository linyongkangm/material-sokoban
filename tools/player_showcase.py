"""Build player/showcase.png - one image to review the heroine in.

GIFs do not animate in a still viewer, so each direction is laid out as a
4-frame filmstrip instead; that is the only way to judge the walk cycle from a
single picture.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, os.pardir, "player")
PAPER = (242, 240, 247, 255)
INK = (25, 25, 34, 255)
MUTED = (120, 124, 140, 255)
CELL = 129                     # 4x frame + 1px sheet padding
DIRS = ["down", "left", "right", "up"]
FS = 3                         # filmstrip frame scale


def font(px, bold=True):
    for name in ("arialbd.ttf" if bold else "arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    sheet = Image.open(os.path.join(P, "sheet.png")).convert("RGBA")
    av = Image.open(os.path.join(P, "avatar_64.png")).convert("RGBA")
    sw = Image.open(os.path.join(P, "swatch.png")).convert("RGBA")

    cell = 64 * FS
    rows = len(DIRS)
    strip_w = cell * 4 + 18 * 3
    left_w = 256 + 48
    W = left_w + strip_w + 60
    H = max(256 + 120, rows * (cell + 30) + 96) + 64
    out = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(out)

    d.text((24, 20), "Heroine", font=font(30), fill=INK)
    d.text((24, 56), "32x32 / 4 directions / 4 frames each", font=font(13, False), fill=MUTED)

    out.alpha_composite(av.resize((256, 256), Image.NEAREST), (24, 92))
    d.text((24, 352), "bust 64px  ·  palette", font=font(12, False), fill=MUTED)
    out.alpha_composite(sw.resize((sw.width * 4, sw.height * 4), Image.NEAREST), (24, 372))

    x0 = left_w + 36
    for i, name in enumerate(DIRS):
        y = 92 + i * (cell + 30)
        d.text((x0, y - 18), f"walk_{name}", font=font(13, False), fill=MUTED)
        for ph in range(4):
            fr = sheet.crop(((i * 4 + ph) * CELL, 0, (i * 4 + ph) * CELL + 128, 128))
            out.alpha_composite(fr.resize((cell, cell), Image.NEAREST), (x0 + ph * (cell + 18), y))

    # 1x row: the filmstrips flatter her. This is the size the game draws at,
    # and the only honest legibility test.
    y1 = H - 52
    d.text((x0, y1 - 16), "1x  ·  in-game size", font=font(12, False), fill=MUTED)
    for i in range(16):
        fr = sheet.crop((i * CELL, 0, i * CELL + 128, 128)).resize((32, 32), Image.NEAREST)
        out.alpha_composite(fr, (x0 + i * 36, y1))

    dest = os.path.join(P, "showcase.png")
    out.save(dest)
    print(f"player/showcase.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
