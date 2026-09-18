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
MAX_W = 2400


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


def reframe(src, dst=None, share=SHARE):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    found = find_piece(im)
    if not found:
        return None
    x0, y0, x1, y1 = found
    ow, oh = x1 - x0, y1 - y0
    if ow > w * 0.85 or oh > h * 0.85:         # framed too close: there is no backdrop to draw on
        return None
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    diag = (ow ** 2 + oh ** 2) ** 0.5
    frame_diag = diag / share
    unit = (RATIO[0] ** 2 + RATIO[1] ** 2) ** 0.5
    W = round(frame_diag * RATIO[0] / unit)
    H = round(frame_diag * RATIO[1] / unit)
    # A piece that sits small in its photograph is cropped in to, so it carries the same
    # weight as the others. The untouched original is kept either way.

    px, py = round(W / 2 - cx), round(H / 2 - cy)      # the piece lands dead centre
    cw, ch = max(W, w + max(px, 0)), max(H, h + max(py, 0))
    out = grow(im, max(px, 0), max(py, 0), cw, ch)
    ox, oy = max(-px, 0), max(-py, 0)
    out = out.crop((ox, oy, ox + W, oy + H))

    share = diag / ((W ** 2 + H ** 2) ** 0.5)          # what the piece actually ended up filling
    if out.width < 1800 and out.width * 1.6 >= 1800:   # a close crop of a large original can carry a little enlargement
        out = out.resize((1800, round(out.height * 1800 / out.width)), Image.LANCZOS)
    if out.width > MAX_W:
        out = out.resize((MAX_W, round(out.height * MAX_W / out.width)), Image.LANCZOS)
    out.save(dst or src, quality=92)
    return out.size + (share,)


if __name__ == "__main__":
    for f in sys.argv[1:]:
        r = reframe(f)
        print(f"  {os.path.relpath(f):34} {'skipped' if not r else f'{r[0]}x{r[1]}'}")
