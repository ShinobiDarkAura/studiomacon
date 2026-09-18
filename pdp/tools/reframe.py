#!/usr/bin/env python3
"""Reframe a piece's photograph: the object dead centre, the same air around each one.

The piece is found by its difference from the backdrop; the canvas is sized so the
object always fills the same share of the frame; any new area is built from the
picture's own edge pixels, mirrored and softened the way the backdrop already falls
away. Nothing is invented, and the piece itself is never touched.

Only for even sweeps. Hands, tools and busy surfaces are skipped.
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

# The piece's diagonal as a share of the frame's, so a long ear cuff and an upright
# totem are given the same amount of air, which reading height alone does not do.
SHARE = 0.46          # measured from Ren, the frame Alex approved
RATIO = (4, 5)        # portrait frames on the product pages
CANVAS = (2000, 2500) # every framed photograph comes out the same size


def find_piece(im, small=360):
    """Where the piece sits, read as whatever the backdrop's slow shading cannot explain.

    Comparing the picture with a heavily blurred copy of itself ignores vignetting and
    the gradient of a lit sweep, and leaves the carved edges of the piece behind.
    """
    g = im.convert("L").copy()
    w0, h0 = g.size
    g.thumbnail((small, small), Image.LANCZOS)
    w, h = g.size
    blur = g.filter(ImageFilter.GaussianBlur(radius=max(6, w / 9)))
    d = np.abs(np.asarray(g, float) - np.asarray(blur, float))
    thr = max(5.0, np.percentile(d, 99.2) * 0.30)
    m = d > thr
    cs = np.where(m.sum(0) > h * 0.02)[0]
    rs = np.where(m.sum(1) > w * 0.02)[0]
    if not len(cs) or not len(rs):
        return None
    k = w0 / w
    return round(cs[0] * k), round(rs[0] * k), round(cs[-1] * k), round(rs[-1] * k)


def grow(im, x, y, W, H):
    """Place the picture at (x, y) on a W×H canvas, filling the rest from its own edges."""
    w, h = im.size
    out = Image.new("RGB", (W, H))
    out.paste(im, (x, y))

    def band(strip, size, horizontal):
        b = strip.resize(size, Image.LANCZOS)
        b = b.transpose(Image.FLIP_LEFT_RIGHT if horizontal else Image.FLIP_TOP_BOTTOM)
        return b.filter(ImageFilter.GaussianBlur(radius=max(2, (size[0] if horizontal else size[1]) * 0.03)))

    tx, ty = max(8, round(w * 0.10)), max(8, round(h * 0.10))
    if x > 0:
        out.paste(band(im.crop((0, 0, tx, h)), (x, h), True), (0, y))
    if x + w < W:
        out.paste(band(im.crop((w - tx, 0, w, h)), (W - x - w, h), True), (x + w, y))
    mid = out.crop((0, y, W, y + h))
    if y > 0:
        out.paste(band(mid.crop((0, 0, W, ty)), (W, y), False), (0, 0))
    if y + h < H:
        out.paste(band(mid.crop((0, h - ty, W, h)), (W, H - y - h), False), (0, y + h))

    for j in (y, y + h):                       # soften the joins so no line shows
        k = round(h * 0.03)
        if k >= 4 and j - k >= 0 and j + k <= H:
            part = out.crop((0, j - k, W, j + k))
            out.paste(Image.blend(part, part.filter(ImageFilter.GaussianBlur(radius=k * 0.5)), 0.55), (0, j - k))
    return out


def reframe(src, dst=None, share=SHARE, may_grow=True):
    """Lay the photograph onto a common canvas so every piece lands identically.

    The whole photograph is scaled until the piece measures the agreed share of the
    frame, then shifted so the piece's centre is the frame's centre. Its own backdrop
    travels with it, so the light, the shadow and the weave stay the ones that were
    photographed; only the area beyond the photograph's edge is grown from it.
    """
    im = Image.open(src).convert("RGB")
    found = find_piece(im)
    if not found:
        return None
    x0, y0, x1, y1 = found
    ow, oh = x1 - x0, y1 - y0
    if ow < 12 or oh < 12:
        return None

    W, H = CANVAS
    want = share * (W ** 2 + H ** 2) ** 0.5
    have = (ow ** 2 + oh ** 2) ** 0.5
    k = want / have                                   # one scale for the whole photograph

    sw, sh = max(2, round(im.width * k)), max(2, round(im.height * k))
    scaled = im.resize((sw, sh), Image.LANCZOS)
    cx, cy = ((x0 + x1) / 2) * k, ((y0 + y1) / 2) * k

    px, py = round(W / 2 - cx), round(H / 2 - cy)     # the piece's centre becomes the frame's

    def place(px, py):
        cw, ch = max(W, sw + max(px, 0)), max(H, sh + max(py, 0))
        whole = grow(scaled, max(px, 0), max(py, 0), cw, ch)
        ox, oy = max(-px, 0), max(-py, 0)
        return whole.crop((ox, oy, ox + W, oy + H))

    if not may_grow and (px > 0 or py > 0 or px + sw < W or py + sh < H):
        return None          # a hand, a tool or a busy surface: crop it or leave it, never extend it

    out = place(px, py)
    # The piece reads a little differently once it is in its new frame, so the placing
    # is checked against the finished picture and corrected until it sits true.
    for _ in range(3):
        b = find_piece(out)
        if not b:
            break
        ex = W / 2 - (b[0] + b[2]) / 2
        ey = H / 2 - (b[1] + b[3]) / 2
        if abs(ex) <= W * 0.006 and abs(ey) <= H * 0.006:
            break
        px, py = px + round(ex), py + round(ey)
        out = place(px, py)

    out.save(dst or src, quality=92)
    return W, H, share, round(k, 2)


if __name__ == "__main__":
    for f in sys.argv[1:]:
        r = reframe(f)
        print(f"  {os.path.relpath(f):34} {'skipped' if not r else f'{r[0]}x{r[1]}'}")
