"""The newsletter maker (newsletter.html): a private page for writing the monthly email.

Called from build_pdp.py. It fills the maker with the shop's pieces (name, price, kind) and makes sure each
piece has its two email photographs in img/email (tile-<slug>.jpg, 4:5, and held-<slug>.jpg, 3:2), cutting
any that are missing from the piece's own photos. Existing email photos are never touched.
"""
import json, os
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))


def _cut(pdp, src, dst, w, ratio):
    im = ImageOps.exif_transpose(Image.open(os.path.join(pdp, src))).convert("RGB")
    im = ImageOps.fit(im, (w, round(w / ratio)), Image.LANCZOS)
    im.save(os.path.join(pdp, "img", "email", dst), quality=82, optimize=True, progressive=True)


def _first(pdp, *paths):
    return next((p for p in paths if p and os.path.exists(os.path.join(pdp, p))), None)


def build(pdp, pieces, content):
    """pieces: the shop's running order, each {slug, name, price, kind}."""
    for p in pieces:
        s, c = p["slug"], content.get(p["slug"]) or {}
        if not os.path.exists(os.path.join(pdp, "img", "email", f"tile-{s}.jpg")):
            src = _first(pdp, c.get("tile_image"), f"img/{s}/terracotta.jpg", f"img/{s}/hero.jpg")
            if src: _cut(pdp, src, f"tile-{s}.jpg", 520, 4 / 5)
        if not os.path.exists(os.path.join(pdp, "img", "email", f"held-{s}.jpg")):
            src = _first(pdp, c.get("tile_hover"), f"img/{s}/hand-2.jpg", f"img/{s}/hand-1.jpg", f"img/{s}/plain-1.jpg")
            if src: _cut(pdp, src, f"held-{s}.jpg", 960, 3 / 2)
    page = open(os.path.join(HERE, "maker.html"), encoding="utf-8").read()
    page = page.replace("/*PIECES*/[]", json.dumps(pieces, ensure_ascii=False))
    with open(os.path.join(pdp, "newsletter.html"), "w", encoding="utf-8") as f:
        f.write(page)
