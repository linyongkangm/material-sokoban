"""Render the avatar preview sheet: 4x, card mock, and true 1x size.

Kept separate from compose.py because the avatar is 64x64 and gets cropped by
the card frame, unlike the seamless 32x32 tiles.
"""
import os
import sys

from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ART, "murdoku", "avatar_player_4x.png")
PAPER = (242, 240, 247, 255)
INK = (25, 25, 34, 255)
CARD = (248, 247, 251, 255)

# accent bar per character, so a roster reads apart at a glance
ACCENT = {"teal": (92, 172, 181, 255), "brick": (165, 81, 66, 255),
          "peri": (163, 171, 210, 255), "ochre": (224, 169, 63, 255)}


def main() -> None:
    accent = ACCENT[sys.argv[1] if len(sys.argv) > 1 else "teal"]
    av = Image.open(SRC).convert("RGBA")
    pw, ph = av.size
    gap = 16
    out = Image.new("RGBA", (pw * 2 + gap * 3 + 150, ph + gap * 2), PAPER)
    out.alpha_composite(av, (gap, gap))

    card = Image.new("RGBA", (pw + 8, ph + 8), INK)
    d = ImageDraw.Draw(card)
    d.rectangle([4, 4, card.width - 5, card.height - 5], fill=CARD)
    d.rectangle([4, 4, 26, card.height - 5], fill=accent)
    card.alpha_composite(av, (30, 4))
    out.alpha_composite(card, (gap * 2 + pw, gap))

    x = gap * 3 + pw * 2
    out.alpha_composite(av.resize((128, 128), Image.LANCZOS), (x, gap))
    out.alpha_composite(av.resize((64, 64), Image.LANCZOS), (x, gap + 128 + 8))
    out.save(os.path.join(ART, "avatar_preview.png"))
    print(f"avatar_preview.png {out.size[0]}x{out.size[1]}")


if __name__ == "__main__":
    main()
