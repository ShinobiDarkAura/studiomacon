#!/usr/bin/env python3
"""Cut individual label carriers out of the generated grid, shadows included.

Two things make this awkward.

The carriers sit on a ground almost exactly their own colour, so a colour key
alone cannot find a cream card on cream paper — but the segmenter can. The
segmenter, in turn, sometimes returns a ghost with no solid pixels at all for
precisely those pale-on-pale cells, so the colour key covers what it misses.

And the grid was lit, so each carrier already has a real contact shadow. Those
are worth keeping rather than drawing new ones later, so anything on the backdrop
darker than the backdrop — and not already the object — is carried through as
partial alpha.

    python3 shelf/tools/carriers.py
"""
import os, sys
import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut import offline_session, clean_alpha
from rembg import remove

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "shelf/_test/label-carriers.png")
OUT = os.path.join(ROOT, "shelf/carriers")
COLS, ROWS = 6, 5
PAD = 0.06

NAMES = {1: "torn-paper", 3: "washi-tape", 17: "vellum-strip", 19: "graph-slip",
         20: "ledger-strip", 24: "apothecary-oval", 25: "letterpress-card"}


def object_mask(cell, sess):
    """Alpha for the carrier itself, full cell size."""
    cut = remove(cell, session=sess).convert("RGBA")
    a = np.asarray(clean_alpha(cut.getchannel("A")), np.float32) / 255.0
    bb = Image.fromarray((a * 255).astype(np.uint8)).getbbox()
    solid = 0.0
    if bb:
        sub = a[bb[1]:bb[3], bb[0]:bb[2]]
        solid = float((sub > 0.9).mean())
    if solid >= 0.30:
        return a, False

    arr = np.asarray(cell, np.float32)
    k = 6
    corners = np.concatenate([arr[:k, :k].reshape(-1, 3), arr[:k, -k:].reshape(-1, 3),
                              arr[-k:, :k].reshape(-1, 3), arr[-k:, -k:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    m = (np.sqrt(((arr - bg) ** 2).sum(axis=2)) > 10).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    ncomp, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if ncomp > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = (lab == big).astype(np.uint8)
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2), True


def main():
    im = Image.open(SRC).convert("RGB")
    W, H = im.size
    cw, ch = W / COLS, H / ROWS
    sess = offline_session()
    os.makedirs(OUT, exist_ok=True)

    for num, name in NAMES.items():
        r, c = divmod(num - 1, COLS)
        box = (max(0, int((c - PAD) * cw)), max(0, int((r - PAD) * ch)),
               min(W, int((c + 1 + PAD) * cw)), min(H, int((r + 1 + PAD) * ch)))
        cell = im.crop(box)
        arr = np.asarray(cell, np.float32)

        obj, keyed = object_mask(cell, sess)

        k = 6
        corners = np.concatenate([arr[:k, :k].reshape(-1, 3), arr[:k, -k:].reshape(-1, 3),
                                  arr[-k:, :k].reshape(-1, 3), arr[-k:, -k:].reshape(-1, 3)])
        bg = float(np.median(corners))
        shade = np.clip((bg - arr.mean(axis=2)) / 26.0, 0, 1)
        shade[obj > 0.5] = 0.0
        shade = cv2.GaussianBlur(shade, (0, 0), 1.5)
        shade[shade < 0.06] = 0.0

        # Keep this carrier and nothing else. Choosing the component from object
        # plus shadow lets a neighbour ride in wherever the two shadows touch, so
        # the choice is made on the object alone, and shadow is then kept only
        # within reach of it.
        ncomp, lab, stats, _ = cv2.connectedComponentsWithStats((obj > 0.5).astype(np.uint8), 8)
        stray = 0
        if ncomp > 1:
            keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            mine = (lab == keep)
            stray += int(((lab != keep) & (lab != 0)).sum())
            obj = obj * mine
            reach = cv2.dilate(mine.astype(np.uint8),
                               np.ones((3, 3), np.uint8), iterations=26).astype(bool)
            stray += int((shade > 0.05).sum() - ((shade > 0.05) & reach).sum())
            shade = shade * reach

        # A shadow pixel must be DARK, not pale. Carrying the backdrop's own cream
        # into a partially transparent pixel lightens whatever it lands on, which
        # is the white halo: the matte was right but the colour under it was not.
        # Object pixels keep their real colour; shadow pixels become a warm dark
        # whose alpha does the darkening.
        SHADOW_RGB = np.array([58, 48, 38], np.float32)
        alpha = np.clip(np.maximum(obj, shade * 0.9), 0, 1)
        is_obj = (obj > 0.5)[..., None]
        rgb = np.where(is_obj, arr, SHADOW_RGB[None, None, :])
        # feather the handover so the object's own edge does not show a dark rim
        edge = np.clip((obj - 0.15) / 0.5, 0, 1)[..., None]
        rgb = rgb * (1 - edge) + arr * edge
        rgba = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
        out = Image.fromarray(rgba, "RGBA")
        bb = out.getchannel("A").getbbox()
        if bb:
            out = out.crop(bb)
        out.save(os.path.join(OUT, f"{name}.png"))
        note = " keyed" if keyed else ""
        note += f"  dropped {stray}px of neighbour" if stray > 40 else ""
        print(f"{num:>2} {name:18} {out.size}{note}")


if __name__ == "__main__":
    main()
