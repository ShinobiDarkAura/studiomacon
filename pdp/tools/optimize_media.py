#!/usr/bin/env python3
"""Write <name>.<ext>.webp siblings for images under pdp/img. Originals untouched."""
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent / "img"
SMALL = {"commissions-cut", "commissions", "inspiration"}

PIECES = {d.name for d in ROOT.iterdir() if d.is_dir() and (ROOT.parent / "_originals" / d.name).is_dir()}          # folders of piece photographs
import io
import numpy as np
from skimage.metrics import structural_similarity

TARGET = 0.995          # the lightest webp whose picture is indistinguishable from the original at that size


def save_clean(im, out, floor=80):
    """Save the lightest webp that still measures as the same picture as its source."""
    if out.name.startswith("white-"):          # mostly plain grey backdrop: the whole-picture score passes while the small piece smears
        floor = 93
    ref = np.asarray(im.convert("L"), dtype=float)
    for q in sorted(q for q in {floor, 84, 88, 91, 93, 95, 97} if q >= floor):
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=q, method=6)
        got = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("L"), dtype=float)
        if structural_similarity(ref, got, data_range=255) >= TARGET:
            break
    out.write_bytes(buf.getvalue())


TILE = 1800          # the shop grid and the related row show pictures small; they get their own copy


def make_tile(src):
    """A light copy for the grids.

    The grids show the same picture as the product page, expanded framing and all, so
    the tile is cut from the picture the site actually serves.
    """
    source = src
    out = src.with_name(src.stem + "--tile.jpg.webp")
    if out.exists() and out.stat().st_mtime >= source.stat().st_mtime:
        return
    im = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    if max(im.size) > TILE:
        im.thumbnail((TILE, TILE), Image.LANCZOS)
    save_clean(im, out)


PHONE = 1200          # a phone at 3x fills at most ~1200 px, so phones get this lighter copy (see srcset in build_pdp.save)


def make_phone(src):
    """A phone-sized copy of a large photograph, <name>--m.<ext>.webp, used through srcset."""
    out = src.with_name(src.stem + "--m" + src.suffix + ".webp")
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return
    im = ImageOps.exif_transpose(Image.open(src))
    if im.width <= PHONE * 1.15:          # already small: no second copy
        return
    im = im.convert("RGB")
    im.thumbnail((PHONE, PHONE * 3), Image.LANCZOS)
    save_clean(im, out)


def main():
    before, after = defaultdict(int), defaultdict(int)
    for src in sorted(ROOT.rglob("*")):
        if src.suffix.lower() not in (".jpg", ".jpeg", ".png") or not src.is_file():
            continue
        rel = src.relative_to(ROOT)
        top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        if src.stem.endswith("--tile") or src.stem.endswith("--m"):
            continue
        if src.suffix.lower() in (".jpg", ".jpeg") and top not in SMALL:
            make_phone(src)
        if len(rel.parts) > 1 and rel.parts[0] in PIECES:          # any photograph of a piece may be chosen for the grids
            make_tile(src)
        out = src.with_name(src.name + ".webp")
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            limit = 1000 if top in SMALL else 3200          # retina-sharp on a large display
            im = ImageOps.exif_transpose(Image.open(src))
            im.thumbnail((limit, limit), Image.LANCZOS)
            if src.suffix.lower() == ".png":
                im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") or "transparency" in im.info else im.convert("RGB")
                im.save(out, "WEBP", lossless=False, quality=82, method=6, alpha_quality=90)
            else:
                save_clean(im.convert("RGB"), out)          # product photos: as light as they can be without losing anything
        before[top] += src.stat().st_size
        after[top] += out.stat().st_size
    for k in sorted(before):
        print(f"{k:24} {before[k]/1e6:8.2f} MB -> {after[k]/1e6:7.2f} MB")
    print(f"{'TOTAL':24} {sum(before.values())/1e6:8.2f} MB -> {sum(after.values())/1e6:7.2f} MB")

if __name__ == "__main__":
    main()
