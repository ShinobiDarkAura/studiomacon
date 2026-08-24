#!/usr/bin/env python3
"""Pull a plate's tone onto the tone of the plates it sits beside.

Matching whole-image means is wrong here: the closing bays carry far more empty
plaster than the busy upper plates, so their averages differ for reasons of
content rather than colour, and matching them over-darkens. The plaster wall is
the one surface every plate shares, so the gains are measured there and then
applied to the whole frame.

    python3 shelf/tools/plate_tone.py TARGET REF [REF ...]
"""
import sys
import numpy as np
from PIL import Image

# A patch of bare wall well above the shelf, centred to dodge props.
WALL = (0.42, 0.58, 0.05, 0.28)
CLAMP = (0.85, 1.15)   # a mismeasurement must not be able to recolour a plate


def wall_mean(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    H, W, _ = a.shape
    x0, x1, y0, y1 = WALL
    return a[int(H * y0):int(H * y1), int(W * x0):int(W * x1)].reshape(-1, 3).mean(0)


def main():
    target, refs = sys.argv[1], sys.argv[2:]
    want = np.mean([wall_mean(r) for r in refs], axis=0)
    have = wall_mean(target)
    gain = np.clip(want / have, *CLAMP)
    print("  wall now", have.round(1), "-> want", want.round(1), " gain", gain.round(4))
    a = np.asarray(Image.open(target).convert("RGB")).astype(float)
    Image.fromarray(np.clip(a * gain, 0, 255).astype(np.uint8)).save(target)
    print("  wall after", wall_mean(target).round(1))


if __name__ == "__main__":
    main()
