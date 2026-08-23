#!/usr/bin/env python3
"""Render each shelf scene from composition.json.

Scale is real: a piece's size comes from the millimetres in its catalogue notes,
mapped through the scene's px_per_mm, so two pieces on one shelf are correct
relative to each other without anyone eyeballing it. Where the notes give three
numbers the axis order is inconsistent across the catalogue, so the largest is
taken and mapped to the object's longest side — that is ordering-agnostic.

    python3 shelf/tools/compose.py
"""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "_site")


def longest_mm(notes):
    for n in notes or []:
        nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?=[x×]|\s*mm)", n)]
        if nums:
            return max(nums)
    return None


def contact_shadow(plate, cx, by, obj_px, cfg):
    """Lay a soft contact shadow on the shelf under a piece.

    The harvested sprites carry almost none. Asking the lighting rig for "a short
    contact shadow tucked beneath the piece" worked too well — what little it cast
    is hidden behind the object itself, so the sprites arrive with a few pixels of
    shadow below the base and nothing to ground them.

    This is a contact shadow only: a small soft ellipse where the piece meets the
    shelf, offset the way the plate's own props are lit. It is not the long fake
    cast shadow that read as wrong earlier — the plate supplies the room's light,
    this only supplies the darkening at the point of contact.
    """
    rx = max(2.0, obj_px * float(cfg.get("width", 0.62)))
    ry = max(1.0, obj_px * float(cfg.get("height", 0.13)))
    dx = obj_px * float(cfg.get("dx", 0.10))
    blur = max(1.5, obj_px * float(cfg.get("blur", 0.09)))
    pad = int(blur * 4 + rx)

    layer = Image.new("L", (int(rx * 2 + pad * 2), int(ry * 2 + pad * 2)), 0)
    ImageDraw.Draw(layer).ellipse(
        [pad, pad, pad + rx * 2, pad + ry * 2],
        fill=int(255 * float(cfg.get("opacity", 0.42))),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    tint = Image.new("RGBA", layer.size, tuple(cfg.get("rgb", [58, 48, 38])) + (0,))
    tint.putalpha(layer)
    plate.alpha_composite(tint, (round(cx + dx - layer.width / 2), round(by - layer.height / 2)))


def settle(sp, ambient, cfg):
    """Sit a piece into the room's tone instead of sitting on top of it.

    A cut-out carries the contrast of its own shoot, so against faded plaster and
    bleached books it reads bolder than everything around it — correct in
    isolation, wrong in company. Four small moves, all on the object only:
    pull contrast in, lift the blacks off pure dark, ease saturation, and blend a
    little of the room's own colour over it the way distance and ambient light do.
    """
    a = np.asarray(sp, np.float32)
    rgb, alpha = a[..., :3], a[..., 3:4] / 255.0

    pivot = float(cfg.get("pivot", 150.0))
    rgb = pivot + (rgb - pivot) * float(cfg.get("contrast", 1.0))
    rgb = rgb + float(cfg.get("lift", 0.0))
    lum = rgb.mean(axis=2, keepdims=True)
    rgb = lum + (rgb - lum) * float(cfg.get("saturation", 1.0))
    haze = float(cfg.get("haze", 0.0))
    if haze:
        rgb = rgb * (1 - haze) + np.asarray(ambient, np.float32) * haze

    # Only the object changes; the baked shadow keeps its own density.
    out = np.concatenate([np.clip(rgb, 0, 255), a[..., 3:4]], axis=2)
    blend = np.clip(alpha, 0, 1)
    out[..., :3] = a[..., :3] * (1 - blend) + out[..., :3] * blend
    return Image.fromarray(out.astype(np.uint8))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "shelf/composition.json"
    comp = json.load(open(os.path.join(ROOT, which), encoding="utf-8"))
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
    notes = {p["slug"]: p.get("notes") for p in cache["products"]}
    live = {p["slug"] for p in cache["products"] if p.get("status") == "live"}
    overrides = comp.get("mm", {})
    excluded = set(pieces.get("_shelf_exclude", {}))

    os.makedirs(OUT, exist_ok=True)
    for scene in comp["scenes"]:
        plate = Image.open(os.path.join(ROOT, scene["plate"])).convert("RGBA")
        W, H = plate.size
        ppmm = scene["px_per_mm"]
        cfg = scene.get("settle", {})
        ambient = np.asarray(plate.convert("RGB"), np.float32).reshape(-1, 3)
        ambient = np.median(ambient, axis=0)
        # Pieces read as hovering without this. The anchor is the lowest opaque
        # pixel of the cutout, but a shelf seen straight on shows a band of top
        # surface, and the y in composition.json lands on its back edge. Sinking
        # by a few pixels puts the piece on the surface rather than behind it.
        sink = scene.get("sink_px", 0)

        # Back to front, so a piece nearer the camera overlaps one behind it
        # without anyone hand-managing draw order.
        for obj in sorted(scene["objects"], key=lambda o: o["y"]):
            slug = obj["slug"]
            if slug in excluded:
                sys.exit(f"{slug} is on a shelf but marked excluded in pieces.json")
            if slug not in live:
                sys.exit(f"{slug} is on a shelf but is not live in the catalogue")
            piece = pieces[slug]
            sp = Image.open(os.path.join(ROOT, "shelf/sprites", f"{piece}.png")).convert("RGBA")
            meta = json.load(open(os.path.join(ROOT, "shelf/sprites", f"{piece}.json")))

            mm = overrides.get(slug) or longest_mm(notes.get(slug))
            if not mm:
                sys.exit(f"no size for {slug}: add it to composition.json 'mm'")
            s = (mm * ppmm) / max(meta["object"])
            sp = sp.resize((max(1, round(sp.width * s)), max(1, round(sp.height * s))), Image.LANCZOS)
            if cfg:
                sp = settle(sp, ambient, cfg)
            bx, by = meta["base"][0] * s, meta["base"][1] * s
            cs = scene.get("contact_shadow")
            if cs:
                contact_shadow(plate, W * obj["x"], H * obj["y"] + sink,
                               meta["object"][0] * s, cs)
            plate.alpha_composite(sp, (round(W * obj["x"] - bx), round(H * obj["y"] - by) + sink))

        dst = os.path.join(OUT, f"scene-{scene['id']}.jpg")
        plate.convert("RGB").save(dst, quality=92)
        print(f"{scene['id']:10} {len(scene['objects']):2d} pieces -> {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    main()
