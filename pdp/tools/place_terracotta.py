#!/usr/bin/env python3
"""Place a terracotta-suede photograph as a piece's lead picture: tone matched to the totems' shoot,
cut 4:5 with the piece centred and sized as the totems sit in their frames, then written as
img/<slug>/terracotta.jpg (the product page's first picture) and img/ab-clay/<slug>(--tile).webp (the grids)."""
import sys, json, os
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TOTEMS = ["pip", "rebi", "ren", "zuma", "ori", "yael", "milo", "ibi", "eleph"]


def piece_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; mx, mn = a.max(-1), a.min(-1); s = (mx - mn) / (mx + 1e-6)
    return (s < .42) | ((r - b) < .18)          # the suede and its shadows are strongly orange; the piece is not


def background_stats(im):
    a = np.asarray(im.convert("RGB").resize((400, round(400 * im.height / im.width)))).astype(float) / 255
    bg = ~ndimage.binary_dilation(piece_mask(a), iterations=6)
    return a[bg].mean(0), a[bg].std(0)


def target_stats():
    ms, ss = zip(*(background_stats(Image.open(os.path.join(ROOT, "img", t, "terracotta.jpg"))) for t in TOTEMS))
    return np.mean(ms, 0), np.mean(ss, 0)


def tone(im, tgt):
    """Shift and scale each colour so the suede matches the totems' suede; the piece moves with it."""
    m, s = background_stats(im); tm, ts = tgt
    a = np.asarray(im).astype(float) / 255
    k = np.clip(ts / (s + 1e-6), .7, 1.4)
    out = (a - m) * k + tm
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype("uint8"))


def frame(im, box, frac, cy=.51):
    """A 4:5 crop with the piece's centre at the middle (a touch low, as the totems sit), the piece
    filling `frac` of the frame's height, or its width when it is a wide piece."""
    x0, y0, x1, y1 = box; W, H = im.size
    pw, ph = x1 - x0, y1 - y0
    h = max(ph / frac, pw / (frac * 1.6) * 1.25)          # wide pieces: sized by width, as Pip and Zuma are
    h = min(h, H, W * 1.25); w = h * .8
    cx, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    left = min(max(cx - w / 2, 0), W - w); top = min(max(cyp - h * cy, 0), H - h)
    return im.crop((round(left), round(top), round(left + w), round(top + h)))


def find_box(im):
    k = 1000 / im.width; sm = np.asarray(im.resize((1000, round(im.height * k)))).astype(float) / 255
    m = piece_mask(sm); lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1)); big = np.argmax(sizes) + 1
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > m.size * .0003])
    ys, xs = np.nonzero(keep)
    return [v / k for v in (xs.min(), ys.min(), xs.max(), ys.max())]


def place(slug, src, frac=.30, box=None):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im = tone(im, TARGET)
    box = box or find_box(im)
    out = frame(im, box, frac)
    d = os.path.join(ROOT, "img", slug); os.makedirs(d, exist_ok=True)
    out.save(os.path.join(d, "terracotta.jpg"), quality=92)
    big = out.resize((1600, 2000), Image.LANCZOS); big.save(os.path.join(ROOT, "img", "ab-clay", slug + ".webp"), quality=86)
    big.resize((960, 1200), Image.LANCZOS).save(os.path.join(ROOT, "img", "ab-clay", slug + "--tile.webp"), quality=84)
    print(slug, out.size)


TARGET = None
if __name__ == "__main__":
    TARGET = target_stats()
    for slug, src, frac, box in json.load(open(sys.argv[1])):
        place(slug, src, frac, box)
