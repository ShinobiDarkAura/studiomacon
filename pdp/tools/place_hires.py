#!/usr/bin/env python3
"""Place the studio's edited hi-res photographs (2026-09-18) into the site.

Each photo that is an edit of a picture already on the site replaces that picture, cropped to
full-height portrait (4:5) around the same centre. Photos that match nothing on the site (new
shots, or matches too weak to trust) get the same crop and join the end of that piece's gallery.
The builder never re-exports over a placed photo (a ".studio" marker sits beside it).
Reads /tmp/place_hires.json (from the matcher). The pictures it replaces are in pdp/_before_hires/.
"""
import json, os, urllib.request
from PIL import Image, ImageOps
Image.MAX_IMAGE_PIXELS = 200_000_000
PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.expanduser("~/Downloads/Maçon/HI RES Product Photos, Edited")
MAXH = 3600                                                       # tall enough for any screen, kept light

P = json.load(open("/tmp/place_hires.json"))
# strong matches take their slot; if two claim one, the stronger keeps it
claims = {}
for p in P:
    if p.get("slot") and p["inliers"] >= 30:
        k = (p["slug"], p["slot"])
        if k not in claims or p["inliers"] > claims[k]["inliers"]:
            claims[k] = p
placed = {id(v) for v in claims.values()}

def whole(p):
    """The photograph whole, only made lighter: every frame on the site crops to its own shape
    (portrait tiles, squarer desktop product frames), so pre-cropping would only throw picture away."""
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, p["file"]))).convert("RGB")
    if max(im.size) > MAXH:
        k = MAXH / max(im.size); im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    return im

def crop45(p):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, p["file"]))).convert("RGB")
    W, H = im.size
    cx = p.get("cx") if id(p) in placed else None
    cx = W / 2 if cx is None else cx
    cy = p.get("cy") if id(p) in placed else None
    cy = H / 2 if cy is None else cy
    if W / H > 0.8:                                               # wider than 4:5: full height, centred on the piece
        w = H * 0.8; x = min(max(cx - w / 2, 0), W - w)
        im = im.crop((round(x), 0, round(x + w), H))
    else:                                                         # taller than 4:5: full width
        h = W / 0.8; y = min(max(cy - h / 2, 0), H - h)
        im = im.crop((0, round(y), W, round(y + h)))
    if im.height > MAXH:
        im = im.resize((round(MAXH * 0.8), MAXH), Image.LANCZOS)
    return im

def put(slug, name, im):
    for base in ("_originals", "img"):
        d = os.path.join(PDP, base, slug); os.makedirs(d, exist_ok=True)
        im.save(os.path.join(d, name), quality=90)
    open(os.path.join(PDP, "_originals", slug, name + ".studio"), "w").write("hires 2026-09-18\n")

report = {"replaced": [], "added": []}
extras = {}
for p in P:
    im = whole(p)
    if id(p) in placed:
        put(p["slug"], p["slot"], im); report["replaced"].append(f'{p["slug"]}/{p["slot"]} <- {p["file"]}')
    else:
        extras.setdefault(p["slug"], []).append((p, im))

# the new shots join the end of their piece's gallery, after whatever the studio has chosen to show
data = json.load(urllib.request.urlopen("http://127.0.0.1:8131/api/editor"))
content = json.load(open(os.path.join(PDP, "content.json")))
for slug, items in extras.items():
    prod = next(x for x in data["products"] if x["slug"] == slug)
    e = content["products"].setdefault(slug, {})
    gallery = list(e.get("gallery") or prod["defaults"]["gallery"])
    for n, (p, im) in enumerate(items, 1):
        name = f"hires-{n}.jpg"
        put(slug, name, im)
        gallery.append(f"img/{slug}/{name}"); report["added"].append(f"{slug}/{name} <- {p['file']}")
    e["gallery"] = gallery
json.dump(content, open(os.path.join(PDP, "content.json"), "w"), indent=1, ensure_ascii=False)
print(len(report["replaced"]), "replaced;", len(report["added"]), "added")
json.dump(report, open("/tmp/place_report.json", "w"), indent=1)
