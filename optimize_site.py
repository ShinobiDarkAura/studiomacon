#!/usr/bin/env python3
"""Produce web-sized images in the deploy staging directory.

Originals stay untouched in the repo (they're the archive); only the copy that
ships gets resized/recompressed. Run against _site after staging:

    python3 optimize_site.py _site
"""
import os, sys
from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else "_site"
MAX_W = 1800          # nothing on the site renders wider than ~1180 CSS px (2x for retina)
JPEG_Q = 82

def human(n):
    for u in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}GB"

def has_real_alpha(im):
    """True only if transparency is actually used (not just an alpha channel present)."""
    if im.mode not in ("RGBA", "LA", "P"):
        return False
    if im.mode == "P":
        im = im.convert("RGBA")
    alpha = im.getchannel("A")
    return alpha.getextrema()[0] < 250

def optimize(path):
    before = os.path.getsize(path)
    try:
        im = Image.open(path)
    except Exception:
        return before, before
    fmt = (im.format or "").upper()

    if fmt == "GIF":
        return before, before                     # leave animation alone

    if im.width > MAX_W:
        h = round(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)

    transparent = has_real_alpha(im)

    # Wix served many photographs as PNG (even named .jpg) — hugely wasteful.
    # Anything without real transparency ships as JPEG.
    if transparent:
        im.save(path, "PNG", optimize=True)
    else:
        im.convert("RGB").save(path, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)

    return before, os.path.getsize(path)

def main():
    total_before = total_after = 0
    worst = []
    for base, _, files in os.walk(ROOT):
        for f in files:
            if not f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                continue
            p = os.path.join(base, f)
            b, a = optimize(p)
            total_before += b
            total_after += a
            if a > 400_000:
                worst.append((a, p))
    print(f"images: {human(total_before)} -> {human(total_after)} "
          f"({100 - (total_after / max(total_before, 1)) * 100:.0f}% smaller)")
    for a, p in sorted(worst, reverse=True)[:5]:
        print(f"  still large: {human(a)}  {p}")

if __name__ == "__main__":
    main()
