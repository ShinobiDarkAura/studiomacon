"""Extend a photograph's plain backdrop upward and downward using its own pixels.

No invention: the new area is built from the picture's own edge rows, mirrored and
blurred along the direction the backdrop already fades, so the weave never repeats
recognisably. Only for even sweeps — never for a hand, a tool or a busy surface.
"""
import sys
from PIL import Image, ImageFilter, ImageStat

def expand(src, dst, ratio=(4, 5), feather=0.55):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target_h = round(w * ratio[1] / ratio[0])
    if target_h <= h:
        im.save(dst, quality=92); return im.size, im.size
    add = target_h - h
    top_add = round(add * 0.62)          # more room above the piece than below it
    bot_add = add - top_add

    out = Image.new("RGB", (w, target_h))
    out.paste(im, (0, top_add))

    def band(strip, height, flip):
        """Grow a strip of the picture into a band of new backdrop."""
        b = strip.resize((w, height), Image.LANCZOS)
        if flip:
            b = b.transpose(Image.FLIP_TOP_BOTTOM)
        # the backdrop softens as it recedes, so the new area softens with it
        return b.filter(ImageFilter.GaussianBlur(radius=max(2, height * 0.03)))

    if top_add:
        out.paste(band(im.crop((0, 0, w, max(8, round(h * 0.10)))), top_add, True), (0, 0))
    if bot_add:
        out.paste(band(im.crop((0, h - max(8, round(h * 0.10)), w, h)), bot_add, True), (0, top_add + h))

    # soften the two joins so no line shows
    for y in (top_add, top_add + h):
        k = round(h * 0.03)
        if k < 4 or y - k < 0 or y + k > target_h: continue
        seam = out.crop((0, y - k, w, y + k)).filter(ImageFilter.GaussianBlur(radius=k * 0.5))
        out.paste(Image.blend(out.crop((0, y - k, w, y + k)), seam, feather), (0, y - k))

    out.save(dst, quality=92)
    return (w, h), out.size

if __name__ == "__main__":
    print(expand(sys.argv[1], sys.argv[2]))
