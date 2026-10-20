#!/usr/bin/env python3
"""The jewelry's grey-backdrop photos, made like the totems' (tools/grey_backdrop.py) but for silver.

    python3 pdp/tools/jewelry_backdrop.py [out_pdp]          (default: this pdp)

From ~/Downloads/Maçon/WHITE-BG-JEWELRY: each photo cut to 5:4, its backdrop made the totems' one flat warm grey
(224, 222, 220) with its own grain, the piece 15% smaller in frame. No golden warming (that was for the totems'
bronze heads). Then the pieces' contrast is evened out across the set: each piece's spread of light and dark is
brought towards the set's middle, gently (never more than about a quarter either way), on the piece only.
Saved at full resolution as img/<slug>/white-1.jpg (quality 95, full colour), the flat copy kept in _originals.
Then run tools/optimize_media.py and build_pdp.py in the same pdp.
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grey_backdrop as G

G.SRC = os.path.expanduser("~/Downloads/Maçon/WHITE-BG-JEWELRY")
PIECES = {          # slug: the file sent
    "ear-cuff": "Caldera Arc White 2.jpg",
    "eclipse-ring": "Eclipse Ring White 1.jpg",
    "wonderhorn-talisman": "Ida Horn White 1.jpeg",
    "lunar-canyon-ring": "Lunar Canyon White 1.jpg",
    "meridian-egg-ring": "Meridian Egg White 1.jpg",
    "sietch-aperture": "Sietch White 1.jpeg",
    "zuma-ring": "Zuma Ring Whote 1.png",
}


def piece_mask(a):
    """0..1: the piece (and nothing of the flat grey), feathered."""
    q = 4
    small = ndimage.zoom(a, (1 / q, 1 / q, 1), order=1)
    dev = ndimage.gaussian_filter(np.abs(small - G.TARGET).max(2), 1.5)
    fg = ndimage.binary_opening(dev > 14, iterations=2)
    lab, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        fg = np.isin(lab, [i + 1 for i in range(n) if sizes[i] > 0.04 * sizes.max()])
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(fg, iterations=3))
    m = ndimage.gaussian_filter(fg.astype(np.float32), 2)
    return np.clip(ndimage.zoom(m, (a.shape[0] / m.shape[0], a.shape[1] / m.shape[1]), order=1)[:a.shape[0], :a.shape[1]], 0, 1)


def spread(a, m):
    L = a.mean(2)[m > .9]
    return np.percentile(L, 98) - np.percentile(L, 2), L.mean()


if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else G.PDP
    flats = {}
    for slug, f in PIECES.items():
        a = np.asarray(G.flatten(f)).astype(np.float32)
        m = piece_mask(a)
        flats[slug] = (a, m, *spread(a, m))
        print(f"{slug:22s} contrast {flats[slug][2]:.0f}  mean {flats[slug][3]:.0f}")
    target = float(np.median([v[2] for v in flats.values()]))
    for slug, (a, m, rng, mean) in flats.items():
        k = float(np.clip(target / rng, .8, 1.25)) if rng > 1 else 1.0
        even = mean + (a - mean) * k          # around the piece's own middle grey, so it neither darkens nor brightens overall
        res = np.clip(a * (1 - m[..., None]) + even * m[..., None], 0, 255).round().astype(np.uint8)
        for d in ("_originals", "img"):
            os.makedirs(os.path.join(out, d, slug), exist_ok=True)
        Image.fromarray(a.round().astype(np.uint8)).save(os.path.join(out, "_originals", slug, "white-1.flat.jpg"), quality=95, subsampling=0)
        for d in ("_originals", "img"):
            Image.fromarray(res).save(os.path.join(out, d, slug, "white-1.jpg"), quality=95, subsampling=0)          # full colour detail
        print(f"{slug:22s} x{k:.2f} -> {res.shape[1]}x{res.shape[0]}")
