#!/usr/bin/env python3
"""Open up the enclosed backdrop a segmenter leaves inside a pierced piece.

A ring photographed face-on comes back with its aperture filled: the segmenter
carries the paper seen through the hole along with the object, at partial alpha,
so the ring reads as glazed rather than open.

Colour alone cannot find it - polished silver mirrors the same white paper the
hole shows. Three things together can, and all three are needed:

  partial alpha    the hole is never fully opaque; solid metal is
  flat             paper has almost no local variation, metal has specular
                   structure everywhere
  enclosed         it is surrounded by the piece, never touching the canvas edge

Measured on the Lunar Canyon ring: the aperture sits at alpha 192, local
variation 1.7, against 5.3 at the metal's own first quartile.

    python3 shelf/tools/punch_holes.py DIR [--apply] [--only NAME]
"""
import argparse, os
import numpy as np
import cv2
from PIL import Image

FLAT = 3.5          # local standard deviation below which a region is paper
A_LO, A_HI = 20, 248
MIN_FRAC = 0.004    # of the canvas, so a stray speck is never punched


def find_holes(rgba):
    a = rgba.astype(np.float32)
    al = a[..., 3]
    h, w = al.shape
    g = cv2.cvtColor(a[..., :3].astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean = cv2.blur(g, (15, 15))
    sd = np.sqrt(np.maximum(cv2.blur(g * g, (15, 15)) - mean * mean, 0))

    cand = (al > A_LO) & (al < A_HI) & (sd < FLAT)
    cand = cv2.morphologyEx(cand.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cand, 8)
    hole = np.zeros((h, w), bool)
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        if area < MIN_FRAC * h * w:
            continue
        if x <= 1 or y <= 1 or x + ww >= w - 1 or y + hh >= h - 1:
            continue                      # reaches the edge, so it is outside air
        hole |= (lab == i)
    return hole


def punch(path, apply_it):
    im = Image.open(path).convert("RGBA")
    rgba = np.asarray(im)
    hole = find_holes(rgba)
    if not hole.any():
        return 0
    a = rgba.astype(np.float32)
    soft = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 1.2)
    a[..., 3] = np.clip(a[..., 3] * (1.0 - soft), 0, 255)
    if apply_it:
        Image.fromarray(a.astype(np.uint8)).save(path)
    return int(hole.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir"); ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    files = sorted(f for f in os.listdir(a.dir) if f.endswith(".png"))
    if a.only:
        files = [f for f in files if a.only in f]
    hit = 0
    for f in files:
        n = punch(os.path.join(a.dir, f), a.apply)
        if n:
            hit += 1
            print(f"  {f:44} {n:6d} px opened")
    print(f"\n{hit} of {len(files)} had an enclosed backdrop"
          f"{'' if a.apply else '  (dry run, nothing written)'}")


if __name__ == "__main__":
    main()
