"""How alike two pieces look, for ordering Also Worth Keeping on phones.

Each piece is read from its grid photograph: the piece is separated from the
backdrop (the backdrop is whatever colour fills the edges), then compared on
two things a person notices first: its colours (bronze patina, gold, silver)
and its outline (tall, wide, round). Scores are cached in visual_match.json.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "visual_match.json")


def features(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((240, 240))
    a = np.asarray(im, dtype=float)
    h, w, _ = a.shape
    edge = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    bg = np.median(edge, axis=0)
    mask = np.linalg.norm(a - bg, axis=2) > 38                 # the piece: clearly unlike the backdrop
    if mask.sum() < 50:
        mask = np.ones((h, w), bool)
    px = a[mask]
    hist, _ = np.histogramdd(px, bins=(6, 6, 6), range=((0, 256),) * 3)
    hist = hist.ravel() / hist.sum()
    ys, xs = np.nonzero(mask)
    bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    fill = mask.sum() / (bw * bh)                               # round and solid, or open and spindly
    return hist, math.log(bh / bw), fill


def score(f1, f2):
    colour = np.minimum(f1[0], f2[0]).sum()                     # 1 = the same colours
    shape = math.exp(-abs(f1[1] - f2[1])) * (1 - abs(f1[2] - f2[2]))
    return 0.6 * colour + 0.4 * shape


def build(photos):
    """photos: {slug: image path}. Returns {slug: {other: score}} and caches it."""
    feats = {s: features(p) for s, p in photos.items() if os.path.exists(p)}
    out = {a: {b: round(score(fa, fb), 4) for b, fb in feats.items() if b != a} for a, fa in feats.items()}
    json.dump(out, open(CACHE, "w"), indent=1, sort_keys=True)
    return out
