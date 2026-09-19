#!/usr/bin/env python3
"""First pass at colour-matching the shop grid: measure each grid picture's backdrop (its outer frame, where
the studio linen shows), take the median colour across all pieces as the target, and work out the warm/tint
that brings each one to it. Writes content "tile": warm, tint (fine-tune by eye in the lab).

    python3 pdp/tools/match_tiles.py            # dry run: prints the values
    python3 pdp/tools/match_tiles.py --write    # saves them to content.json
"""
import json, os, sys
import numpy as np
from PIL import Image

PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PDP)
import build_pdp as B                                   # grid_still, tile_src, tint_gains

C = json.load(open(os.path.join(PDP, "content.json")))
slugs = [s for s in (C.get("order") or []) if s in C["products"] and not C["products"][s].get("hidden")]

def backdrop(src):
    a = np.asarray(Image.open(os.path.join(PDP, src)).convert("RGB"), float)
    h, w = a.shape[:2]; m = np.zeros((h, w), bool); b = int(min(h, w) * .15)
    m[:b] = m[-b:] = True; m[:, :b] = m[:, -b:] = True
    px = a[m]; lum = px.mean(1)
    px = px[(lum > 60) & (lum < 235)]                     # the linen, not deep shadow or blown highlight
    return px.mean(0)

meas = {s: backdrop(B.tile_src(B.grid_still(s))) for s in slugs}
chroma = {s: v / v[1] for s, v in meas.items()}           # r/g and b/g: colour, independent of brightness
target = np.median(np.array(list(chroma.values())), 0)

best = {}
W = np.arange(-20, 20.5, .5)
for s, c in chroma.items():
    err, pick = 9, (0, 0)
    for w in W:
        for t in W:
            g = np.array(B.tint_gains(w, t)); o = c * g; o = o / o[1]
            e = abs(o[0] - target[0]) + abs(o[2] - target[2]) + 0.0004 * (abs(w) + abs(t))   # the smallest change that gets there
            if e < err: err, pick = e, (w, t)
    best[s] = pick
    print(f"{s:22} r/g {c[0]:.3f} b/g {c[2]:.3f}  ->  warm {pick[0]:+5.1f}  tint {pick[1]:+5.1f}")
print("target r/g %.3f b/g %.3f" % (target[0], target[2]))

if "--write" in sys.argv:
    for s, (w, t) in best.items():
        tile = C["products"][s].setdefault("tile", {})
        tile["warm"], tile["tint"] = float(w), float(t)
    json.dump(C, open(os.path.join(PDP, "content.json"), "w"), indent=1, ensure_ascii=False)
    print("saved")
