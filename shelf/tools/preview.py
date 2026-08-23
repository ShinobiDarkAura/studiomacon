#!/usr/bin/env python3
"""Draw what the page lays out, without a browser.

The pieces and labels are positioned by CSS percentages now, so a mistake in that
arithmetic cannot be caught by looking at the composed plate. This replays the
exact percentages the page emits — same plate, same sprites, same offsets — so the
layout can be checked when a browser is not cooperating.

Type is approximated with a system serif; the page itself uses Louize and Index.

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

    for scene in comp["scenes"]:
        plate = Image.open(os.path.join(SITE, f"plate-{scene['id']}.jpg")).convert("RGBA")
        W, H = plate.size
        d = ImageDraw.Draw(plate)
        serif = font(["/System/Library/Fonts/Supplemental/Georgia.ttf",
                      "/System/Library/Fonts/Supplemental/Times New Roman.ttf"], max(13, int(W * 0.0115)))
        mono = font(["/System/Library/Fonts/Supplemental/Courier New.ttf",
                     "/System/Library/Fonts/Menlo.ttc"], max(11, int(W * 0.0085)))
        ppmm, sink = scene["px_per_mm"], scene.get("sink_px", 0)
        scene_dy = scene.get("label_dy", 0.045)

        for o in scene["objects"]:
            slug = o["slug"]; p = prod[slug]
            meta = json.load(open(os.path.join(ROOT, "shelf/sprites", f"{pieces[slug]}.json")))
            dy = o.get("label_dy", scene_dy)
            mm = over.get(slug) or longest_mm(p.get("notes"))
            s = (mm * ppmm) / max(meta["object"])
            sw, sh = meta["sprite"][0] * s, meta["sprite"][1] * s
            bx, by = meta["base"][0] * s, meta["base"][1] * s
            left, top = W * o["x"] - bx, H * o["y"] - by + sink

            sp = Image.open(os.path.join(SITE, f"piece-{slug}.webp")).convert("RGBA")
            sp = sp.resize((max(1, round(sw)), max(1, round(sh))), Image.LANCZOS)
            plate.alpha_composite(sp, (round(left), round(top)))

            cx, cy = left + bx, top + by + dy * H
            name, price = p["name"], (f"${float(p['price']):,.0f}" if p.get("price") else "")
            wn = d.textlength(name, font=serif)
            d.text((cx - wn / 2, cy), name, fill=(43, 39, 34), font=serif)
            wp = d.textlength(price, font=mono)
            d.text((cx - wp / 2, cy + serif.size * 1.35), price, fill=(141, 131, 117), font=mono)

        out = os.path.join(ROOT, "shelf/_test", f"preview-{scene['id']}.jpg")
        plate.convert("RGB").save(out, quality=92)
        print(f"{scene['id']:14} {len(scene['objects'])} pieces -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
