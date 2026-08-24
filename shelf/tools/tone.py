#!/usr/bin/env python3
"""Warm and deepen the bright patina on selected pieces.

These bronzes are ombre: a pale gold head over a dark body. The relight tends to
wash the light half toward grey. This lifts saturation and warmth on the brighter
areas only, keyed on luminance, so the dark body is untouched.

Runs after match_colour.py, and is undone by a re-harvest — re-run it then.

    python3 shelf/tools/tone.py
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPR = os.path.join(ROOT, "shelf", "sprites")

# slug: (saturation, red gain, blue gain, luminance knee, brightness)
# Red and blue are separate because tying them together — lifting red while
# dividing blue — warms and darkens at the same time, so brightness could not be
# raised without the warmth pulling it back down.
# Applied in place and cumulative, so re-harvest the piece before re-running.
PIECES = {"ren":  (1.34, 1.16, 0.86, 0.42, 1.00),
          "zuma": (1.28, 1.10, 0.95, 0.15, 1.62)}


def main():
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    for slug, (sat, rg, bg, knee, lift) in PIECES.items():
        path = os.path.join(SPR, f"{pieces[slug]}.png")
        a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
        rgb, al = a[..., :3], a[..., 3:4] / 255.0
        lum = rgb.mean(axis=2, keepdims=True) / 255.0
        # only the lit half, easing in rather than switching on
        w = np.clip((lum - knee) / (1.0 - knee), 0, 1) ** 0.8 * (al > 0.5)
        grey = rgb.mean(axis=2, keepdims=True)
        boosted = grey + (rgb - grey) * sat
        boosted[..., 0] *= rg
        boosted[..., 2] *= bg
        boosted *= lift
        out = np.clip(rgb * (1 - w) + boosted * w, 0, 255)
        before = rgb[(al[..., 0] > .5) & (lum[..., 0] > knee)]
        after = out[(al[..., 0] > .5) & (lum[..., 0] > knee)]
        Image.fromarray(np.dstack([out, a[..., 3]]).astype(np.uint8), "RGBA").save(path)
        print(f"{slug:6} lit area warmth (R-B) {before[:,0].mean()-before[:,2].mean():5.1f}"
              f" -> {after[:,0].mean()-after[:,2].mean():5.1f}")


if __name__ == "__main__":
    main()
