#!/usr/bin/env python3
"""Cut the piece out of the generated scene and compare it to the real cutout.

Side by side at matched height, plus a silhouette overlay — real in red,
generated in blue, agreement in dark. Drift that the eye forgives at a glance
is obvious once the two outlines are stacked.
"""
import os, sys
from PIL import Image, ImageOps
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut import offline_session, clean_alpha

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = os.path.join(ROOT, "shelf", "_test")
CREAM = (238, 232, 220)


def cut_file(path):
    from rembg import remove
    im = Image.open(path).convert("RGB")
    out = remove(im, session=offline_session()).convert("RGBA")
    out.putalpha(clean_alpha(out.getchannel("A")))
    return out.crop(out.getchannel("A").getbbox())


def on_cream(im, h):
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    bg = Image.new("RGBA", im.size, CREAM + (255,))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def main():
    piece = sys.argv[1] if len(sys.argv) > 1 else "milo-1"
    H = 520
    real = Image.open(os.path.join(ROOT, f"shelf/cutouts/obj-{piece}.png")).convert("RGBA")
    gen = cut_file(os.path.join(T, f"identity-{piece}.png"))
    gen.save(os.path.join(T, f"identity-{piece}-cut.png"))

    a, b = on_cream(real, H), on_cream(gen, H)
    pad = 40
    sheet = Image.new("RGB", (a.width + b.width + pad * 3, H + pad * 2), CREAM)
    sheet.paste(a, (pad, pad))
    sheet.paste(b, (pad * 2 + a.width, pad))
    sheet.save(os.path.join(T, f"identity-{piece}-sidebyside.jpg"), quality=95)

    # silhouette overlay, both normalised to the same height and centred
    def sil(im):
        im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS)
        return np.array(im.getchannel("A")) > 100
    sa, sb = sil(real), sil(gen)
    W = max(sa.shape[1], sb.shape[1])
    def pad_to(m):
        out = np.zeros((H, W), bool)
        x = (W - m.shape[1]) // 2
        out[:, x:x + m.shape[1]] = m
        return out
    sa, sb = pad_to(sa), pad_to(sb)
    rgb = np.full((H, W, 3), 255, np.uint8)
    rgb[sa & ~sb] = (214, 64, 48)     # real only
    rgb[sb & ~sa] = (48, 96, 214)     # generated only
    rgb[sa & sb] = (44, 40, 36)       # agreement
    Image.fromarray(rgb).save(os.path.join(T, f"identity-{piece}-overlay.jpg"), quality=95)

    inter = (sa & sb).sum()
    union = (sa | sb).sum()
    print(f"silhouette IoU: {inter / union:.3f}")
    print(f"real-only px:  {int((sa & ~sb).sum())}")
    print(f"gen-only px:   {int((sb & ~sa).sum())}")


if __name__ == "__main__":
    main()
