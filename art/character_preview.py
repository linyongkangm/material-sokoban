"""Contact sheet for the character pack: avatar + token + swatch per row.

Reads the delivered PNGs from character/ so it checks the actual artifacts,
not an in-memory copy.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR = os.path.join(ROOT, "character")
NAMES = ["ada", "brigitte", "cameron", "darlene", "edison", "vinita"]
S = 2
PAPER = (242, 240, 247, 255)
INK = (25, 25, 34, 255)
MUTED = (120, 124, 140, 255)
ROW_H = 64 * S + 30
PAD = 18


def font(px):
    for name in ("arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/" + name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    big, small = font(20), font(13)
    W = 620
    out = Image.new("RGBA", (W, ROW_H * len(NAMES) + 46), PAPER)
    d = ImageDraw.Draw(out)
    d.text((PAD, 12), "character pack", font=big, fill=INK)
    d.text((W - 250, 16), "avatar 64   token 32   swatch", font=small, fill=MUTED)

    y = 46
    for n in NAMES:
        av = Image.open(os.path.join(CHAR, f"{n}_avatar.png")).convert("RGBA")
        tk = Image.open(os.path.join(CHAR, f"{n}_token.png")).convert("RGBA")
        sw = Image.open(os.path.join(CHAR, f"{n}_swatch.png")).convert("RGBA")
        x = PAD
        for im in (av, tk, sw):
            up = im.resize((im.width * S, im.height * S), Image.NEAREST)
            out.alpha_composite(up, (x, y + (ROW_H - 20 - up.height) // 2))
            x += up.width + 22
        d.text((x + 8, y + 24), n.capitalize(), font=big, fill=INK)
        d.text((x + 8, y + 48), f"{sw.width // 8} colours", font=small, fill=MUTED)
        y += ROW_H

    dest = os.path.join(ROOT, "art", "character_preview.png")
    out.save(dest)
    print(f"art/character_preview.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
