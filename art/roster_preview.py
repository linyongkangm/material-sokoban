"""Render the suspect roster: 4x grid with name labels, plus a 1x strip.

The 1x row is the real acceptance test -- a roster only works if you can tell
the characters apart at the size a game actually draws them.
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ART = os.path.dirname(os.path.abspath(__file__))
AV = os.path.join(ART, "avatars")
Roster = [
    ("ada", "Ada"), ("brigitte", "Brigitte"), ("cameron", "Cameron"),
    ("darlene", "Darlene"), ("edison", "Edison"), ("vinita", "Vinita"),
    ("felix", "Felix"), ("gwen", "Gwen"), ("hassan", "Hassan"),
    ("ingrid", "Ingrid"), ("jorge", "Jorge"), ("kim", "Kim"),
]
PAPER = (242, 240, 247, 255)
INK = (25, 25, 34, 255)
CARD = (248, 247, 251, 255)
COLS, S, GAP = 4, 4, 18


def font(px):
    for path in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(path, px)
        except OSError:
            continue
    return ImageFont.load_default()


def primaries():
    """Character primary colours, from the pack manifest.

    The card accent bar used to sample a pixel out of the avatar to guess at
    this; the manifest is now the single source of truth. Falls back to the
    sample only if the pack has not been rendered yet.
    """
    path = os.path.join(ART, os.pardir, "character", "pack.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return {c["name"]: c["primary"] for c in data["characters"]}
    except (OSError, ValueError, KeyError):
        return {}


def rgba(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def main():
    cell = 64 * S
    PRI = primaries()
    rows = (len(Roster) + COLS - 1) // COLS
    label_h = 34
    grid_h = rows * (cell + label_h) + GAP
    strip_h = 64 + 2 * GAP
    W = COLS * cell + (COLS + 1) * GAP
    out = Image.new("RGBA", (W, grid_h + strip_h), PAPER)
    draw = ImageDraw.Draw(out)
    big, small = font(22), font(14)

    for i, (slug, name) in enumerate(Roster):
        im = Image.open(os.path.join(AV, f"{slug}_1x.png")).convert("RGBA")
        r, c = divmod(i, COLS)
        x = GAP + c * (cell + GAP)
        y = GAP + r * (cell + label_h + GAP)
        # card plate: the avatar sits in a bordered tile with its own accent bar
        plate = Image.new("RGBA", (cell + 8, cell + 8), INK)
        d = ImageDraw.Draw(plate)
        d.rectangle([4, 4, cell + 3, cell + 3], fill=CARD)
        d.rectangle([4, 4, 20, cell + 3],
                    fill=rgba(PRI[slug]) if slug in PRI else im.getpixel((6, 60)))
        plate.alpha_composite(im.resize((cell, cell), Image.NEAREST), (24, 4))
        out.alpha_composite(plate, (x - 4, y - 4))
        bb = draw.textbbox((0, 0), name, font=big)
        draw.text((x + (cell - bb[2] + bb[0]) // 2, y + cell + 4),
                  name, font=big, fill=INK)

    for i, (slug, name) in enumerate(Roster):
        im = Image.open(os.path.join(AV, f"{slug}_1x.png")).convert("RGBA")
        x = GAP + i * (64 + 10)
        out.alpha_composite(im, (x, grid_h + GAP))
        draw.text((x, grid_h + GAP + 66), name[:4], font=small, fill=INK)

    dest = os.path.join(ART, "roster_preview.png")
    out.save(dest)
    print(f"roster_preview.png {out.size[0]}x{out.size[1]}")


def sheets():
    """Engine-ready strips, written here so they cannot drift from the
    per-character PNGs the review image uses. They once did: the sheets came
    from a throwaway command and kept showing a rejected pass.
    """
    ims = [Image.open(os.path.join(AV, f"{slug}_1x.png")).convert("RGBA")
           for slug, _ in Roster]
    for scale, tag in ((1, "1x"), (4, "4x")):
        cell = 64 * scale
        out = Image.new("RGBA", (cell * len(ims), cell))
        for i, im in enumerate(ims):
            out.alpha_composite(im.resize((cell, cell), Image.NEAREST), (i * cell, 0))
        dest = os.path.join(AV, f"roster_sheet_{tag}.png")
        out.save(dest)
        print(f"avatars/roster_sheet_{tag}.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
    sheets()
