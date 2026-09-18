#!/usr/bin/env python3
"""Write <name>.<ext>.webp siblings for images under pdp/img. Originals untouched."""
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent / "img"
SMALL = {"commissions-cut", "commissions", "inspiration"}

TILE = 900          # the shop grid and the related row show pictures small; they get their own copy


def make_tile(src):
    """A light copy for the grids.

    The grids keep the photograph as it was shot — the framing Alex approved — so the
    tile is cut from the kept original rather than from the reframed product picture.
    """
    keep = ROOT.parent / "_originals" / src.parent.name / src.name
    source = keep if keep.exists() else src
    out = src.with_name(src.stem + "--tile.jpg.webp")
    if out.exists() and out.stat().st_mtime >= source.stat().st_mtime:
        return
    im = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    if max(im.size) > TILE:
        im.thumbnail((TILE, TILE), Image.LANCZOS)
    im.save(out, "WEBP", quality=80, method=6)


def main():
    before, after = defaultdict(int), defaultdict(int)
    for src in sorted(ROOT.rglob("*")):
        if src.suffix.lower() not in (".jpg", ".jpeg", ".png") or not src.is_file():
            continue
        rel = src.relative_to(ROOT)
        top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        if src.stem.endswith("--tile"):
            continue
        if src.stem in ("hero", "plain-3", "plain-1", "plain-2", "hand-1") and len(rel.parts) > 1:
            make_tile(src)
        out = src.with_name(src.name + ".webp")
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            limit = 1000 if top in SMALL else 2400          # retina-sharp on a large display
            im = ImageOps.exif_transpose(Image.open(src))
            im.thumbnail((limit, limit), Image.LANCZOS)
            if src.suffix.lower() == ".png":
                im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") or "transparency" in im.info else im.convert("RGB")
                im.save(out, "WEBP", lossless=False, quality=82, method=6, alpha_quality=90)
            else:
                im.convert("RGB").save(out, "WEBP", quality=80, method=6)
        before[top] += src.stat().st_size
        after[top] += out.stat().st_size
    for k in sorted(before):
        print(f"{k:24} {before[k]/1e6:8.2f} MB -> {after[k]/1e6:7.2f} MB")
    print(f"{'TOTAL':24} {sum(before.values())/1e6:8.2f} MB -> {sum(after.values())/1e6:7.2f} MB")

if __name__ == "__main__":
    main()
