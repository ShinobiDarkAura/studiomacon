#!/usr/bin/env python3
"""Harvest a shelf-ready sprite for one piece.

  real photo -> cutout (reference)
             -> generated shelf scene (GPT Image 2, piece as reference)
             -> object + its BAKED shadow, lifted back out as one RGBA sprite

The point of the round trip is the shadow. Generating the piece into a lit scene
produces a physically correct contact shadow, bounce and occlusion that no affine
projection of a silhouette can imitate. But rembg only returns the object — it has
no concept of the shadow the object casts — so the shadow has to be recovered from
the shelf separately, by asking how much darker each pixel is than the shelf would
be with nothing on it.

That shadow-free estimate comes from a greyscale morphological closing: dilate then
erode with a kernel wider than the shadow. Closing removes dark features smaller
than its kernel while leaving the shelf's own gradient intact, which is exactly the
separation needed. The shadow is then stored as alpha over a warm dark, so
compositing it onto a different plate behaves like a multiply.

  python3 shelf/tools/harvest.py milo-1 --skip-generate
  python3 shelf/tools/harvest.py pip-2
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut import cut, offline_session, clean_alpha, SHADOW_RGB

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CUTS = os.path.join(ROOT, "shelf", "cutouts")
SCENES = os.path.join(ROOT, "shelf", "scenes")
OUT = os.path.join(ROOT, "shelf", "sprites")


def frame_size(ref_path):
    """Match the canvas to the piece's proportions.

    A tall piece rendered into a landscape frame gets scaled up to fill it and
    walks off the bottom edge, taking its contact shadow with it and truncating
    the silhouette the fidelity score is measured against.
    """
    w, h = Image.open(ref_path).size
    if h > w * 1.15:
        return "1024x1536"
    if w > h * 1.15:
        return "1536x1024"
    return "1024x1024"


def generate(piece, notes, name):
    """Render the piece into a shelf scene. Material comes from the catalogue."""
    material = "; ".join(n for n in (notes or []) if not any(c.isdigit() for c in n)) or "cast metal"
    # A lighting rig, not a set. The environment comes from the plate; all this
    # image has to deliver is the piece correctly lit and its shadow. A plain
    # seamless ground is also what makes the shadow recoverable at all — the
    # closing below needs a smooth background to measure darkening against, and
    # any set dressing (shelf edges, boxes, uprights) reads as shadow and gets
    # harvested along with it.
    prompt = (
        f"Product photograph of this exact object — {name}, {material} — resting on a "
        "plain seamless pale warm-grey surface. Absolutely nothing else in frame: no "
        "shelf, no shelf edge, no walls, no boxes, no props, no texture, no vignette. "
        "Plain even background. Warm late-afternoon light from camera-left at a low "
        "angle, casting one soft contact shadow to the right. Eye-level camera. "
        "FRAMING IS CRITICAL: the ENTIRE object must be visible well inside the frame, "
        "including the very bottom where it meets the surface, with at least 20 percent "
        "empty margin on every side. Do not crop, touch or run the object off any edge. "
        "Leave clear empty surface beneath and to the right of it for its shadow. "
        "Reproduce the object EXACTLY as given: identical silhouette, proportions, stance, "
        "surface finish and colour. Do not restyle, redesign, smooth or re-proportion it. "
        "It must remain the same object, only relit."
    )
    os.makedirs(SCENES, exist_ok=True)
    dst = os.path.join(SCENES, f"scene-{piece}.png")
    ref = os.path.join(CUTS, f"obj-{piece}.png")
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "shelf/tools/gen_scene.py"),
         "--ref", ref, "--out", dst, "--prompt", prompt, "--size", frame_size(ref)],
        check=True,
    )
    return dst


def harvest(scene_path, shadow_strength=1.0, kernel=0.22):
    """Split a generated scene into (object RGBA, shadow RGBA, object base point)."""
    import cv2
    from rembg import remove

    scene = Image.open(scene_path).convert("RGB")
    obj = remove(scene, session=offline_session()).convert("RGBA")
    a = clean_alpha(obj.getchannel("A"))
    obj.putalpha(a)
    bbox = a.getbbox()
    if not bbox:
        sys.exit("nothing segmented in " + scene_path)

    arr = np.asarray(scene, np.float32) / 255.0
    mask = np.asarray(a, np.float32) / 255.0

    # Shadow-free estimate of the shelf. The kernel must be wider than the shadow
    # or the closing will preserve it and the ratio comes out flat.
    ow = bbox[2] - bbox[0]
    k = max(15, int(ow * kernel) | 1)
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    clean = cv2.morphologyEx(arr, cv2.MORPH_CLOSE, se)
    clean = cv2.GaussianBlur(clean, (0, 0), k * 0.35)

    ratio = np.clip(arr / np.maximum(clean, 1e-4), 0, 1)
    dark = np.clip(1.0 - ratio.min(axis=2), 0, 1) * shadow_strength
    dark[mask > 0.15] = 0.0            # object handles itself
    dark = cv2.GaussianBlur(dark, (0, 0), 1.6)
    dark[dark < 0.03] = 0.0            # kill sensor/paper noise

    # Bound the shadow to the object's own footprint. Without this the closing
    # reports every dark thing in the scene — archive boxes, the wall falloff,
    # the shelf's front edge — and the sprite comes out the size of the frame.
    # Asymmetric because the light is camera-left: the cast falls to the right.
    x0, y0, x1, y1 = bbox
    ow, oh = x1 - x0, y1 - y0
    keep = np.zeros(dark.shape, np.float32)
    rx0, rx1 = int(x0 - ow * 0.25), int(x1 + ow * 1.40)
    ry0, ry1 = int(y1 - oh * 0.35), int(y1 + oh * 0.90)
    keep[max(0, ry0):ry1, max(0, rx0):rx1] = 1.0
    keep = cv2.GaussianBlur(keep, (0, 0), max(6, ow * 0.06))
    dark *= keep

    sh = Image.new("RGBA", scene.size, SHADOW_RGB + (0,))
    sh.putalpha(Image.fromarray((np.clip(dark, 0, 1) * 255).astype(np.uint8)))

    # base = bottom-centre of the object's footprint
    cols = np.where(mask.max(axis=0) > 0.15)[0]
    rows = np.where(mask.max(axis=1) > 0.15)[0]
    base = (int((cols[0] + cols[-1]) / 2), int(rows[-1]))
    return obj, sh, base, bbox


def fidelity(ref_path, obj, bbox, H=520):
    """Silhouette IoU of the harvested object against the real photo's cutout.

    Drift is not uniform across the catalogue. Pieces with a strong asymmetric
    gesture come back at ~0.98; a smooth symmetric mass gives the model little to
    lock onto and it regularises toward the generic form of the animal, which is
    a plausible object that is not the one being sold. That has to be caught per
    piece rather than assumed from a spot check, so every harvest is scored.
    """
    ref = Image.open(ref_path).convert("RGBA")
    gen = obj.crop(bbox)

    def sil(im):
        im = im.resize((max(1, round(im.width * H / im.height)), H), Image.LANCZOS)
        return np.array(im.getchannel("A")) > 100

    a, b = sil(ref), sil(gen)
    W = max(a.shape[1], b.shape[1])

    def pad(m):
        out = np.zeros((H, W), bool)
        x = (W - m.shape[1]) // 2
        out[:, x:x + m.shape[1]] = m
        return out

    a, b = pad(a), pad(b)
    return float((a & b).sum() / max(1, (a | b).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piece")
    ap.add_argument("--slug", help="catalogue slug (defaults to piece minus trailing -N)")
    ap.add_argument("--skip-generate", action="store_true")
    ap.add_argument("--width", type=int, default=900, help="reference cutout width")
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--min-iou", type=float, default=0.95,
                    help="below this the piece is flagged for review, not silently accepted")
    a = ap.parse_args()

    slug = a.slug or a.piece.rsplit("-", 1)[0]
    os.makedirs(CUTS, exist_ok=True); os.makedirs(OUT, exist_ok=True)

    ref = os.path.join(CUTS, f"obj-{a.piece}.png")
    if not os.path.exists(ref):
        print(f"cutting reference {a.piece} ...", flush=True)
        c = cut(a.piece)
        c = c.resize((a.width, round(c.height * a.width / c.width)), Image.LANCZOS)
        c.save(ref)

    scene = os.path.join(SCENES, f"scene-{a.piece}.png")
    if not a.skip_generate or not os.path.exists(scene):
        cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
        p = next((x for x in cache["products"] if x["slug"] == slug), None)
        if p is None:
            sys.exit(f"slug {slug!r} not in the catalogue")
        print(f"generating scene for {slug} ...", flush=True)
        scene = generate(a.piece, p.get("notes"), p["name"])

    print("harvesting ...", flush=True)
    obj, sh, base, bbox = harvest(scene, shadow_strength=a.strength)

    sprite = Image.new("RGBA", obj.size, (0, 0, 0, 0))
    sprite.alpha_composite(sh)
    sprite.alpha_composite(obj)
    box = sprite.getchannel("A").getbbox()
    sprite = sprite.crop(box)

    iou = fidelity(ref, obj, bbox)
    # A clipped subject is a different failure from drift and has to be named as
    # one: the silhouette is truncated, so the IoU understates fidelity, and the
    # base anchor lands on the frame edge instead of on the object's footprint.
    sw, sh_ = Image.open(scene).size
    margin = 4
    clipped = (bbox[0] <= margin or bbox[1] <= margin
               or bbox[2] >= sw - margin or bbox[3] >= sh_ - margin)
    verdict = "CLIPPED" if clipped else ("ok" if iou >= a.min_iou else "REVIEW")

    sprite.save(os.path.join(OUT, f"{a.piece}.png"))
    json.dump(
        {"sprite": list(sprite.size),
         "object": [bbox[2] - bbox[0], bbox[3] - bbox[1]],
         "base": [base[0] - box[0], base[1] - box[1]],
         "source_scene": os.path.relpath(scene, ROOT),
         "fidelity_iou": round(iou, 4),
         "clipped": bool(clipped),
         "verdict": verdict},
        open(os.path.join(OUT, f"{a.piece}.json"), "w"), indent=2,
    )
    print(f"  fidelity IoU {iou:.3f}  [{verdict}]" + ("  <- subject touches the frame edge" if clipped else ""))
    print(f"  sprite {sprite.size}  object {bbox[2]-bbox[0]}x{bbox[3]-bbox[1]}  base {base}")


if __name__ == "__main__":
    main()
