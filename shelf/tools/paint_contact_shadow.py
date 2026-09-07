#!/usr/bin/env python3
"""Paint a contact shadow into one cutout's transmission map.

Only for photographs where the measurement genuinely failed. The background
estimate in cut_photos.py removes dark things NARROWER than its kernel; a large
dark subject - a stone - survives into the estimate of the bare paper, so C/L
comes back at 1 underneath it and the piece lands with no shadow at all.

What is painted here is invented, not measured, so it stays opt-in and per file.
The shape is the piece's own silhouette flattened onto the ground plane and
pushed away from the light, which is what a soft overhead source actually casts,
then blurred with distance from the contact line.

    python3 shelf/tools/paint_contact_shadow.py NAME [--dx -0.06] [--squash 0.26]
                                                     [--strength 0.55] [--blur 0.02]
"""
import argparse, os
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHOTOS = os.path.join(ROOT, "shelf/photos")


def contact(alpha, dx, squash, blur, strength):
    h, w = alpha.shape
    a = alpha.astype(np.float32) / 255.0
    ys = np.nonzero((a > 0.5).any(axis=1))[0]
    base = float(ys.max())

    # Flatten the silhouette onto the ground: everything above the contact line
    # collapses toward it, which is the projection a high, soft light makes.
    M = np.float32([[1, 0, dx * w], [0, squash, base * (1 - squash)]])
    ground = cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    ground[: int(base * 0.2), :] = 0

    # A contact shadow is sharp where the object meets the ground and loosens
    # with distance, so blur twice and cross-fade by height above the line.
    s = max(2.0, blur * w)
    tight = cv2.GaussianBlur(ground, (0, 0), s * 0.4)
    loose = cv2.GaussianBlur(ground, (0, 0), s * 2.2)
    yy = np.arange(h, dtype=np.float32)[:, None]
    near = np.clip(1.0 - np.abs(yy - base) / (s * 6.0), 0, 1)
    return np.clip((tight * near + loose * (1 - near)) * strength, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--dx", type=float, default=-0.06)
    ap.add_argument("--squash", type=float, default=0.26)
    ap.add_argument("--blur", type=float, default=0.02)
    ap.add_argument("--strength", type=float, default=0.55)
    ap.add_argument("--out")
    a = ap.parse_args()

    obj = os.path.join(PHOTOS, "object", a.name)
    shd = os.path.join(PHOTOS, "shadow", a.name)
    alpha = np.asarray(Image.open(obj).convert("RGBA"))[..., 3]
    T = np.asarray(Image.open(shd).convert("RGB")).astype(np.float32) / 255.0

    d = contact(alpha, a.dx, a.squash, a.blur, a.strength)
    # Multiply, never replace: whatever shadow WAS measured stays, and the paint
    # can only darken. The object covers its own footprint, so no mask is needed.
    out = np.clip(T * (1.0 - d[..., None]), 0, 1)
    Image.fromarray((out * 255).astype(np.uint8)).save(a.out or shd)
    print(f"  {a.name}  painted, max depth {d.max():.2f}")


if __name__ == "__main__":
    main()
