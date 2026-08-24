#!/usr/bin/env python3
"""Pin a couple of blank cards to the hero plate's wall.

Composited into the plate rather than laid over it in the browser, so they take
the plate's own grain and sit behind everything at the right depth. Each gets a
soft offset shadow — the light on these plates comes from camera-left, so the
shadow falls right and slightly down.

Dimensions are unchanged, so the composition's fractions still hold.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLATE = os.path.join(ROOT, "shelf/plates/dressed/dressed-thresh-b-trim.png")
OUT = os.path.join(ROOT, "shelf/plates/dressed/dressed-thresh-b-wall.png")
CARRIERS = os.path.join(ROOT, "shelf/carriers")

# x, y are the item's centre as a fraction of the plate; w is its width likewise.
ITEMS = [
    dict(src="letterpress-card.png", x=0.255, y=0.300, w=0.088, rot=-2.0),
    dict(src="apothecary-oval.png",  x=0.742, y=0.268, w=0.066, rot=1.5),
]


def main():
    plate = Image.open(PLATE).convert("RGBA")
    W, H = plate.size
    for it in ITEMS:
        card = Image.open(os.path.join(CARRIERS, it["src"])).convert("RGBA")
        tw = int(W * it["w"])
        card = card.resize((tw, max(1, round(card.height * tw / card.width))), Image.LANCZOS)
        card = card.rotate(it["rot"], expand=True, resample=Image.BICUBIC)

        shadow = Image.new("RGBA", card.size, (54, 46, 36, 0))
        shadow.putalpha(card.getchannel("A").point(lambda v: int(v * 0.42)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, tw * 0.022)))

        cx, cy = int(W * it["x"]), int(H * it["y"])
        off = max(2, int(tw * 0.02))
        plate.alpha_composite(shadow, (cx - card.width // 2 + off, cy - card.height // 2 + off))
        plate.alpha_composite(card, (cx - card.width // 2, cy - card.height // 2))
        print(f"{it['src']:22} {card.size} at {it['x']:.3f},{it['y']:.3f}")

    plate.convert("RGB").save(OUT)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
