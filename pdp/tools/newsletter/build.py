"""The newsletter maker (newsletter.html): a private page for writing the monthly email.

Called from build_pdp.py. It fills the maker with the shop's pieces (name, price, kind) and makes sure each
piece has its two email photographs in img/email (tile-<slug>.jpg, 4:5, and held-<slug>.jpg, 3:2), cutting
any that are missing from the piece's own photos. Existing email photos are never touched.
"""
import json, os, subprocess
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))


def _cut(pdp, src, dst, w, ratio):
    im = ImageOps.exif_transpose(Image.open(os.path.join(pdp, src))).convert("RGB")
    im = ImageOps.fit(im, (w, round(w / ratio)), Image.LANCZOS)
    im.save(os.path.join(pdp, "img", "email", dst), quality=82, optimize=True, progressive=True)


def _first(pdp, *paths):
    return next((p for p in paths if p and os.path.exists(os.path.join(pdp, p))), None)


BUREAU = os.path.expanduser("~/Documents/git/macon-archive/index.html")          # the Bureau of Provenance: its calendar of monthly letters


def letters():
    """The Bureau's monthly letter outlines (LETTER_EDITIONS: kind → YYYY-MM → label, subject, body), read with node
    from the Bureau's page. Empty when the Bureau isn't on this machine; the maker then skips smart drafts."""
    if not os.path.exists(BUREAU):
        return {}
    js = r"""const s=require('fs').readFileSync(process.argv[1],'utf8'),a=s.indexOf('const LETTER_EDITIONS=');if(a<0){console.log('{}');process.exit()}
let i=s.indexOf('{',a),d=0,j=i;for(;j<s.length;j++){if(s[j]=='{')d++;else if(s[j]=='}'){d--;if(!d)break}}
console.log(JSON.stringify(Function('return ('+s.slice(i,j+1)+')')()))"""
    try:
        return json.loads(subprocess.run(["node", "-e", js, BUREAU], capture_output=True, text=True, timeout=20).stdout or "{}")
    except Exception:
        return {}


def build(pdp, pieces, content, shop=None):
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
    page = page.replace("/*SHOP*/{}", json.dumps(shop or {}))
    page = page.replace("/*LETTERS*/{}", json.dumps(letters(), ensure_ascii=False))
    # issues written ahead of time (starters/*.json), offered first under New
    sd = os.path.join(HERE, "starters")
    starters = [json.load(open(os.path.join(sd, f), encoding="utf-8")) for f in sorted(os.listdir(sd)) if f.endswith(".json")] if os.path.isdir(sd) else []
    page = page.replace("/*STARTERS*/[]", json.dumps(starters, ensure_ascii=False))          # the public, read-only store key the site already uses
    with open(os.path.join(pdp, "newsletter.html"), "w", encoding="utf-8") as f:
        f.write(page)
