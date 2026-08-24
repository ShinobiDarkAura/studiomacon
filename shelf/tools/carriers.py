#!/usr/bin/env python3
"""Cut individual label carriers out of the generated grid.

The grid is 6x5; items are numbered in reading order. Each cell is cropped with
padding and segmented, because the carriers sit on a ground almost exactly their
own colour — a colour key cannot separate cream paper from a cream backdrop, but
the segmenter can.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut import offline_session, clean_alpha
from rembg import remove
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "shelf/_test/label-carriers.png")
OUT = os.path.join(ROOT, "shelf/carriers")
COLS, ROWS = 6, 5

NAMES = {1: "torn-paper", 3: "washi-tape", 17: "vellum-strip", 19: "graph-slip",
         20: "ledger-strip", 24: "apothecary-oval", 25: "letterpress-card"}


def main():
    im = Image.open(SRC).convert("RGB")
    W, H = im.size
    cw, ch = W / COLS, H / ROWS
    sess = offline_session()
    os.makedirs(OUT, exist_ok=True)
    for n, name in NAMES.items():
        r, c = divmod(n - 1, COLS)
        pad = 0.06
        box = (int((c - pad) * cw), int((r - pad) * ch),
               int((c + 1 + pad) * cw), int((r + 1 + pad) * ch))
        box = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
        cell = im.crop(box)
        cut = remove(cell, session=sess).convert("RGBA")
        cut.putalpha(clean_alpha(cut.getchannel("A")))

        # A pale card on a pale ground can defeat the segmenter outright — it
        # returns a ghost with no solid pixels at all. The grid's backdrop is
        # genuinely uniform, though, so a colour key works where segmentation
        # does not, and the two together cover both cases.
        import numpy as np
        al = np.asarray(cut.getchannel("A"), float) / 255.0
        bb0 = cut.getchannel("A").getbbox()
        # Coverage has to be judged against the item's own box, not the padded
        # cell — a thin strip of tape fills very little of its cell even when the
        # cut is perfect, and measuring the cell fires the fallback on everything.
        solid = 0.0
        if bb0:
            sub = al[bb0[1]:bb0[3], bb0[0]:bb0[2]]
            solid = float((sub > 0.9).mean())
        if solid < 0.30:
            arr = np.asarray(cell, float)
            k = 6
            corners = np.concatenate([arr[:k, :k].reshape(-1, 3), arr[:k, -k:].reshape(-1, 3),
                                      arr[-k:, :k].reshape(-1, 3), arr[-k:, -k:].reshape(-1, 3)])
            bg = np.median(corners, axis=0)
            dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
            m = (dist > 10).astype(np.uint8) * 255
            import cv2
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            ncomp, lab, stats, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), 8)
            if ncomp > 1:
                big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
                m = ((lab == big) * 255).astype(np.uint8)
            m = cv2.GaussianBlur(m, (0, 0), 1.2)
            cut = cell.convert("RGBA")
            cut.putalpha(Image.fromarray(m))
            print(f"   {name}: segmenter found nothing, keyed on the backdrop instead")
        bb = cut.getchannel("A").getbbox()
        if bb:
            cut = cut.crop(bb)
        cut.save(os.path.join(OUT, f"{name}.png"))
        print(f"{n:>2} {name:18} {cut.size}")


if __name__ == "__main__":
    main()
