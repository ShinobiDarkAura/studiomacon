#!/usr/bin/env python3
"""Build the go/no-go test sheet: two cutouts placed on a plate.

Also writes an alpha-check sheet on magenta, because a cutout viewed on a light
background hides exactly the fringe you need to see.
"""
import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUT = os.path.join(ROOT, "shelf", "cutouts")
OUT = os.path.join(ROOT, "shelf", "_test")

# x, y are fractions of the plate; y is where the object's BASE meets the shelf.
# w is object width as a fraction of plate width (BUILD-GUIDE §3).
# The only genuinely empty stretch of this plate is between the bowl and the
# pocket watch — it is a dressed still life, not a bare stage. Scale is anchored
# to real dimensions: Milo is 38mm wide, the Zuma ring ~20mm.
PLACEMENTS = [
    {"sprite": "obj-milo-1-shadow.png", "x": 0.437, "y": 0.578, "w": 0.115},
]


def place(plate, spec):
    """x, y put the OBJECT's base on the shelf; w is the object's width.

    Both are read off the sidecar written by cut.py, so the shadow's extent never
    leaks into the placement maths.
    """
    name = spec["sprite"]
    sp = Image.open(os.path.join(CUT, name)).convert("RGBA")
    meta = json.load(open(os.path.join(CUT, os.path.splitext(name)[0] + ".json")))
    W, H = plate.size

    # scale so the OBJECT (not the sprite) is w of the plate
    scale = (W * spec["w"]) / meta["object"][0]
    sp = sp.resize((max(1, round(sp.width * scale)), max(1, round(sp.height * scale))), Image.LANCZOS)
    bx, by = meta["base"][0] * scale, meta["base"][1] * scale

    px = round(W * spec["x"] - bx)
    py = round(H * spec["y"] - by)
    plate.alpha_composite(sp, (px, py))


def main():
    os.makedirs(OUT, exist_ok=True)
    plate = Image.open(os.path.join(ROOT, "shelf/plates/plate-shelf01.jpg")).convert("RGBA")
    for spec in PLACEMENTS:
        place(plate, spec)
    plate.convert("RGB").save(os.path.join(OUT, "sheet-plate.jpg"), quality=92)

    # alpha check — magenta ground so any halo or leftover fringe is obvious
    tiles = []
    for n in ("obj-milo-1.png", "obj-zuma-ring-3.png"):
        im = Image.open(os.path.join(CUT, n)).convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 0, 255, 255))
        bg.alpha_composite(im)
        tiles.append(bg.convert("RGB"))
    h = max(t.height for t in tiles)
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + 30, h), (255, 0, 255))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, h - t.height))
        x += t.width + 30
    sheet.save(os.path.join(OUT, "sheet-alpha.jpg"), quality=92)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
