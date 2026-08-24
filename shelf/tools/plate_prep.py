#!/usr/bin/env python3
"""Trim the uprights, and square off the top and bottom of each plate.

The steel uprights were invented separately on every plate, so stacked they never
line up and the shelving reads as two or three different units. Cropping them off
removes the mismatch at its source — no grating, nothing to disagree.

Also squares the plate ends: the hero is cut at the bottom of its lower shelf, and
the bronze plate gains room below its last shelf.

Prints the transform for each plate so the composition's fractions can be moved
with it — every position in that file is a fraction of the plate, so a crop that
is not mirrored there silently shifts every piece.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "shelf", "plates", "dressed")
XL, XR = 0.066, 0.934          # keep this much of the width; the rest is upright

JOBS = {
    "dressed-thresh-b":   dict(src="dressed-thresh-b.png",   cut_bottom=0.9854, extend=0),
    "dressed-bronze-b-eq": dict(src="dressed-bronze-b-eq.png", cut_bottom=1.0,    extend=64,
                                extend_from=(0.600, 0.640)),
}


def main():
    for name, job in JOBS.items():
        im = Image.open(os.path.join(D, job["src"])).convert("RGB")
        W, H = im.size
        x0, x1 = int(round(W * XL)), int(round(W * XR))
        y1 = int(round(H * job["cut_bottom"]))
        out = im.crop((x0, 0, x1, y1))

        if job["extend"]:
            a = np.asarray(out).astype(np.float32)
            pad = job["extend"]
            # continue downward with the rows just above, so the added strip is
            # the same surface rather than an invented one
            # Neither tiling a block nor repeating the last row works: the last
            # row still contains the bottoms of books and a vase, which smear into
            # vertical streaks. Take a band of plain wall instead and mirror it,
            # which has no features to repeat visibly.
            b0, b1 = job["extend_from"]
            band = a[int(round(H * b0)):int(round(H * b1))]
            mirrored = np.vstack([band, band[::-1]])
            reps = int(np.ceil(pad / mirrored.shape[0]))
            strip = np.vstack([mirrored] * reps)[:pad]
            k = 8
            wgt = np.ones((pad, 1, 1), np.float32)
            wgt[:k, 0, 0] = np.linspace(0, 1, k)
            base = np.repeat(a[-1:], pad, axis=0)
            grown = np.vstack([a, base * (1 - wgt) + strip * wgt])
            out = Image.fromarray(np.clip(grown, 0, 255).astype(np.uint8))

        dst = os.path.join(D, f"{name}-trim.png")
        out.save(dst)
        nW, nH = out.size
        print(f"{name}: {W}x{H} -> {nW}x{nH}")
        print(f"    x' = (x*{W} - {x0}) / {nW}")
        print(f"    y' = y*{H} / {nH}")


if __name__ == "__main__":
    main()
