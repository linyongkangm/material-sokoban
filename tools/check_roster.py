"""Roster integrity gate.

Two checks that have each already caught a real defect:
  1. hair vs primary(shirt) luminance contrast - a token's rim and core merge
     when these are close (Edison shipped at 1.08:1).
  2. hair vs skin luminance contrast - brightening hair to fix (1) can make it
     vanish into the face instead (felix would have hit 1.10:1 that way).
Plus: the avatars/ sheet must match the individual PNGs, and the six locked
suspects must be byte-identical to their approved fingerprints.
"""
import hashlib
import json
import os
import re
import sys

from PIL import Image, ImageChops

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
AV = os.path.join(ROOT, "character", "avatars")
CHAR = os.path.join(ROOT, "character")
LOCKED = ["ada", "brigitte", "cameron", "darlene", "edison", "vinita"]
# Hard gate: token rim (primary) vs core (hair). This is the pair that shipped
# broken once, at 1.08:1.
FLOOR = 2.7
# Informational only. A light-haired, light-skinned suspect is perfectly
# readable - the avatar separates them with an ink line and the token's skin
# pip is 5px. The approved roster itself sits at 1.07-1.11 here, so making this
# a failure would only train everyone to ignore the gate.
SKIN_NOTE = 2.7
ACCEPTED = {
    "edison": "user chose hair #6F7E7B knowing it measures 1.88:1 vs his shirt",
}


def lum(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def chars():
    """Parse the CHARS table in roster.lua.

    Splits on the `n='name'` markers rather than matching whole entries: an
    entry contains nested braces (the prof anchor list) that break naive
    non-greedy matching, and a parser that silently returns {} here would turn
    this gate into a no-op.
    """
    src = open(os.path.join(TOOLS, "roster.lua"), encoding="utf-8").read()
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"n='(\w+)'", src)]
    out = {}
    for i, (pos, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(src)
        body = src[pos:end]
        g = lambda k: (re.search(k + r"='(#\w{6})'", body) or [None, None])[1]
        hair, skin, shirt = g("hair"), g("skin"), g("shirt")
        if hair and skin and shirt:
            out[name] = {"hair": hair, "skin": skin, "shirt": shirt, "primary": shirt}
    return out


def main():
    c = chars()
    if len(c) < 6:
        print(f"FAIL: parsed only {len(c)} characters from roster.lua - the parser "
              "is broken, which would make every other check a no-op")
        return 1
    fails = []

    print(f"luminance separation (hard floor {FLOOR}:1 on hair/primary, "
          f"note {SKIN_NOTE}:1 on hair/skin):")
    for n, v in c.items():
        r1, r2 = ratio(v["hair"], v["primary"]), ratio(v["hair"], v["skin"])
        notes = []
        if r1 < FLOOR:
            if n in ACCEPTED:
                notes.append("hair/primary accepted")
            else:
                notes.append("hair/primary")
                fails.append(f"{n}: hair/primary {r1:.2f}:1 below floor")
        if r2 < SKIN_NOTE:
            notes.append("hair/skin (info)")
        mark = "  <-- " + ", ".join(notes) if notes else ""
        print(f"  {n:9s} hair {v['hair']}  rim {r1:5.2f}:1  skin {r2:5.2f}:1{mark}")
    for n, why in ACCEPTED.items():
        if n in c:
            print(f"\naccepted exception: {n} - {why}")

    manifest = json.load(open(os.path.join(CHAR, "pack.json"), encoding="utf-8"))
    for e in manifest["characters"]:
        if e["palette"][0] != e["primary"]:
            fails.append(f"{e['name']}: swatch cell 0 is not the primary colour")
    print(f"\nmanifest: {len(manifest['characters'])} characters, primary-first verified")

    names = list(c)
    sheet = Image.open(os.path.join(AV, "roster_sheet_1x.png")).convert("RGBA")
    if sheet.width != 64 * len(names):
        fails.append(f"sheet width {sheet.width} != {64 * len(names)} - rerun roster_preview.py")
    for i, n in enumerate(names):
        ind = Image.open(os.path.join(AV, f"{n}_1x.png")).convert("RGBA")
        if ImageChops.difference(ind, sheet.crop((i * 64, 0, (i + 1) * 64, 64))).getbbox():
            fails.append(f"{n}: sheet cell differs from individual PNG")
    print("sheet vs individuals: checked", len(names))

    fp = os.path.join(TOOLS, "roster_locked.sha256")
    if os.path.exists(fp):
        want = {}
        for line in open(fp):
            parts = line.split()
            if len(parts) == 2 and len(parts[0]) == 64:
                want[parts[1].lstrip("*")] = parts[0]
        compared = 0
        for n in LOCKED:
            for f in (f"{n}.aseprite", f"{n}_1x.png"):
                got = hashlib.sha256(open(os.path.join(AV, f), "rb").read()).hexdigest()
                if f not in want:
                    # a missing fingerprint used to be skipped silently, which is
                    # how a gate passes while checking nothing at all
                    fails.append(f"no fingerprint recorded for locked asset {f}")
                elif want[f] != got:
                    fails.append(f"LOCKED asset changed: {f}")
                else:
                    compared += 1
        print(f"locked fingerprints: {compared}/{len(LOCKED) * 2} verified unchanged")
    else:
        print(f"no fingerprint file; write one with --pin to guard {len(LOCKED)} locked assets")

    if "--pin" in sys.argv:
        with open(fp, "w") as fh:
            for n in LOCKED:
                for f in (f"{n}.aseprite", f"{n}_1x.png"):
                    h = hashlib.sha256(open(os.path.join(AV, f), "rb").read()).hexdigest()
                    fh.write(f"{h}  {f}\n")
        print("pinned current state as the locked baseline")

    print("\n" + ("FAIL\n  " + "\n  ".join(fails) if fails else "ALL CHECKS PASS"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
