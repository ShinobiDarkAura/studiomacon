#!/usr/bin/env python3
"""Pull every product's variants (sizes, styles, prices, ids) from Shopify into shopify/variants.json.

    python3 pdp/tools/shopify_sync.py      # then rebuild: python3 pdp/build_pdp.py

Uses the public Storefront token in shopify/config.json (read-only).
"""
import json, os, urllib.request

PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(PDP, "shopify", "config.json")))
Q = """{ products(first: 100) { edges { node { handle options { name } variants(first: 100) { edges { node {
      id title price { amount } availableForSale } } } } } } }"""
req = urllib.request.Request(f"https://{cfg['shop']}/api/{cfg['apiVersion']}/graphql.json",
                             data=json.dumps({"query": Q}).encode(),
                             headers={"Content-Type": "application/json", "X-Shopify-Storefront-Access-Token": cfg["storefrontToken"]})
data = json.load(urllib.request.urlopen(req))["data"]["products"]["edges"]
out = {}
for e in data:
    n = e["node"]
    out[n["handle"]] = {
        "option": n["options"][0]["name"] if n["options"] else "Title",
        "variants": [{"value": v["node"]["title"], "id": v["node"]["id"], "price": float(v["node"]["price"]["amount"]),
                      "available": v["node"]["availableForSale"]} for v in n["variants"]["edges"]],
    }
json.dump(out, open(os.path.join(PDP, "shopify", "variants.json"), "w"), indent=1)
print(len(out), "products synced")
