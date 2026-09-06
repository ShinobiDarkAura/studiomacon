#!/usr/bin/env python3
"""Cut photographed pieces off their backdrop, keeping the shadow re-placeable.

The shadow is stored as a TRANSMISSION MAP applied by multiply, not as a dark
colour with an alpha. That distinction is the whole point of this tool.

Chuang et al., "Shadow Matting and Compositing" (SIGGRAPH 2003), give the
physical model as

    C = b*L + (1-b)*S

with L the lit surface, S the same surface fully shadowed, and b the per-pixel
visibility of the light. Rearranged for a surface we have not seen yet, and
folding the ambient term in, the shadow is just a per-pixel attenuation:

    T = C / L          measured on the paper it was actually cast on
    result = T * L_new applied to whatever it is later placed on

An alpha-over composite of a dark colour cannot do this. It drives every pixel
toward one fixed colour, so it is only correct on a surface the same tone as the
original paper - on anything darker it lightens the surface, which is exactly
the pale halo that kept appearing around pieces on the shelf.

Three files per photograph, on a common canvas so they register:

    object/    RGBA, the piece alone, backdrop unmixed out of its soft edge
    shadow/    RGB transmission, white where there is no shadow, multiply this
    preview/   the two combined over a mid grey, to look at

    python3 shelf/tools/cut_photos.py SRC_DIR OUT_DIR [--list FILE] [--width N]
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
import cv2
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut import offline_session, clean_alpha
from rembg import remove


def load(path, long_edge):
    """HEIC included - sips reads what PIL will not.

    The orientation tag is baked in here rather than carried. iPhone files
    record rotation as EXIF 274 instead of rotating the pixels, and rembg
    honours that tag while raw pixel access does not - so the mask came back
    transposed against the image and the two could not be combined. Baking it
    once at load also means a portrait photograph is not saved on its side.
    """
    if path.lower().endswith((".heic", ".heif")):
        tmp = tempfile.mktemp(suffix=".png")
        subprocess.run(["sips", "-s", "format", "png", "-Z", str(long_edge), path, "--out", tmp],
                       capture_output=True, check=True)
        im = ImageOps.exif_transpose(Image.open(tmp)).convert("RGB")
        im.load(); os.unlink(tmp)
        return im
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    im.thumbnail((long_edge, long_edge), Image.LANCZOS)
    return im


def drop_clutter(alpha, margin_frac=0.012):
    """Discard anything touching the frame edge.

    The lightbox sweep curves up at the sides, and that curve reads as a dark
    band in the corner of most frames. The segmenter sometimes calls it
    foreground; it is background, so leaving it in both cuts it out and drags
    the crop to the corner. The jewellery never touches the border; the sweep
    always does.
    """
    h, w = alpha.shape
    mg = max(4, int(min(h, w) * margin_frac))
    m = (alpha > 40).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m, bool)
    for i in range(1, n):
        x, y, ww, hh, area = st[i]
        if area < 0.0004 * h * w:
            continue
        if x <= mg or y <= mg or x + ww >= w - mg or y + hh >= h - mg:
            continue
        keep |= (lab == i)
    # Returned too, not just discarded: it is dark, so removing it only from the
    # object leaves it in the shadow map as attenuation belonging to the
    # backdrop rather than to the piece.
    clutter = (alpha > 40) & ~keep
    clutter = cv2.dilate(clutter.astype(np.uint8),
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))).astype(bool)
    return (alpha * keep).astype(np.uint8), clutter


def transmission(img, obj_alpha, clutter=None, kernel=0.22):
    """Per-channel T = observed / unshadowed, measured against the paper.

    The unshadowed paper is estimated by closing the image with a kernel wider
    than the shadow, which removes it, then blurring off the seams. Only the
    ground is measured - the object's own pixels are excluded and left at 1.
    """
    arr = np.asarray(img, np.float32) / 255.0
    m = obj_alpha.astype(np.float32) / 255.0
    ys, xs = np.nonzero(obj_alpha > 40)
    if not len(xs):
        return np.ones_like(arr)
    ow = xs.max() - xs.min() + 1
    k = max(15, int(ow * kernel) | 1)

    # Estimate the lit paper at low resolution. Morphology with a non-rectangular
    # kernel costs the kernel's AREA per pixel, and this kernel scales with the
    # piece — 169x169 on a typical frame, which is 22 of the 25 seconds each
    # photograph was taking, against 0.6s for the actual segmentation. The thing
    # being estimated is a smooth shadow-free field, so it carries no detail that
    # survives to full resolution anyway.
    scale = min(1.0, 480.0 / max(arr.shape[:2]))
    small = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    ks = max(5, int(k * scale) | 1)
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))
    lit_s = cv2.GaussianBlur(cv2.morphologyEx(small, cv2.MORPH_CLOSE, se), (0, 0), ks * 0.35)
    lit = cv2.resize(lit_s, (arr.shape[1], arr.shape[0]), interpolation=cv2.INTER_CUBIC)
    T = np.clip(arr / np.maximum(lit, 1e-4), 0.0, 1.0)

    # Bound it to the ground around the subject. A photograph has other dark
    # things in it and the closing reports all of them.
    grow = max(24, int(ow * 0.6)) | 1
    near = cv2.dilate((obj_alpha > 40).astype(np.uint8),
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
    near = np.clip(cv2.GaussianBlur(near.astype(np.float32), (0, 0), grow * 0.18), 0, 1)

    raw = np.clip(1.0 - T, 0, 1)

    # Remove the lightbox sweep BEFORE the shadow is bounded to the subject.
    #
    # The curve is out of focus, so the segmenter never called it foreground and
    # taking clutter out of the OBJECT mask did not touch it — it exists only
    # here, as darkness the background estimate reads as attenuation. In
    # principle a wide enough closing would fold the sweep into the lit estimate
    # and it would cancel in C/L, but the curve is far broader than any kernel
    # that still preserves a shadow, so it is removed explicitly instead.
    #
    # It has to happen before bounding: bounding zeroes the frame border, after
    # which the blob touches no edge and this test cannot see it. Being backdrop
    # rather than an object, anything connected to the frame edge here is always
    # safe to drop.
    d1 = raw.max(axis=2)
    h, w = d1.shape
    mgn = max(3, int(min(h, w) * 0.01))
    n, lab, st, _ = cv2.connectedComponentsWithStats((d1 > 0.05).astype(np.uint8), 8)
    intruder = np.zeros(d1.shape, bool)
    for i in range(1, n):
        x, y, ww, hh, _ = st[i]
        if x <= mgn or y <= mgn or x + ww >= w - mgn or y + hh >= h - mgn:
            intruder |= (lab == i)
    # a piece's own contact shadow is never treated as an intruder
    keep_near = cv2.dilate((obj_alpha > 40).astype(np.uint8),
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61))).astype(bool)
    raw[intruder & ~keep_near] = 0.0

    depth = raw * near[..., None]
    depth[depth < 0.02] = 0.0                      # sensor noise on flat paper
    depth *= (1.0 - m)[..., None]                  # the object is not its own shadow
    if clutter is not None:
        depth[clutter] = 0.0
    return np.clip(1.0 - depth, 0.0, 1.0)


def defringe(rgb, alpha, backdrop):
    """Unmix the paper out of the soft edge: observed = a*true + (1-a)*paper."""
    a = alpha.astype(np.float32)[..., None] / 255.0
    soft = (a[..., 0] > 0.02) & (a[..., 0] < 0.97)
    out = rgb.astype(np.float32).copy()
    unmixed = (out - (1.0 - a) * backdrop) / np.maximum(a, 0.25)
    out = np.where(soft[..., None], np.clip(unmixed, 0, 255), out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--list", help="JSON array of stems to process")
    ap.add_argument("--width", type=int, default=2400)
    a = ap.parse_args()

    names = {os.path.splitext(f)[0]: f for f in os.listdir(a.src) if not f.startswith(".")}
    stems = json.load(open(a.list)) if a.list else sorted(names)
    stems = [os.path.splitext(s)[0] for s in stems]

    for d in ("object", "shadow", "preview"):
        os.makedirs(os.path.join(a.out, d), exist_ok=True)
    sess = offline_session()
    report = []

    for i, stem in enumerate(stems):
        f = names.get(stem)
        if not f:
            print(f"  [{i+1}/{len(stems)}] {stem}: not in source"); continue
        img = load(os.path.join(a.src, f), a.width)
        alpha = np.asarray(clean_alpha(remove(img, session=sess).convert("RGBA").getchannel("A")))
        full = alpha.copy()
        alpha, clutter = drop_clutter(alpha)
        clipped = False
        if alpha.max() < 40 and full.max() >= 40:
            # Everything touched the border - usually because the piece sits on
            # a prop that runs off the frame, so the two segment as one region.
            # Better a flagged cutout than no cutout.
            alpha, clutter, clipped = full, None, True
        if alpha.max() < 40:
            print(f"  [{i+1}/{len(stems)}] {stem}: nothing left after clutter removal"); continue

        arr = np.asarray(img)
        bg = (np.percentile(arr[alpha < 8], 60, axis=0)
              if (alpha < 8).any() else np.array([235., 233., 230.]))
        T = transmission(img, alpha, clutter)

        # one canvas for both layers, so they register when stacked
        shade = (T.min(axis=2) < 0.985)
        box = cv2.boundingRect(((alpha > 8) | shade).astype(np.uint8))
        x, y, w, h = box
        sl = (slice(y, y + h), slice(x, x + w))

        obj = np.dstack([defringe(arr, alpha, bg)[sl], alpha[sl]]).astype(np.uint8)
        Image.fromarray(obj).save(os.path.join(a.out, "object", stem + ".png"))
        Image.fromarray((T[sl] * 255).astype(np.uint8)).save(
            os.path.join(a.out, "shadow", stem + ".png"))

        # what it looks like dropped on a surface it was not shot on
        ground = np.full((h, w, 3), (176, 168, 154), np.float32)
        comp = ground * T[sl]
        oa = obj[..., 3:4].astype(np.float32) / 255.0
        comp = comp * (1 - oa) + obj[..., :3].astype(np.float32) * oa
        Image.fromarray(comp.astype(np.uint8)).save(
            os.path.join(a.out, "preview", stem + ".jpg"), quality=92)

        oy, ox = np.nonzero(alpha[sl] > 128)
        report.append({"stem": stem, "canvas": [w, h],
                       "object_box": [int(ox.min()), int(oy.min()), int(ox.max()), int(oy.max())]
                       if len(ox) else None,
                       "base": [int((ox.min() + ox.max()) / 2), int(oy.max())] if len(ox) else None,
                       "shadow_depth": round(float(1 - T[sl].min()), 3),
                       "clipped": clipped})
        print(f"  [{i+1}/{len(stems)}] {stem}  {w}x{h}"
              f"  depth {report[-1]['shadow_depth']:.2f}{'  CLIPPED' if clipped else ''}")

    json.dump(report, open(os.path.join(a.out, "_report.json"), "w"), indent=1)
    print(f"\ndone: {len(report)} photographs")


if __name__ == "__main__":
    main()
