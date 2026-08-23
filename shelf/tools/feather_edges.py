#!/usr/bin/env python3
"""Fade a sprite's shadow out where its own frame cut it.

Some generated scenes throw a shadow that runs off the edge of the image. The
clipping check only looks at the object, so those pass, and the harvest then crops
to the alpha box — leaving the shadow ending in a hard line partway through its
falloff. Rebi's stopped dead at 25% alpha.

Identifying a cut is the whole difficulty. "There is alpha at the border" proves
nothing: a sprite is cropped to its alpha box, so alpha touches all four borders
by definition. Neither does coverage — an object's antialiased tip and a severed
shadow occupy similar fractions of a border.

Colour settles it. The baked shadow is laid down as one known warm dark, so
shadow pixels sit at essentially zero distance from it while any part of the
object is twenty or more away. Only borders that are unmistakably shadow get
faded, and the object is never touched.

    python3 shelf/tools/feather_edges.py --dry
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPR = os.path.join(ROOT, "shelf", "sprites")
SHADOW_RGB = np.array([58, 48, 38], float)
NEAR = 6.0          # colour distance within which a pixel is the shadow tint
FLOOR = 0.05        # alpha below this is nothing
MIN_RUN = 12        # ignore a handful of stray pixels
DRY = "--dry" in sys.argv


def ramp(n, m):
    r = np.ones(n, np.float32)
    m = max(1, min(m, n // 2))
    r[:m] = np.linspace(0.0, 1.0, m)
    return r


def main():
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    touched = 0
    for slug in [k for k in pieces if not k.startswith("_")]:
        path = os.path.join(SPR, f"{pieces[slug]}.png")
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert("RGBA")
        a = np.asarray(im).astype(np.float32)
        al, rgb = a[..., 3] / 255.0, a[..., :3]
        h, w = al.shape

        cut = {}
        for k, idx in (("left", (slice(None), 0)), ("right", (slice(None), -1)),
                       ("top", (0, slice(None))), ("bottom", (-1, slice(None)))):
            line, cols = al[idx], rgb[idx]
            m = line > FLOOR
            if m.sum() < MIN_RUN:
                continue
            d = float(np.linalg.norm(cols[m] - SHADOW_RGB, axis=1).mean())
            if d < NEAR:
                cut[k] = (int(m.sum()), d)
        if not cut:
            continue

        touched += 1
        detail = ", ".join(f"{k} ({n}px, dist {d:.1f})" for k, (n, d) in cut.items())
        if DRY:
            print(f"{slug:22} would fade {detail}")
            continue
        mw, mh = max(12, int(w * 0.12)), max(12, int(h * 0.12))
        if "left" in cut:   al *= ramp(w, mw)[None, :]
        if "right" in cut:  al *= ramp(w, mw)[::-1][None, :]
        if "top" in cut:    al *= ramp(h, mh)[:, None]
        if "bottom" in cut: al *= ramp(h, mh)[::-1][:, None]
        a[..., 3] = np.clip(al * 255.0, 0, 255)
        out = Image.fromarray(a.astype(np.uint8), "RGBA")
        bb = out.getchannel("A").getbbox()
        (out.crop(bb) if bb else out).save(path)
        print(f"{slug:22} faded {detail}")
    if not touched:
        print("no cut shadows found")


if __name__ == "__main__":
    main()
