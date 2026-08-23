#!/usr/bin/env python3
"""Pull each sprite's colour back to its real photograph.

The relight warms everything slightly. On bronze that is invisible — a couple of
points — but sterling silver comes back up to twenty points warmer, reading as
brass rather than silver, and the silhouette score cannot see it because shape is
unchanged. So colour is corrected separately, per channel, against the real
photograph the piece was cut from.

Gains apply only to the object, feathered by its own mask so no seam appears at
the edge, and are clamped so a bad measurement can never recolour a piece wildly.

    python3 shelf/tools/match_colour.py
"""
import json, os
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLAMP = (0.80, 1.25)


def mean_rgb(rgba, amin=200):
    m = rgba[..., 3] > amin
    return rgba[..., :3][m].astype(float).mean(0) if m.any() else None


def main():
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    excl = set(pieces.get("_shelf_exclude", {}))
    for slug in [k for k in pieces if not k.startswith("_") and k not in excl]:
        piece = pieces[slug]
        sp_path = os.path.join(ROOT, "shelf/sprites", f"{piece}.png")
        real = np.asarray(Image.open(os.path.join(ROOT, "shelf/cutouts", f"obj-{piece}.png")).convert("RGBA"))
        sp = np.asarray(Image.open(sp_path).convert("RGBA")).astype(float)

        want, have = mean_rgb(real), mean_rgb(sp.astype(np.uint8))
        if want is None or have is None:
            continue
        gain = np.clip(want / np.maximum(have, 1e-3), *CLAMP)

        # Feather the object mask so the correction fades out rather than
        # stopping dead at the alpha edge and leaving a visible outline.
        m = (sp[..., 3] > 200).astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 2.0)[..., None]

        sp[..., :3] = np.clip(sp[..., :3] * (1 + m * (gain - 1)), 0, 255)
        Image.fromarray(sp.astype(np.uint8), "RGBA").save(sp_path)
        after = mean_rgb(sp.astype(np.uint8))
        print(f"{slug:22} gain {gain.round(3)}  warmth {have[0]-have[2]:5.1f} -> {after[0]-after[2]:5.1f}  (real {want[0]-want[2]:5.1f})")


if __name__ == "__main__":
    main()
