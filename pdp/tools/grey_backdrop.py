#!/usr/bin/env python3
"""The totems' grey-backdrop photos, made the same way every time.

    python3 pdp/tools/grey_backdrop.py rebi "Rebi White 1.png" "Rebi White 2.png"

Each photo from ~/Downloads/Maçon/WHITE-BG-TOTEMS is cut to 5:4 (the site's frames never show
wider), its backdrop made one flat warm grey (224, 222, 220) with the photo's own grain, the piece
15% smaller in frame (the same grey extended outward), and the light head warmed a touch toward
gold. Saved at full resolution (up to 5000px) as img/<slug>/white-<n>.jpg, with the unwarmed copy
kept in _originals. Then run tools/optimize_media.py and build_pdp.py.
"""
import os, sys
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.expanduser("~/Downloads/Maçon/WHITE-BG-TOTEMS")
TARGET = np.array([224.0, 222.0, 220.0])          # neutral grey, 2% warm (R +1%, B -1%)
ZOOM = 0.85                                      # the piece 15% smaller in frame
MAXL = 5000                                      # Shopify's largest
ASPECT = 1.25
WARMTH = 1.0                                     # "A": a tad warmer (1.8 read too yellow)


def poly_terms(x, y, deg=3):
    return np.stack([x**i * y**j for i in range(deg + 1) for j in range(deg + 1 - i)], -1)


def flatten(f, whole=False, anchor="centre"):
    """whole=True only evens out the lighting (every pixel kept, shadows fading naturally); otherwise
    everything but the piece and its shadow also becomes the one flat grey."""
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, f))).convert("RGB")
    # the site's frames are never wider than 5:4, so the far sides are cut away first and the piece keeps its pixels
    if im.width > ASPECT * im.height:
        w = round(ASPECT * im.height); x = 0 if anchor == "left" else (im.width - w) // 2          # left: something (a chain) runs off that edge and must keep doing so
        im = im.crop((x, 0, x + w, im.height))
    k = MAXL * ZOOM / max(im.size)                   # final long side at most MAXL after padding
    if k < 1: im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape
    # the lighting across the backdrop, fitted on a small copy
    s = 160 / w
    small = np.asarray(im.resize((160, max(1, round(h * s))), Image.BOX)).astype(np.float32)
    sh, sw, _ = small.shape
    yy, xx = np.mgrid[0:sh, 0:sw]
    X = poly_terms(xx / sw, yy / sh).reshape(sh * sw, -1)
    lum = small.mean(2); chroma = small.max(2) - small.min(2)
    mask = (lum > np.percentile(lum, 40) - 15) & (chroma < 25)
    mask = ndimage.binary_erosion(mask, iterations=2)
    for _ in range(4):
        coef = [np.linalg.lstsq(X[mask.ravel()], small[..., c].ravel()[mask.ravel()], rcond=None)[0] for c in range(3)]
        fit = np.stack([X @ cc for cc in coef], -1).reshape(sh, sw, 3)
        resid = np.abs(small - fit).max(2)
        mask = ndimage.binary_erosion((resid < 6) & (chroma < 25), iterations=1)
    Y, Xg = np.mgrid[0:h, 0:w]
    full = np.empty_like(a)
    for c in range(3):
        for y0 in range(0, h, 256):
            full[y0:y0+256, :, c] = poly_terms(Xg[y0:y0+256] / w, Y[y0:y0+256] / h) @ coef[c]
    out = a * (TARGET / full)
    if whole and ZOOM == 1.0:
        return Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8))
    # keep the piece and the shadow it casts; everything else becomes the one flat grey
    bgmask = ndimage.zoom(mask.astype(float), (h / sh, w / sw), order=0)[:h, :w] > 0.5
    hp = out - ndimage.gaussian_filter(out, (3, 3, 0))
    sigma = hp[bgmask].std(0)
    q = 4
    o4 = ndimage.zoom(out, (1 / q, 1 / q, 1), order=1)
    dev = ndimage.gaussian_filter(np.abs(o4 - TARGET).max(2), 1.5)
    fg = dev > 9
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    hh, ww = fg.shape
    keep = np.zeros_like(fg)
    big = sizes.max() if n else 0
    for i in range(n):          # the piece: large, and in the middle of the picture (not a table edge at the border)
        com = ndimage.center_of_mass(fg, lab, i + 1)
        central = 0.12 * hh < com[0] < 0.88 * hh and 0.12 * ww < com[1] < 0.88 * ww
        if central and sizes[i] > 0.05 * big:
            keep |= lab == i + 1
    keep = ndimage.binary_fill_holes(keep)
    keep = ndimage.binary_dilation(keep, iterations=max(2, ww // 60))
    alpha = np.clip(ndimage.gaussian_filter(keep.astype(np.float32), ww / 120), 0, 1)
    alpha = ndimage.zoom(alpha, (h / alpha.shape[0], w / alpha.shape[1]), order=1)[:h, :w, None]
    H, W = round(h / ZOOM), round(w / ZOOM)
    rng = np.random.default_rng(0)
    canvas = TARGET + rng.normal(0, 1, (H, W, 3)) * sigma
    y0, x0 = (H - h) // 2, 0 if anchor == "left" else (W - w) // 2
    canvas[y0:y0+h, x0:x0+w] = alpha * out + (1 - alpha) * canvas[y0:y0+h, x0:x0+w]
    return Image.fromarray(np.clip(canvas, 0, 255).round().astype(np.uint8))


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def head_weight(a):
    """0..1 per pixel: how much of the pale (golden) head this pixel is."""
    L = a.mean(2); warm = a[..., 0] - a[..., 2]; dev = np.abs(a - TARGET).max(2)
    q = 3
    s = lambda x: ndimage.zoom(x, 1 / q, order=1)
    Ls, ws, ds = s(L), s(warm), s(dev)
    piece = ndimage.binary_opening(ds > 12, iterations=2)
    ys, xs = np.where(piece); top, bot = ys.min(), ys.max(); hgt = bot - top
    m = ndimage.binary_opening((ws > 8) & (Ls > 100), iterations=2)
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1)); keep = np.zeros_like(m)
    for i in range(n):
        yy = np.where(lab == i + 1)[0]
        if sizes[i] >= 0.25 * sizes.max() and yy.min() < bot - 0.25 * hgt:          # part of the head, not a warm patch on the floor
            keep |= lab == i + 1
    keep = ndimage.binary_closing(keep, iterations=3)
    keep = ndimage.binary_fill_holes(keep)
    w = ndimage.gaussian_filter(keep.astype(np.float32), 2.5)
    w = ndimage.zoom(w, (a.shape[0] / w.shape[0], a.shape[1] / w.shape[1]), order=1)[:a.shape[0], :a.shape[1]]
    # backdrop pixels lit warm by the head (on the floor, beside the legs) are only faintly warm and flat
    metal = np.maximum(smooth(warm, 12, 22), smooth(L - 222, 6, 18))          # warm, or a highlight brighter than the grey; shadows are neither
    metal = ndimage.gaussian_filter(metal, 5)          # no JPEG-block edges in the highlights
    return np.clip(w, 0, 1) * smooth(L, 70, 150) * metal          # fades through the ombré into the dark body


def warm(a, k):
    """Golden shift: a touch more red and yellow, a little less blue, strength k."""
    gain = np.array([1 + 0.035 * k, 1 + 0.008 * k, 1 - 0.07 * k])
    return np.clip(a * (1 + (gain - 1) * head_weight(a)[..., None]), 0, 255)


if __name__ == "__main__":
    slug, files = sys.argv[1], sys.argv[2:]
    for i, f in enumerate(files, 1):
        flat = flatten(f)
        im = Image.fromarray(warm(np.asarray(flat).astype(float), WARMTH).round().astype(np.uint8))
        base = f"white-{i}"
        for d in ("_originals", "img"): os.makedirs(os.path.join(PDP, d, slug), exist_ok=True)
        flat.save(os.path.join(PDP, "_originals", slug, base + ".flat.jpg"), quality=95, subsampling=0)
        for d in ("_originals", "img"):
            im.save(os.path.join(PDP, d, slug, base + ".jpg"), quality=95, subsampling=0)          # full colour detail
        open(os.path.join(PDP, "_originals", slug, base + ".jpg.studio"), "w").write(
            f"<- {f}: tools/grey_backdrop.py (5:4, flat 224/222/220, 15% smaller, head warmed {WARMTH})\n")
        print(slug, base, im.size)
