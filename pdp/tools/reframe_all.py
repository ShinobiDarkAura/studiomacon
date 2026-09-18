#!/usr/bin/env python3
"""Reframe every plain sweep on the product pages, and say which ones it could not.

Hands, tools, composites and drawings are left alone: their backdrops have
structure, and extending them would invent things that were never photographed.
"""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reframe import reframe, find_piece
from PIL import Image

IMG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img")
BACKUP = os.path.join(os.path.dirname(IMG), "_originals")
PLAIN = ("hero", "plain-1", "plain-2", "plain-3", "plain-4")
SKIP_FOLDERS = {"inspiration", "commissions", "commissions-cut", "logo-letters"}


def main(dry=False):
    done, skipped = [], []
    for slug in sorted(os.listdir(IMG)):
        folder = os.path.join(IMG, slug)
        if not os.path.isdir(folder) or slug in SKIP_FOLDERS:
            continue
        for name in PLAIN:
            src = os.path.join(folder, name + ".jpg")
            if not os.path.exists(src):
                continue
            keep = os.path.join(BACKUP, slug)
            os.makedirs(keep, exist_ok=True)
            kept = os.path.join(keep, name + ".jpg")
            if not os.path.exists(kept):
                shutil.copy2(src, kept)          # the untouched photograph, kept for good
            if dry:
                im = Image.open(kept)
                box = find_piece(im)
                w, h = im.size
                if not box or (box[2] - box[0]) > w * 0.92 or (box[3] - box[1]) > h * 0.92:
                    skipped.append(f"{slug}/{name}")
                else:
                    done.append(f"{slug}/{name}")
                continue
            r = reframe(kept, src)               # always reframe from the kept original
            (done if r else skipped).append(f"{slug}/{name}")
    print(f"reframed {len(done)}")
    print(f"left alone {len(skipped)}:")
    for s in skipped:
        print("   ", s)
    return done, skipped


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
