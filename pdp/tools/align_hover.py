#!/usr/bin/env python3
"""Hold the piece still when a home-grid tile is hovered.

Each tile shows two photographs in one 4:5 frame: the still, and the in-hand
picture that fades in on hover. Shot separately, the piece sits somewhere else
in each one, so hovering made it jump and change size.

This measures where the piece actually sits in both photographs, then works out
the framing (object-position and an extra zoom) that puts the in-hand piece on
the same spot, at the same height, as the still one. The numbers are written to
img/hover-align.json and the build puts them on the hover picture as
--hx / --hy / --hz.

    python3 pdp/tools/align_hover.py            # measure, write json, draw the sheet
    python3 pdp/tools/align_hover.py --sheet    # draw the sheet from the saved json

Anything the detector reads wrongly can be corrected by hand in BY_HAND below.
"""
import json, math, os, re, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # pdp/
REPO = os.path.dirname(ROOT)
SITE = ROOT          # the built site: pdp/index.html and pdp/img/<slug>/
OUTJSON = os.path.join(SITE, "img", "hover-align.json")

FRAME = (240, 300)          # the virtual tile: 4:5, the proportion the grid clips to

MAX_HZ = 1.9          # past this the hover picture is no longer a photograph, it is a crop of one

# Where the detector read a piece wrongly and it was set by eye instead, off a grid drawn
# over the photograph. slug -> {"still": box, "held": box}, each box (left, top, right, bottom)
# as a percentage of that photograph's own width and height.
BY_HAND = {
    "pip":               {"still": (36, 32, 65, 70), "held": (36, 30, 61, 60)},
    "rebi":              {"still": (40, 21, 60, 80), "held": (36, 28, 72, 82)},
    "ren":               {"still": (42, 29, 64, 73), "held": (36, 31, 63, 79)},
    "zuma":              {"still": (38, 34, 65, 65), "held": (36, 31, 72, 70)},
    "ori":               {"still": (42, 28, 60, 71), "held": (43, 26, 63, 66)},
    "yael":              {"still": (38, 29, 73, 74), "held": (34, 18, 80, 72)},
    "milo":              {"still": (28, 37, 70, 72), "held": (34, 30, 68, 64)},
    "ibi":               {"still": (38, 27, 62, 76), "held": (35, 19, 70, 80)},
    "eleph":             {"still": (30, 21, 62, 76), "held": (30, 23, 61, 74)},
    "zuma-ring":         {"still": (40, 30, 62, 79), "held": (30, 21, 52, 80)},
    "eclipse-ring":      {"still": (38, 38, 62, 64), "held": (34, 31, 56, 49)},
    "sietch-aperture":   {"still": (38, 28, 60, 75), "held": (34, 44, 76, 62)},
    "lunar-canyon-ring": {"still": (36, 33, 64, 72), "held": (38, 38, 70, 58)},
    "ear-cuff":          {"still": (40, 32, 60, 70), "held": (45, 52, 63, 78)},
    "meridian-egg-ring": {"still": (38, 34, 62, 68), "held": (52, 42, 72, 62)},
}


# Corrections made by eye off the comparison sheet, where matching the two boxes did not
# quite match the two pictures (the box a piece fills is not the same shape lying in a hand
# as it is standing on a sweep). slug -> (dx, dy, dz): dx/dy move the held piece right and
# down by that share of the frame, dz makes it that much bigger.
NUDGE = {
    "ren":               (-0.02, 0.00, 0.95),
    "ibi":               (-0.01, 0.00, 1.00),
    "eclipse-ring":      (-0.06, 0.04, 1.00),
    "sietch-aperture":   ( 0.00, 0.08, 0.85),
    "lunar-canyon-ring": (-0.02, 0.08, 1.05),
    "meridian-egg-ring": (-0.03, 0.00, 0.70),   # the hand shows only the ring's crown, not the whole band
}

# Pieces whose hover picture is a different scene rather than a different view: the Wonder
# Horn and the Starship Key are shown worn, a speck against a body. Holding those still would
# mean blowing the photograph up four or five times, so they are left as they were shot.
SKIP = {"wonderhorn-talisman", "starshipkey-pendant"}


# ---------------------------------------------------------------- finding the piece

def piece_on_sweep(im, small=360):
    """A piece on a plain pale sweep: whatever the backdrop's slow shading cannot explain.
    (The same reading tools/reframe.py uses to centre a photograph.)"""
    g = im.convert("L").copy()
    w0, h0 = g.size
    g.thumbnail((small, small), Image.LANCZOS)
    w, h = g.size
    blur = g.filter(ImageFilter.GaussianBlur(radius=max(6, w / 9)))
    d = np.abs(np.asarray(g, float) - np.asarray(blur, float))
    thr = max(5.0, np.percentile(d, 99.2) * 0.30)
    m = d > thr
    cs = np.where(m.sum(0) > h * 0.02)[0]
    rs = np.where(m.sum(1) > w * 0.02)[0]
    if not len(cs) or not len(rs):
        return None
    k = w0 / w
    return round(cs[0] * k), round(rs[0] * k), round(cs[-1] * k), round(rs[-1] * k)


def piece_in_hand(im, small=340, cut=80):
    """A piece held in a hand: whatever belongs neither to the backdrop nor to the skin.

    The outer band of the picture is only ever backdrop, hand and surface, so its colours
    are taken as a model of "not the piece"; everything far from that model in Lab is a
    candidate. The hand's own creases and shadows answer too, but they run off the edge of
    the picture, and the piece does not — so the largest island that touches no edge is it.
    """
    import cv2
    w0, h0 = im.size
    work = im.convert("RGB").copy()
    work.thumbnail((small, small), Image.LANCZOS)
    w, h = work.size
    a = np.asarray(work)
    lab = cv2.cvtColor(a, cv2.COLOR_RGB2LAB).astype(float)
    px = np.stack([lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128], -1)

    band = np.zeros((h, w), bool)
    b = max(3, round(min(h, w) * 0.04))
    band[:b] = band[-b:] = True
    band[:, :b] = band[:, -b:] = True
    samp = px[band]
    samp = samp[np.linspace(0, len(samp) - 1, min(700, len(samp))).astype(int)]
    d = np.sqrt(((px.reshape(-1, 1, 3) - samp[None]) ** 2).sum(-1)).min(1).reshape(h, w)

    m = (d > max(3.0, np.percentile(d, cut))).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

    n, _, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    edge = max(2, round(min(w, h) * 0.012))
    best, best_area, any_box, any_area = None, 0, None, 0
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < w * h * 0.003:
            continue
        box = (x, y, x + bw, y + bh)
        if x > edge and y > edge and x + bw < w - edge and y + bh < h - edge and area > best_area:
            best, best_area = box, area
        if area > any_area and area < w * h * 0.5:
            any_box, any_area = box, area
    box = best or any_box
    if not box:
        return None
    k = w0 / w
    return tuple(round(v * k) for v in box)


def has_hand(im, small=200):
    """Is there skin in this photograph? (Then it is an in-hand picture, whatever it is called.)"""
    import cv2
    work = im.convert("RGB").copy()
    work.thumbnail((small, small), Image.LANCZOS)
    hsv = cv2.cvtColor(np.asarray(work), cv2.COLOR_RGB2HSV)
    H, S, V = hsv[..., 0].astype(float), hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    skin = ((H <= 25) | (H >= 172)) & (S > 0.18) & (S < 0.72) & (V > 0.25)
    return skin.mean() > 0.12


def find(path):
    """The piece's box in a photograph, read the way that photograph asks for."""
    im = Image.open(path).convert("RGB")
    box = piece_in_hand(im) if has_hand(im) else piece_on_sweep(im)
    return im.size, (box or piece_on_sweep(im))


# ---------------------------------------------------------------- the CSS, in numbers

def cover(iw, ih, W, H):
    return max(W / iw, H / ih)


def place(iw, ih, x, y, z, W, H):
    """object-fit:cover, then object-position (x,y) as fractions, then scale(z) about the
    same point of the frame. Returns (offset_x, offset_y, scale): a point p in image pixels
    lands at offset + scale * p."""
    s0 = cover(iw, ih, W, H)
    return (x * (W - z * iw * s0), y * (H - z * ih * s0), s0 * z)


def framed(box, iw, ih, x, y, z, W, H):
    """Where a box of the photograph lands inside the frame."""
    ox, oy, s = place(iw, ih, x, y, z, W, H)
    return (ox + s * box[0], oy + s * box[1], ox + s * box[2], oy + s * box[3])


def solve(still, held, x, y, z, W, H, nudge=(0, 0, 1)):
    """The held picture's framing: object-position and extra zoom that put its piece where the
    still's piece is, at the size the still's piece reads. Returns (hx, hy, hz, notes).

    The two cannot always both be had. A picture may only be slid about inside the frame as
    far as it overhangs it, so a picture zoomed just enough to match the size often cannot be
    slid far enough to match the place; zooming in buys the travel but costs the match. So the
    zoom is searched rather than solved, and the one that leaves the piece looking stillest —
    counting a jump in place as worse than a change in size — wins.
    """
    (siw, sih), sbox = still
    (hiw, hih), hbox = held
    t = framed(sbox, siw, sih, x, y, z, W, H)
    diag = lambda b: math.hypot(b[2] - b[0], b[3] - b[1])
    tcx, tcy = (t[0] + t[2]) / 2 + nudge[0] * W, (t[1] + t[3]) / 2 + nudge[1] * H
    td = diag(t) * nudge[2]                              # across the corners: steadier than height alone
                                              # when a piece is held at a different angle

    s0 = cover(hiw, hih, W, H)
    pd = max(1.0, diag(hbox))
    cx, cy = (hbox[0] + hbox[2]) / 2, (hbox[1] + hbox[3]) / 2
    want = td / (s0 * pd)                     # the total scale that would match the size exactly

    def at(Z):
        """Best placing at this zoom, and what it costs: how far the piece still lands from
        where it should (in frame heights), and how far off its size is."""
        def frac(target, c, dim_img, dim_frame):
            span = dim_frame - Z * dim_img * s0        # negative: the picture overhangs the frame
            if abs(span) < 1e-9:
                return 0.5, target - (Z * s0 * c + 0.5 * span)
            f = min(1.0, max(0.0, (target - Z * s0 * c) / span))
            return f, target - (Z * s0 * c + f * span)
        hx, ex = frac(tcx, cx, hiw, W)
        hy, ey = frac(tcy, cy, hih, H)
        return hx, hy, math.hypot(ex, ey) / H, abs(math.log(Z / want))

    best = None
    lo, hi = z, z * MAX_HZ
    for i in range(401):
        Z = lo + (hi - lo) * i / 400
        hx, hy, off, size = at(Z)
        cost = 9 * off * off + size * size             # a jump in place reads worse than a change in size
        if best is None or cost < best[0]:
            best = (cost, Z, hx, hy, off, size)
    _, Z, hx, hy, off, size = best

    notes = []
    if off > 0.012:
        notes.append(f"{round(off * 100)}% of a frame away from where the still's piece sits")
    if size > 0.03:
        notes.append(("smaller" if Z < want else "larger") + f" than the still by {round(abs(math.exp(size) - 1) * 100)}%")
    if want > z * MAX_HZ * 1.02:
        notes.append(f"would need {want / z:.1f}x zoom; capped at {MAX_HZ}x")
    return hx, hy, Z / z, notes


# ---------------------------------------------------------------- the comparison sheet

def render(path, x, y, z, W, H, cross=True, box=None, target=None):
    """Draw what the browser would draw, at frame size."""
    im = Image.open(path).convert("RGB")
    ox, oy, s = place(im.width, im.height, x, y, z, W, H)
    big = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    out = Image.new("RGB", (W, H), (230, 230, 228))
    out.paste(big, (round(ox), round(oy)))
    d = ImageDraw.Draw(out)
    if box:
        b = framed(box, im.width, im.height, x, y, z, W, H)
        d.rectangle([b[0], b[1], b[2], b[3]], outline=(255, 90, 0), width=2)
    if target:
        d.rectangle(list(target), outline=(40, 210, 90), width=2)          # where the still's piece sits
    if cross:
        d.line([W / 2, 0, W / 2, H], fill=(0, 200, 255), width=1)
        d.line([0, H / 2, W, H / 2], fill=(0, 200, 255), width=1)
    return out


def outline_over(base, other):
    """The still, with the hover picture's edges drawn over it: where the two disagree, the
    green outline sits away from the shape underneath it."""
    import cv2
    e = cv2.Canny(cv2.cvtColor(np.asarray(other), cv2.COLOR_RGB2GRAY), 60, 150)
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    a = np.asarray(base).copy()
    a[e > 0] = (40, 255, 120)
    return Image.fromarray(a)


def sheet(rows, dst, W, H):
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
    gap, head, lab = 10, 34, 26
    cols = max(len(r[1]) for r in rows)
    cw, ch = W * cols + gap * (cols + 1), H + gap + head
    out = Image.new("RGB", (cw, (ch + lab) * len(rows) + gap), (255, 255, 255))
    d = ImageDraw.Draw(out)
    for i, (slug, imgs, note) in enumerate(rows):
        top = gap + i * (ch + lab)
        d.text((gap, top), f"{slug}    {note}", fill=(0, 0, 0), font=font)
        for j, im in enumerate(imgs):
            out.paste(im, (gap + j * (W + gap), top + head))
        for j, t in enumerate(("still", "held  before", "held  after", "hover edges on still")[:cols]):
            d.text((gap + j * (W + gap), top + head + H + 3), t, fill=(90, 90, 90), font=font)
    out.save(dst)
    return dst


# ---------------------------------------------------------------- main

def tiles():
    html = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    pat = (r'<a class="piece" href="([\w-]+)\.html"([^>]*)><span class="pic">'
           r'<img src="([^"]+)"[^>]*>(?:<img class="held" src="([^"]+)")?')
    for m in re.finditer(pat, html):
        slug, style, still, held = m.group(1), m.group(2), m.group(3), m.group(4)
        if not held:
            continue
        num = lambda k, d: float((re.search(rf"--{k}:([-\d.]+)", style) or [None, d]).__getitem__(1))
        x = num("x", 50) / 100
        y = num("y", 50) / 100
        z = num("z", 1.12)
        yield slug, still, held, x, y, z


def main():
    W, H = FRAME
    scratch = os.environ.get("ALIGN_SCRATCH") or os.path.join(REPO, "..", "align-scratch")
    os.makedirs(scratch, exist_ok=True)
    saved = {}
    if "--sheet" in sys.argv and os.path.exists(OUTJSON):
        saved = json.load(open(OUTJSON))

    out, rows = {}, []
    for slug, still_src, held_src, x, y, z in tiles():
        if slug in SKIP:
            continue
        sp, hp = os.path.join(SITE, still_src), os.path.join(SITE, held_src)
        (siw, sih), sbox = find(sp)
        (hiw, hih), hbox = find(hp)
        by = BY_HAND.get(slug, {})
        pct = lambda b, w, h: (b[0] * w / 100, b[1] * h / 100, b[2] * w / 100, b[3] * h / 100)
        if "still" in by:
            sbox = pct(by["still"], siw, sih)
        if "held" in by:
            hbox = pct(by["held"], hiw, hih)
        if not sbox or not hbox:
            rows.append((slug, [render(sp, x, y, z, W, H), render(hp, x, y, z, W, H),
                                render(hp, x, y, z, W, H)], "NOT FOUND"))
            continue

        hx, hy, hz, notes = solve(((siw, sih), sbox), ((hiw, hih), hbox), x, y, z, W, H,
                                  NUDGE.get(slug, (0, 0, 1)))
        if slug in saved:
            hx, hy, hz = saved[slug]["hx"] / 100, saved[slug]["hy"] / 100, saved[slug]["hz"]

        out[slug] = {"hx": round(hx * 100, 2), "hy": round(hy * 100, 2), "hz": round(hz, 4)}
        after = render(hp, hx, hy, z * hz, W, H, cross=False)
        rows.append((slug, [
            render(sp, x, y, z, W, H, box=sbox),
            render(hp, x, y, z, W, H, box=hbox),
            render(hp, hx, hy, z * hz, W, H, box=hbox,
                   target=framed(sbox, siw, sih, x, y, z, W, H)),
            outline_over(render(sp, x, y, z, W, H, cross=False), after),
        ], f'hx {out[slug]["hx"]:g}  hy {out[slug]["hy"]:g}  hz {out[slug]["hz"]:g}'
           + ("   — " + "; ".join(notes) if notes else "")))
        print(f'{slug:22s} hx {out[slug]["hx"]:6.2f}  hy {out[slug]["hy"]:6.2f}  hz {out[slug]["hz"]:.4f}'
              + ("   " + "; ".join(notes) if notes else ""))

    if "--sheet" not in sys.argv:
        with open(OUTJSON, "w") as f:
            json.dump(out, f, indent=2, sort_keys=True)
            f.write("\n")
        print("wrote", OUTJSON)
    for i in range(0, len(rows), 6):
        print("sheet:", sheet(rows[i:i + 6], os.path.join(scratch, f"hover-align-sheet-{i // 6 + 1}.png"), W, H))


if __name__ == "__main__":
    main()
