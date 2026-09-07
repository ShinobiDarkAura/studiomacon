#!/usr/bin/env python3
"""Build a fidelity-locked jewelry proof from approved transparent masters."""

from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "shelf/scenes/v8-locked-proof"
PLATE = OUT / "jewelry-french-single-shelf-empty-v1.png"

PIECES = (
    # name, source, target width, rotation, base x/y
    ("lunar", ROOT / "shelf/cutouts/obj-lunar-canyon-ring-3.png", 172, -3.0, 390, 668),
    ("zuma", ROOT / "shelf/cutouts/obj-zuma-ring-3.png", 112, 7.0, 790, 468),
    ("meridian", ROOT / "shelf/cutouts/obj-meridian-egg-ring-3.png", 145, -9.0, 1160, 620),
)


def trim(im):
    box = im.getchannel("A").getbbox()
    return im.crop(box) if box else im


def prepare(path, width, rotation):
    im = trim(Image.open(path).convert("RGBA"))
    height = round(im.height * width / im.width)
    im = im.resize((width, height), Image.Resampling.LANCZOS)

    # Warm only the product pixels. Geometry and internal detail stay untouched.
    rgb = ImageEnhance.Color(im.convert("RGB")).enhance(0.82)
    warm = Image.new("RGB", rgb.size, (157, 121, 78))
    rgb = Image.blend(rgb, warm, 0.11)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.04)
    rgb.putalpha(im.getchannel("A"))
    return trim(rgb.rotate(rotation, Image.Resampling.BICUBIC, expand=True))


def projected_shadow(alpha):
    """Project the locked silhouette onto the horizontal support plane."""
    w, h = alpha.size
    ground_h = max(9, round(h * 0.16))
    flat = alpha.resize((round(w * 1.32), ground_h), Image.Resampling.LANCZOS)
    lean = round(ground_h * 1.8)
    flat = flat.transform(
        (flat.width + lean, flat.height),
        Image.Transform.AFFINE,
        (1, -0.9, 0, 0, 1, 0),
        resample=Image.Resampling.BICUBIC,
    )
    body = flat.filter(ImageFilter.GaussianBlur(max(3, ground_h * 0.42)))
    core = flat.filter(ImageFilter.GaussianBlur(max(1, ground_h * 0.10)))
    body = body.point(lambda p: round(p * 0.42))
    core = core.point(lambda p: round(p * 0.58))
    mask = ImageChops.lighter(body, core)
    shadow = Image.new("RGBA", mask.size, (65, 49, 34, 0))
    shadow.putalpha(mask)
    return shadow


def contact_shadow(obj_width):
    """A tight support-plane shadow anchors the object before the cast tail."""
    w = round(obj_width * 0.78)
    h = max(8, round(obj_width * 0.09))
    mask = Image.new("L", (w + 20, h + 16), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((10, 5, 10 + w, 5 + h), fill=145)
    mask = mask.filter(ImageFilter.GaussianBlur(max(2, h * 0.34)))
    shadow = Image.new("RGBA", mask.size, (54, 42, 31, 0))
    shadow.putalpha(mask)
    return shadow


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scene = Image.open(PLATE).convert("RGBA")

    for name, path, width, rotation, base_x, base_y in PIECES:
        obj = prepare(path, width, rotation)
        shadow = projected_shadow(obj.getchannel("A"))
        contact = contact_shadow(obj.width)

        # Bases are the physical contact points on the prop tops.
        ox = round(base_x - obj.width / 2)
        oy = base_y - obj.height
        sx = round(base_x - shadow.width * 0.12)
        sy = base_y - round(shadow.height * 0.48)
        scene.alpha_composite(shadow, (sx, sy))
        scene.alpha_composite(contact, (round(base_x - contact.width / 2),
                                          base_y - round(contact.height / 2)))
        scene.alpha_composite(obj, (ox, oy))

        obj.save(OUT / f"{name}-locked-object.png")
        shadow.save(OUT / f"{name}-locked-shadow.png")
        contact.save(OUT / f"{name}-locked-contact-shadow.png")

    scene.convert("RGB").save(OUT / "jewelry-three-piece-locked-proof-v1.jpg", quality=95)


if __name__ == "__main__":
    main()
