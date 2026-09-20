"""Rewrite the prices in the email templates from Shopify, so a copy-paste is never stale.

Shopify is the one source of prices (see build_pdp.py). The marketing emails name a
piece and its price by hand, because a marketing email has no cart to read from — this
keeps those hand-written numbers honest.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDP = os.path.join(ROOT, "pdp")
EMAIL = os.path.join(PDP, "email", "shopify")

with open(os.path.join(PDP, "shopify", "variants.json")) as f:
    shopify = json.load(f)
with open(os.path.join(ROOT, "_source/products.json")) as f:
    products = json.load(f)

# display name (as the emails write it) -> lowest live price
price = {}
for p in products:
    vs = (shopify.get(p["slug"]) or {}).get("variants") or []
    if vs:
        low = min(float(v["price"]) for v in vs)
        price[p["name"].upper()] = int(low) if low.is_integer() else low

# a tile is a name div followed by a price div; the name is what we look up
TILE = re.compile(r'(padding:12px 0 2px">([^<]+)</div>'
                  r'<div style="[^"]*color:#8a8a8a">)\$([0-9,]+)(</div>)')

changed = []
for name in sorted(os.listdir(EMAIL)):
    if not name.endswith(".html"):
        continue
    path = os.path.join(EMAIL, name)
    src = open(path, encoding="utf-8").read()
    hits = []

    def fix(m):
        head, title, old, tail = m.groups()
        new = price.get(re.sub(r"&#8217;|&#203;", lambda c: {"&#8217;": "’", "&#203;": "Ë"}[c.group()], title).upper())
        if new is None or f"{new:,}".replace(",", "") == old.replace(",", ""):
            return m.group(0)
        hits.append(f"{title} ${old} -> ${new}")
        return f"{head}${new}{tail}"

    out = TILE.sub(fix, src)
    if hits:
        open(path, "w", encoding="utf-8").write(out)
        changed.append((name, hits))

for name, hits in changed:
    print(f"{name}: " + "; ".join(hits))
print(f"email prices: {len(changed)} template(s) updated" if changed else "email prices: all current")
