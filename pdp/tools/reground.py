#!/usr/bin/env python3
"""Recolour the suede ground of the terracotta jewelry photographs (not a regeneration): each suede pixel
keeps its own light and texture, moved to a new colour in Lab; the silver, nearly grey, is left alone."""
import os, sys
import numpy as np
from PIL import Image
from skimage import color

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img")
GROUNDS = {"sage": (60, -9, 13), "moss": (40, -5, 24), "pine": (25, -10, 8)}          # Lab means of each suede
JEWELRY = ["zuma-ring", "eclipse-ring", "sietch-aperture", "lunar-canyon-ring", "ear-cuff", "meridian-egg-ring", "wonderhorn-talisman"]


def reground(im, target):
    a = np.asarray(im.convert("RGB")).astype(float) / 255
    mx, mn = a.max(-1), a.min(-1); s = (mx - mn) / (mx + 1e-6); warm = a[..., 0] - a[..., 2]
    w = np.clip((s - .22) / .18, 0, 1) * np.clip((warm - .06) / .12, 0, 1)          # how much of a pixel is suede
    lab = color.rgb2lab(a); bg = w > .9
    m = lab[bg].mean(0); sd = lab[bg].std(0)
    t = np.array(target, float)
    new = lab.copy()
    new[..., 0] = (lab[..., 0] - m[0]) * (1 + (t[0] - m[0]) / 200) + t[0]          # lighter or darker ground, texture kept
    new[..., 1] = (lab[..., 1] - m[1]) * .5 + t[1]          # the orange's own swing, halved: greens are quieter
    new[..., 2] = (lab[..., 2] - m[2]) * .5 + t[2]
    out = lab * (1 - w[..., None]) + new * w[..., None]
    return Image.fromarray((np.clip(color.lab2rgb(out), 0, 1) * 255 + .5).astype("uint8"))


if __name__ == "__main__":
    for g, t in GROUNDS.items():
        d = os.path.join(ROOT, "ab-clay-grounds", g); os.makedirs(d, exist_ok=True)
        for slug in JEWELRY:
            im = reground(Image.open(os.path.join(ROOT, "ab-clay", slug + ".webp")), t)
            im.save(os.path.join(d, slug + ".webp"), quality=86)
            im.resize((960, 1200), Image.LANCZOS).save(os.path.join(d, slug + "--tile.webp"), quality=84)
        print(g)
