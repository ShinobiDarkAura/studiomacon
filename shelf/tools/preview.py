#!/usr/bin/env python3
"""Draw what the page lays out, without a browser.

The pieces and labels are positioned by CSS percentages now, so a mistake in that
arithmetic cannot be caught by looking at the composed plate. This replays the
exact percentages the page emits — same plate, same sprites, same offsets — so the
layout can be checked when a browser is not cooperating.

Type is approximated with a system serif. The page sets labels in Ashcroft Light,
which ships here as woff2 only and cannot be loaded by PIL — so judge type on the
page, not here. Positions and sizes are faithful.

    python3 shelf/tools/preview.py
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "shelf", "_site")


def font(path_opts, size):
    for p in path_opts:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def longest_mm(notes):
    for n in notes or []:
        v = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?=[x×]|\s*mm)", n)]
        if v:
            return max(v)


def main():
    comp = json.load(open(os.path.join(ROOT, "shelf/composition-dressed.json"), encoding="utf-8"))
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
    prod = {p["slug"]: p for p in cache["products"]}
    over = comp.get("mm", {})

    CARRIERS = ["torn-paper", "washi-tape", "vellum-strip", "graph-slip", "ledger-strip"]
    for scene in comp["scenes"]:
        plate = Image.open(os.path.join(SITE, f"plate-{scene['id']}.jpg")).convert("RGBA")
        W, H = plate.size
        d = ImageDraw.Draw(plate)
        serif = font(["/System/Library/Fonts/Supplemental/Georgia.ttf",
                      "/System/Library/Fonts/Supplemental/Times New Roman.ttf"], max(19, int(W * 0.0134) + 6))
        mono = font(["/System/Library/Fonts/Supplemental/Courier New.ttf",
                     "/System/Library/Fonts/Menlo.ttc"], max(9, int(W * 0.0088)))
        ppmm, sink = scene["px_per_mm"], scene.get("sink_px", 0)
        fronts = scene.get("shelf_fronts", [])

        def front_mid(y):
            """Centre of the shelf's front face — the band the label sits on.

            Measured off the plate rather than guessed at, because the visible
            front face is not where the piece stands: the shelf top is seen in
            slight perspective, so its front edge sits well below the surface
            the object rests on.
            """
            if not fronts:
                return y + 0.045
            f = min(fronts, key=lambda f: abs(f["y"] - y))["front"]
            return (f[0] + f[1]) / 2.0

        for oi, o in enumerate(scene["objects"]):
            slug = o["slug"]; p = prod[slug]
            meta = json.load(open(os.path.join(ROOT, "shelf/sprites", f"{pieces[slug]}.json")))
            mid = front_mid(o["y"])
            mm = over.get(slug) or longest_mm(p.get("notes"))
            s = (mm * ppmm) / max(meta["object"]) * float(o.get("scale", 1.0))
            sw, sh = meta["sprite"][0] * s, meta["sprite"][1] * s
            bx, by = meta["base"][0] * s, meta["base"][1] * s
            left, top = W * o["x"] - bx, H * o["y"] - by + sink

            sp = Image.open(os.path.join(SITE, f"piece-{slug}.webp")).convert("RGBA")
            sp = sp.resize((max(1, round(sw)), max(1, round(sh))), Image.LANCZOS)
            plate.alpha_composite(sp, (round(left), round(top)))

            gap = 0
            name_h, price_h = serif.size, mono.size
            block = name_h + gap + price_h
            cx = left + bx
            name_mid = mid * H - block / 2 + name_h / 2
            price_mid = mid * H + block / 2 - price_h / 2
            name, price = p["name"], (f"${float(p['price']):,.0f}" if p.get("price") else "")
            # at rest the page shows the name only; the price appears on hover
            # the carrier the label is written on
            car = Image.open(os.path.join(ROOT, "shelf/carriers",
                                          CARRIERS[oi % len(CARRIERS)] + ".png")).convert("RGBA")
            tw = int(d.textlength(name, font=serif) + serif.size * 6.6)
            th = int(serif.size * 5.0)
            car = car.resize((max(8, tw), max(6, th)), Image.LANCZOS)
            plate.alpha_composite(car, (int(cx - tw / 2), int(mid * H - th / 2)))
            d.text((cx, mid * H), name, fill=(43, 39, 34), font=serif, anchor="mm")

        out = os.path.join(ROOT, "shelf/_test", f"preview-{scene['id']}.jpg")
        plate.convert("RGB").save(out, quality=92)
        print(f"{scene['id']:14} {len(scene['objects'])} pieces -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
