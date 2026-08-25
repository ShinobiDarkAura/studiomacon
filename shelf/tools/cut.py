#!/usr/bin/env python3
"""Cut a product photo to transparency and bake a directional contact shadow.

Go/no-go test for the shelf concept (BUILD-GUIDE.md §9.1). The question this
answers is not "can we remove a background" — it's whether pieces shot under the
studio's soft catalogue light can be made to sit in a plate's hard window light.

Light is assumed to come from camera-LEFT, matching both the plates and
zuma-ring-3's own cast shadow, so shadows fall to the RIGHT.

Usage:
    python3 shelf/tools/cut.py milo-1 --width 900
    python3 shelf/tools/cut.py zuma-ring-3 --width 520 --squash 0.20
"""
import argparse, json, os, sys
from PIL import Image, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "images", "products")
OUT = os.path.join(ROOT, "shelf", "cutouts")

# Warm near-black pulled toward the plates, never pure black (BUILD-GUIDE §6).
SHADOW_RGB = (58, 48, 38)


def offline_session(model="isnet-general-use"):
    """Build a rembg session from the on-disk model, on CPU, without a fetch.

    Two things are deliberate here:

    1. providers is pinned to CPU. Left to itself onnxruntime picks the CoreML
       provider, which compiles the graph to an .mlmodelc before every run — the
       compile happens in a system daemon, so the Python process sits at ~0% CPU
       for minutes and looks hung rather than busy. The compile is cached to a
       per-process temp dir, so it is paid again on each invocation and never
       amortises for a batch CLI tool.
    2. download_models() is overridden. rembg resolves the model path through it
       and it calls pooch.retrieve() unconditionally, so a cached .onnx still
       depends on the network being reachable.

    Subclassing rather than reimplementing keeps rembg's own normalize/predict,
    so the output is identical to the stock path.
    """
    import onnxruntime as ort
    if model == "birefnet-general":
        from rembg.sessions.birefnet_general import BiRefNetSessionGeneral as Session
    else:
        from rembg.sessions.dis_general_use import DisSession as Session

    path = os.path.join(os.path.expanduser(os.getenv("U2NET_HOME", "~/.u2net")), f"{model}.onnx")
    if not os.path.exists(path):
        sys.exit(f"model not cached: {path}\nrun once with network access to fetch it")
    cls = type("OfflineSession", (Session,),
               {"download_models": classmethod(lambda c, *a, **k: path)})
    return cls(model, ort.SessionOptions(), providers=["CPUExecutionProvider"])


def cut(name, model="isnet-general-use"):
    """Background removal to RGBA, trimmed to the alpha bounding box.

    Model choice is the whole ballgame for rings. u2net segments only the outer
    silhouette, so it returns a ring as a solid disc with the opening filled. The
    obvious repair — key out backdrop-coloured pixels enclosed by the silhouette —
    fails here specifically, because brushed silver and warm linen sit at nearly
    the same tone and it eats the band along with the hole. isnet-general-use cuts
    the opening natively, which makes the repair unnecessary.
    """
    from rembg import remove
    src = Image.open(os.path.join(SRC, f"{name}.jpg")).convert("RGB")
    cutout = remove(src, session=offline_session(model)).convert("RGBA")

    cutout.putalpha(clean_alpha(cutout.getchannel("A")))
    bbox = cutout.getchannel("A").getbbox()
    return cutout.crop(bbox) if bbox else cutout


def clean_alpha(alpha, min_frac=0.02):
    """Drop near-zero alpha dust and any island far smaller than the main subject.

    isnet leaves a faint haze across the frame and the occasional detached speck
    where the backdrop creased. Either one inflates the bounding box, and every
    downstream measurement — the base anchor, the placement scale, the identity
    IoU — is computed against that box, so a single stray pixel silently shifts
    the whole sprite. Keeping only components within min_frac of the largest
    makes the box mean the subject again.
    """
    import cv2, numpy as np
    a = np.asarray(alpha, np.uint8).copy()
    a[a <= 8] = 0
    n, labels, stats, _ = cv2.connectedComponentsWithStats((a > 0).astype(np.uint8), 8)
    if n > 2:
        areas = stats[1:, cv2.CC_STAT_AREA]
        biggest = areas.max()
        for i, area in enumerate(areas, start=1):
            if area < biggest * min_frac:
                a[labels == i] = 0
    return Image.fromarray(a)


def bake_shadow(cutout, squash=0.26, shear=0.55, spread=1.22, opacity=0.74):
    """Project the silhouette onto the ground plane and blur it into a shadow.

    Two layers, because one blur can't do both jobs: a tight dark core that
    reads as contact, and a long soft body that reads as cast light. A single
    radius gives you either a floating object or a smudge.
    """
    w, h = cutout.size
    mask = cutout.getchannel("A")

    # Ground plane: flatten toward the base and lean away from the light.
    flat_h = max(1, int(h * squash))
    ground = mask.resize((int(w * spread), flat_h), Image.LANCZOS)
    gw, gh = ground.size
    lean = int(gh * shear * 2)
    ground = ground.transform(
        (gw + lean, gh), Image.AFFINE, (1, -shear * 2, 0, 0, 1, 0),
        resample=Image.BICUBIC,
    )

    pad = int(max(gw, gh) * 0.9)
    canvas = Image.new("L", (ground.size[0] + pad * 2, gh + pad * 2), 0)
    canvas.paste(ground, (pad, pad))

    body = canvas.filter(ImageFilter.GaussianBlur(gh * 0.42))
    body = body.point(lambda v: int(v * 0.62))
    core = canvas.filter(ImageFilter.GaussianBlur(gh * 0.10))
    core = core.point(lambda v: int(v * 0.95))

    shadow_a = ImageChops.lighter(body, core).point(lambda v: int(v * opacity))
    shadow = Image.new("RGBA", canvas.size, SHADOW_RGB + (0,))
    shadow.putalpha(shadow_a)
    # Anchor: where the object's base sits within the shadow canvas.
    return shadow, (pad, pad + gh)


def compose(cutout, shadow, anchor):
    """Object over its own shadow, plus where the object's base sits in the result.

    The base offset matters: the sprite's bottom edge is the far end of the blurred
    shadow, not the object's feet. Anchoring a placement to the sprite bottom floats
    the object off the shelf by the whole shadow falloff.
    """
    ow, oh = cutout.size
    sw, sh = shadow.size
    ax, ay = anchor
    ox, oy = ax, ay - oh
    minx, miny = min(0, ox), min(0, oy)
    W = max(sw, ox + ow) - minx
    H = max(sh, oy + oh) - miny
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(shadow, (-minx, -miny))
    out.alpha_composite(cutout, (ox - minx, oy - miny))
    bbox = out.getchannel("A").getbbox()
    out = out.crop(bbox)
    # object base, and object left edge, in the cropped sprite's coordinates
    base = ((ox - minx) - bbox[0], (ay - miny) - bbox[1])
    return out, base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--squash", type=float, default=0.26)
    ap.add_argument("--shear", type=float, default=0.55)
    ap.add_argument("--opacity", type=float, default=0.74)
    a = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    print(f"cutting {a.name} ...", flush=True)
    c = cut(a.name)
    if c.width != a.width:
        c = c.resize((a.width, round(c.height * a.width / c.width)), Image.LANCZOS)
    c.save(os.path.join(OUT, f"obj-{a.name}.png"))

    sh, anchor = bake_shadow(c, squash=a.squash, shear=a.shear, opacity=a.opacity)
    sprite, base = compose(c, sh, anchor)
    sprite.save(os.path.join(OUT, f"obj-{a.name}-shadow.png"))
    json.dump(
        {"sprite": list(sprite.size), "object": list(c.size), "base": list(base)},
        open(os.path.join(OUT, f"obj-{a.name}-shadow.json"), "w"), indent=2,
    )
    print(f"  cutout {c.size}  sprite {sprite.size}  base {base}")


if __name__ == "__main__":
    main()
