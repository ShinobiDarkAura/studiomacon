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
import argparse, json, os, shutil, subprocess, sys
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

    But matching proportions too closely is its own trap. The shadow falls to the
    RIGHT, so a tall narrow piece in a tall narrow frame has nowhere to put it:
    Rebi came back with 31px to the right of itself, 7% of its own width, against
    75% for Zuma and 83% for Ren, and its shadow was cut off hard at the border.
    A portrait piece therefore gets the square frame, which costs some height and
    buys the room the shadow actually needs.
    """
    w, h = Image.open(ref_path).size
    if h > w * 1.15:
        return "1024x1024"
    if w > h * 1.15:
        return "1536x1024"
    return "1024x1024"


def shadow_room(ref_path):
    """Give the reference frame somewhere to put the shadow.

    frame_size only steers GPT: gen_scene_fal.py accepts --size and ignores it,
    because fal takes the output's proportions from the reference image. So a
    tall narrow cutout produced a tall narrow scene, and Rebi's shadow — which
    falls to the RIGHT — hit the border still at full strength with 7% of its own
    width of frame to spare.

    Padding the reference fixes both engines at once: the object is set left of
    centre on a square canvas so the room is where the shadow is going. Square
    rather than landscape: a tall piece dropped into a wide frame gets scaled
    down to fit and loses the detail the fidelity score depends on. Returns the
    original path when it already has room, so nothing is rewritten needlessly.
    """
    im = Image.open(ref_path).convert("RGBA")
    w, h = im.size
    want_w = max(w, h)
    if want_w <= w * 1.05:
        return ref_path
    pad = Image.new("RGBA", (want_w, h), (0, 0, 0, 0))
    pad.paste(im, (int((want_w - w) * 0.34), 0))    # left of centre; shadow goes right
    out = ref_path.replace(".png", "-roomy.png")
    pad.save(out)
    print(f"  padded reference {w}x{h} -> {want_w}x{h} so the shadow has somewhere to fall")
    return out


def generate(piece, notes, name, engine="gpt"):
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
        "Plain even background. Warm late-afternoon light from camera-left, softly "
        "diffused and slightly frontal. "
        "CAMERA — critical, and identical for every piece in the set: shoot from EXACTLY "
        "eye level with the surface the object rests on, straight on, lens perpendicular "
        "to the object, horizon line at the object's own mid-height. Never from above, "
        "never looking down, no tilt, no high angle. The object is seen as someone "
        "standing at a shelf at eye height would see it, resting naturally on its base. "
        "FRAMING IS CRITICAL: the ENTIRE object must be visible well inside the frame, "
        "including the very bottom where it meets the surface, with at least 20 percent "
        "empty margin on every side. Do not crop, touch or run the object off any edge. "
        "SHADOW: the object casts ONE real, soft-edged shadow onto the surface, falling "
        "to the RIGHT and slightly toward the camera, about as long as the object is wide "
        "and clearly visible on the surface beside it. The shadow must stay COMPLETELY "
        "inside the frame with clear empty surface beyond its tip — it must never touch "
        "or run off an edge. "
        "It must be the SAME OBJECT as the reference: same form, same proportions, same "
        "surface finish, same colour and patina, with every curve, taper, edge, gap and "
        "opening preserved. Do NOT simplify, round off, thicken, straighten or regularise "
        "it; if the shape is unusual or asymmetric it must stay that way. Only the "
        "viewpoint and the lighting change."
    )
    os.makedirs(SCENES, exist_ok=True)
    dst = os.path.join(SCENES, f"scene-{piece}.png")
    ref = shadow_room(os.path.join(CUTS, f"obj-{piece}.png"))
    script = "gen_scene_fal.py" if engine == "fal" else "gen_scene.py"
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "shelf/tools", script),
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
    # reports every dark thing in the scene and the sprite comes out frame-sized.
    # The mask is an ellipse, not a rectangle: a blurred box leaves faint straight
    # edges that read as a pale panel behind the piece once it is composited onto
    # a flat plate. Offset to the right because the light is camera-left.
    x0, y0, x1, y1 = bbox
    ow, oh = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2 + ow * 0.18, y1
    ry_, rx_ = max(8.0, oh * 0.55), max(8.0, ow * 0.95)
    yy, xx = np.ogrid[:dark.shape[0], :dark.shape[1]]
    d = ((xx - cx) / rx_) ** 2 + ((yy - cy) / ry_) ** 2
    keep = np.clip(1.35 - d, 0.0, 1.0).astype(np.float32)
    keep = cv2.GaussianBlur(keep, (0, 0), max(4, ow * 0.05))
    dark *= keep

    # Anything this faint is measurement noise on a flat backdrop, and it is
    # exactly what shows up as a halo against the plate. Cut it, then ease the
    # remainder so there is no hard step where it was cut.
    dark = np.clip((dark - 0.06) / 0.94, 0.0, 1.0)
    dark = dark * dark * (3 - 2 * dark)

    sh = Image.new("RGBA", scene.size, SHADOW_RGB + (0,))
    sh.putalpha(Image.fromarray((np.clip(dark, 0, 1) * 255).astype(np.uint8)))

    # base = bottom-centre of the object's footprint
    cols = np.where(mask.max(axis=0) > 0.15)[0]
    rows = np.where(mask.max(axis=1) > 0.15)[0]
    base = (int((cols[0] + cols[-1]) / 2), int(rows[-1]))
    return obj, sh, base, bbox


def shadow_score(scene_path, obj_alpha, bbox):
    """How much shadow the piece actually casts on the surface beside it.

    Identity and framing were already scored; shadow was not, and that is how a
    whole set arrived with nothing under it. The model is erratic here — the same
    prompt and piece gave 33 on one roll and 9 on the next — so it has to be
    measured per roll and re-rolled like anything else.

    Measured as mean darkening in a band to the right of the object at its base,
    against clean ground nearby.
    """
    import numpy as np
    arr = np.asarray(Image.open(scene_path).convert("RGB"), np.float32).mean(axis=2)
    m = np.asarray(obj_alpha) > 128
    x0, y0, x1, y1 = bbox
    ow, oh = x1 - x0, y1 - y0
    band = np.zeros(arr.shape, bool)
    band[max(0, y1 - int(oh * 0.25)):min(arr.shape[0], y1 + int(oh * 0.35)),
         x1:min(arr.shape[1], x1 + int(ow * 1.5))] = True
    band &= ~m
    if band.sum() < 50:
        return 0.0
    clean = np.percentile(arr[band], 92)
    return float((clean - arr[band]).clip(0).mean())


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
    ap.add_argument("--engine", choices=("gpt", "fal"), default="fal",
                    help="fal = Nano Banana (cheap, for relighting pieces); gpt = GPT Image 2")
    ap.add_argument("--tries", type=int, default=3,
                    help="re-roll a flagged piece and keep the best; scores vary a lot "
                         "run to run, so one low result is usually a bad roll, not a limit")
    ap.add_argument("--min-shadow", type=float, default=16.0,
                    help="minimum cast-shadow strength; below this the roll is retried")
    ap.add_argument("--min-iou", type=float, default=0.80,
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
    cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
    prod = next((x for x in cache["products"] if x["slug"] == slug), None)
    if prod is None:
        sys.exit(f"slug {slug!r} not in the catalogue")

    best = None
    for attempt in range(1, a.tries + 1):
        if not (a.skip_generate and os.path.exists(scene)):
            print(f"generating scene for {slug} (try {attempt}/{a.tries}) ...", flush=True)
            generate(a.piece, prod.get("notes"), prod["name"], engine=a.engine)

        obj, sh, base, bbox = harvest(scene, shadow_strength=a.strength)
        iou = fidelity(ref, obj, bbox)
        shadow = shadow_score(scene, obj.getchannel("A"), bbox)
        sw, sh_ = Image.open(scene).size
        margin = 4
        clipped = (bbox[0] <= margin or bbox[1] <= margin
                   or bbox[2] >= sw - margin or bbox[3] >= sh_ - margin)
        # A roll has to pass identity AND cast a shadow; ranking on both keeps the
        # best compromise if none passes outright.
        score = -1.0 if clipped else iou + min(shadow, 40.0) / 100.0
        print(f"  try {attempt}: IoU {iou:.3f}  shadow {shadow:4.1f}"
              f"{'  CLIPPED' if clipped else ''}", flush=True)

        if best is None or score > best["score"]:
            keep = os.path.join(SCENES, f"scene-{a.piece}-best.png")
            shutil.copyfile(scene, keep)
            best = {"obj": obj, "sh": sh, "base": base, "bbox": bbox, "shadow": shadow,
                    "iou": iou, "clipped": clipped, "score": score, "scene": keep}
        if not clipped and iou >= a.min_iou and shadow >= a.min_shadow:
            break
        if a.skip_generate:
            break

    obj, sh, base, bbox = best["obj"], best["sh"], best["base"], best["bbox"]
    iou, clipped, shadow = best["iou"], best["clipped"], best["shadow"]
    shutil.move(best["scene"], scene)
    verdict = ("CLIPPED" if clipped else
               "ok" if (iou >= a.min_iou and shadow >= a.min_shadow) else
               "NO-SHADOW" if iou >= a.min_iou else "REVIEW")

    sprite = Image.new("RGBA", obj.size, (0, 0, 0, 0))
    sprite.alpha_composite(sh)
    sprite.alpha_composite(obj)
    box = sprite.getchannel("A").getbbox()
    sprite = sprite.crop(box)

    sprite.save(os.path.join(OUT, f"{a.piece}.png"))
    json.dump(
        {"sprite": list(sprite.size),
         "object": [bbox[2] - bbox[0], bbox[3] - bbox[1]],
         "base": [base[0] - box[0], base[1] - box[1]],
         "source_scene": os.path.relpath(scene, ROOT),
         "engine": a.engine,
         "fidelity_iou": round(iou, 4),
         "shadow": round(shadow, 1),
         "clipped": bool(clipped),
         "verdict": verdict},
        open(os.path.join(OUT, f"{a.piece}.json"), "w"), indent=2,
    )
    print(f"  fidelity IoU {iou:.3f}  shadow {shadow:.1f}  [{verdict}]" + ("  <- subject touches the frame edge" if clipped else ""))
    print(f"  sprite {sprite.size}  object {bbox[2]-bbox[0]}x{bbox[3]-bbox[1]}  base {base}")


if __name__ == "__main__":
    main()
