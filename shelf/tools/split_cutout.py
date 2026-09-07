#!/usr/bin/env python3
"""Separate a multi-piece cutout into one cutout per object.

A frame holding a ring, a stone and a bronze bird is one cutout, so it can only
be moved as a unit. Splitting it needs the shadow divided too, and a shadow does
not belong to whoever is nearest in the image — it belongs to whatever cast it.

Each shadow pixel is assigned to the nearest object by distance transform, which
for a low raking light is the same thing: a shadow lies against the foot of the
object that made it and falls away from it. Where two objects touch, their
shadows merge and the split runs down the middle, which is the best that can be
done without knowing the light's height.

Anything resting on something else — a ring on a stone — stays one component,
because the segmenter never separated them, and that is usually what is wanted.

    python3 shelf/tools/split_cutout.py CUTOUT_DIR NAME [--out DIR] [--min 0.01]
"""
import argparse, json, os
import numpy as np
import cv2
from PIL import Image


def split(cut_dir, name, out_dir, min_frac):
    obj = np.asarray(Image.open(os.path.join(cut_dir, "object", name)).convert("RGBA"))
    shd = np.asarray(Image.open(os.path.join(cut_dir, "shadow", name)).convert("RGB"))
    al = obj[..., 3]
    h, w = al.shape

    solid = (al > 128).astype(np.uint8)
    solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid, 8)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= min_frac * h * w]
    if len(keep) < 2:
        print(f"  {name}: one object only, nothing to split")
        return []

    # nearest object wins the shadow: for a low light, a shadow lies against the
    # foot of whatever cast it
    seeds = np.zeros((h, w), np.int32)
    for k, i in enumerate(keep, start=1):
        seeds[lab == i] = k
    _, nearest = cv2.distanceTransformWithLabels(
        (seeds == 0).astype(np.uint8), cv2.DIST_L2, 3,
        labelType=cv2.DIST_LABEL_PIXEL)
    flat = seeds.flatten()
    idx = np.flatnonzero(flat)
    lut = np.zeros(nearest.max() + 1, np.int32)
    lut[nearest.flatten()[idx]] = flat[idx]
    owner = np.where(seeds > 0, seeds, lut[nearest])

    os.makedirs(os.path.join(out_dir, "object"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "shadow"), exist_ok=True)
    stem = os.path.splitext(name)[0]
    made = []
    for k, i in enumerate(keep, start=1):
        mine = (owner == k)
        a = al * (lab == i)
        s = np.where(mine[..., None], shd, 255).astype(np.uint8)
        has = (a > 8) | (s.min(axis=2) < 250)
        box = cv2.boundingRect(has.astype(np.uint8))
        x, y, ww, hh = box
        sl = (slice(y, y + hh), slice(x, x + ww))
        piece = f"{stem}--{k}.png"
        Image.fromarray(np.dstack([obj[..., :3], a])[sl]).save(
            os.path.join(out_dir, "object", piece))
        Image.fromarray(s[sl]).save(os.path.join(out_dir, "shadow", piece))
        oy, ox = np.nonzero(a[sl] > 128)
        made.append({"object": f"object/{piece}", "shadow": f"shadow/{piece}",
                     "source": stem, "canvas": [ww, hh],
                     "object_box": [int(ox.min()), int(oy.min()), int(ox.max()), int(oy.max())],
                     "base": [int((ox.min() + ox.max()) / 2), int(oy.max())]})
        print(f"  {piece}  {ww}x{hh}")
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cut_dir"); ap.add_argument("names", nargs="+")
    ap.add_argument("--out"); ap.add_argument("--min", type=float, default=0.01)
    a = ap.parse_args()
    out = a.out or os.path.join(a.cut_dir, "split")
    all_made = []
    for nm in a.names:
        all_made += split(a.cut_dir, nm, out, a.min)
    if all_made:
        p = os.path.join(out, "manifest.json")
        old = json.load(open(p)) if os.path.exists(p) else []
        keep = {e["object"]: e for e in old}
        keep.update({e["object"]: e for e in all_made})
        json.dump(list(keep.values()), open(p, "w"), indent=1)
        print(f"\n{len(all_made)} pieces written to {out}")


if __name__ == "__main__":
    main()
