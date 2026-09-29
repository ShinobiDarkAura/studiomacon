#!/usr/bin/env python3
"""The jewelry on moss suede. Real moss photographs where the shoot has one (framed as the terracotta ones);
the rest recoloured from terracotta, suede and silver both matched to those real photographs."""
import os, sys
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage
from skimage import color
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import place_terracotta as P

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img")
OUT = os.path.join(IMG, "ab-clay-grounds", "moss")
SHOOT = os.path.expanduser("~/Downloads/Teracotta photoshoot/Jewelry/")
SUEDE = np.array([42.6, 4.1, 31.9])          # the real moss suede, Lab, averaged over its three photographs
SILVER_MEAN = np.array([72.7, -1.2, 7.5])   # the silver in those three, Lab
SILVER_SD = np.array([15.7, 1.2, 2.8])
REAL = {          # only the Wonder Horn still comes from here; the rest are Hannah's edits
        "wonderhorn-talisman": ("Ida Horn Moss Suede.jpg", .1955, 450, 0)}          # file, size in frame, chain cut-off, nudge
LIFT = {"ear-cuff": 85, "eclipse-ring": 70}          # moss shots taken a touch lower than the terracotta ones: their pieces raised onto the centre, px
RECOLOUR = []          # 2026-09-29: Hannah's own moss edits (~/Downloads/MOSSY AF) replaced these; never regenerate over them          # lunar-canyon-ring: its own photograph, as shot (see AS_SHOT in place_terracotta.py)


def save(slug, im):
    """Full size as the product page's first picture, and the grid's two sizes (terracotta kept as terracotta-orange.jpg)."""
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(IMG, slug, "terracotta.jpg"), quality=92)
    big = im.resize((1600, 2000), Image.LANCZOS); big.save(os.path.join(OUT, slug + ".webp"), quality=86)
    big.resize((960, 1200), Image.LANCZOS).save(os.path.join(OUT, slug + "--tile.webp"), quality=84)


def lab_of(im):
    return color.rgb2lab(np.asarray(im.convert("RGB")).astype(float) / 255)


def to_img(lab):
    return Image.fromarray((np.clip(color.lab2rgb(lab), 0, 1) * 255 + .5).astype("uint8"))


def suede_weight(a, lo=.30, hi=.45):
    mx, mn = a.max(-1), a.min(-1); s = (mx - mn) / (mx + 1e-6)
    return np.clip((s - lo) / (hi - lo), 0, 1)


TERRA = {"ear-cuff": "Caldera Terracotta Suede.jpg", "eclipse-ring": "Eclipse Ring Terracotta Suede.jpg",
         "wonderhorn-talisman": "Ida Horn Terracotta Suede.jpg"}
PENDANT_BOX = [2452, 2354, 3275, 2904]          # the Wonder Horn's pendant, without its chain


def real(slug, name, frac, cut, dx):
    """Shot from the same spot as the terracotta photograph, so it takes that photograph's framing exactly."""
    im = ImageOps.exif_transpose(Image.open(SHOOT + name)).convert("RGB")
    if slug == "wonderhorn-talisman":
        box = PENDANT_BOX
    else:
        t = ImageOps.exif_transpose(Image.open(SHOOT + TERRA[slug])).convert("RGB")
        box = P.find_box(t)
    dy = LIFT.get(slug, 0); box = [box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy]
    if P.PAD.get(slug): im = P.pad_bottom(im, P.PAD[slug])
    out = P.frame(im, box, frac, cy=.5)          # every piece on the frame's vertical centre
    lab = lab_of(out); w = suede_weight(np.asarray(out).astype(float) / 255)[..., None]
    shift = SUEDE - lab[w[..., 0] > .9].mean(0)          # nudge this photo's suede onto the three's average
    save(slug, to_img(lab + shift * w))


def recolour(slug):
    im = Image.open(os.path.join(IMG, slug, "terracotta-orange.jpg")).convert("RGB"); a = np.asarray(im).astype(float) / 255          # full size
    warm = np.clip(((a[..., 0] - a[..., 2]) - .06) / .10, 0, 1)          # suede in the terracotta shot is always orange: a cool blue or green pixel is the silver
    lab = lab_of(im)
    warm = np.maximum(warm, np.clip((32 - lab[..., 0]) / 8, 0, 1))          # shadows on the suede are dark, not orange: still suede, never silver
    w = (suede_weight(a) * warm)[..., None]
    bg = lab[w[..., 0] > .95]; m = bg.mean(0)
    new = lab.copy()
    new[..., 0] = (lab[..., 0] - m[0]) * .95 + SUEDE[0]          # the suede's own light and grain, moved to moss
    new[..., 1:] = (lab[..., 1:] - m[1:]) * .35 + SUEDE[1:]
    # the silver matched to how it reads in the three real moss photographs (Caldera, Eclipse, Wonder Horn):
    # a touch darker and warmer than it is against terracotta, with the same spread of light
    sil = (w[..., 0] < .1) & (lab[..., 0] > 20); m_s, s_s = lab[sil].mean(0), lab[sil].std(0)
    k = np.clip(SILVER_SD / (s_s + 1e-6), .6, 1.2); k[1:] = .15          # colour swing pulled in hard: reflected greens and blues go, the silver reads neutral-warm
    silver = lab.copy(); silver = (lab - m_s) * k + SILVER_MEAN
    silver = lab + (silver - lab) * (1 - w)          # only where it isn't suede
    out = silver * (1 - w) + new * w
    save(slug, to_img(out))


if __name__ == "__main__":
    for slug, a in REAL.items(): real(slug, *a); print("real", slug)
    for slug in RECOLOUR: recolour(slug); print("recoloured", slug)
