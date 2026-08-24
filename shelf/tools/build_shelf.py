#!/usr/bin/env python3
"""Emit the shelf page: bare plates, pieces as elements, labels, nav, record.

The pieces are laid over the plate in the browser rather than burned into it.
Same sprites and the same arithmetic compose.py uses, so the result is identical
at rest — but each piece is now its own element, which is what lets it respond to
a cursor. Baked into the JPEG it could never move, and lifting a copy over the top
would just show the original still sitting underneath.

    python3 shelf/tools/build_shelf.py
"""
import html, json, os, re, shutil
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "_site")
PIECE_W = 320          # plenty: pieces display around 90-180px
# Carriers rotate through the shelf, each also set at its own slight angle, so a
# shelf reads as hand-labelled rather than as a printed row.
# The torn sheet, on every label.
CARRIERS = ["torn-paper"]
TILTS = ["-2.4deg", "1.7deg", "-1.1deg", "2.3deg", "-1.8deg", "0.9deg"]


def stamp(path):
    """Content stamp for a URL. Without one, a refreshed page keeps serving the
    old plate and the change looks like it never happened."""
    try:
        return int(os.path.getmtime(path))
    except OSError:
        return 0


def money(v):
    return f"${float(v):,.0f}" if v else ""


def longest_mm(notes):
    for n in notes or []:
        nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?=[x×]|\s*mm)", n)]
        if nums:
            return max(nums)


SHUFFLE = """
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>__TONE_DEFS__</defs></svg>

<div class="ed" hidden>
  <div class="ed-h"><b>Shelf editor</b><span class="ed-x">esc</span></div>
  <div class="ed-sel">click a piece</div>
  <div class="ed-scale">scale <b id="ed-scaleval">1.000</b> <span>drag the corner</span></div>
  <label>warmth <input type="range" id="ed-warmth" min="-0.35" max="0.35" step="0.005"><i>0.000</i></label>
  <label>bright <input type="range" id="ed-bright" min="0.5" max="1.6" step="0.005"><i>1.000</i></label>
  <label>contrast <input type="range" id="ed-contrast" min="0.5" max="1.8" step="0.005"><i>1.000</i></label>
  <div class="ed-tip">drag to move &middot; arrows nudge &middot; shift = 10px</div>
  <div class="ed-b"><button id="ed-reset">reset piece</button><button id="ed-save">save &amp; rebuild</button></div>
  <div class="ed-msg"></div>
</div>

<script>
/* Edit mode. Off unless the page is opened with ?edit=1 or e is pressed, so the
   published page carries it but never shows it.

   Everything is previewed exactly as it will ship: position moves the same
   fractions the composition stores, scale turns about the piece's own base so it
   stays standing on the shelf, and tone goes through the same colour matrix the
   build writes. Save posts the changed pieces back and rebuilds. */
(function () {
  var panel = document.querySelector('.ed');
  if (!panel) return;
  var sel = null, dragging = null, on = false;
  var f = {
    warmth: document.getElementById('ed-warmth'),
    bright: document.getElementById('ed-bright'),
    contrast: document.getElementById('ed-contrast')
  };
  var dirty = {};

  function num(el, k) { return parseFloat(el.dataset[k]); }

  function apply(el) {
    var img = el.querySelector('.piece');
    var k = num(el, 'scale') / parseFloat(el.dataset.scale0);
    // turn about the base: the piece stands on that point, so it must not drift
    img.style.transformOrigin = getComputedStyle(el).getPropertyValue('--bx') + ' ' +
                                getComputedStyle(el).getPropertyValue('--by');
    img.style.transform = 'translateX(' + num(el, 'dx') + 'px) scale(' + k + ')';
    var w = num(el, 'warmth'), b = num(el, 'bright'), c = num(el, 'contrast');
    if (!w && b === 1 && c === 1) { img.style.filter = ''; return; }
    var id = 'tone-live-' + el.dataset.scene + '-' + el.dataset.slug;
    var fl = document.getElementById(id);
    if (!fl) {
      var defs = document.querySelector('svg defs');
      fl = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
      fl.id = id; fl.setAttribute('color-interpolation-filters', 'sRGB');
      fl.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'feColorMatrix'));
      defs.appendChild(fl);
    }
    var gr = (1 + w) * b * c, gg = b * c, gb = (1 - w) * b * c, off = 0.5 * (1 - c);
    fl.firstChild.setAttribute('type', 'matrix');
    fl.firstChild.setAttribute('values',
      gr + ' 0 0 0 ' + off + ' 0 ' + gg + ' 0 0 ' + off + ' 0 0 ' + gb + ' 0 ' + off + ' 0 0 0 1 0');
    img.style.filter = 'url(#' + id + ')';
  }

  function place(el) {
    // left is (plate width * x) minus the base offset; only x moved, so shift by
    // the same fraction of the scene's rendered width
    var scene = el.closest('.scene').getBoundingClientRect();
    el.style.left = (parseFloat(el.dataset.left0) + (num(el, 'x') - parseFloat(el.dataset.x0)) * 100) + '%';
    el.style.top = (parseFloat(el.dataset.top0) + (num(el, 'y') - parseFloat(el.dataset.y0)) * 100) + '%';
  }

  function show() {
    if (!sel) { panel.querySelector('.ed-sel').textContent = 'click a piece'; return; }
    panel.querySelector('.ed-sel').textContent = sel.dataset.slug + '  ·  ' + sel.dataset.scene;
    document.getElementById('ed-scaleval').textContent = num(sel, 'scale').toFixed(3);
    ['warmth', 'bright', 'contrast'].forEach(function (k) {
      f[k].value = num(sel, k);
      f[k].nextElementSibling.textContent = (+num(sel, k)).toFixed(3);
    });
  }

  function mark(el) { dirty[el.dataset.scene + '/' + el.dataset.slug] = el; }

  function setOn(v) {
    on = v; panel.hidden = !v;
    document.body.classList.toggle('editing', v);
    if (!v && sel) { sel.classList.remove('ed-on'); sel = null; }
  }

  document.querySelectorAll('.mark').forEach(function (el) {
    el.dataset.scale0 = el.dataset.scale;
    var grip = document.createElement('span');
    grip.className = 'ed-grip';
    el.appendChild(grip);
    el.dataset.x0 = el.dataset.x; el.dataset.y0 = el.dataset.y;
    el.dataset.left0 = parseFloat(el.style.left); el.dataset.top0 = parseFloat(el.style.top);
    el.addEventListener('click', function (e) {
      if (!on) return;
      e.preventDefault(); e.stopPropagation();
      if (sel) sel.classList.remove('ed-on');
      sel = el; el.classList.add('ed-on'); show();
    });
    el.addEventListener('pointerdown', function (e) {
      if (!on) return;
      e.preventDefault();
      if (sel) sel.classList.remove('ed-on');
      sel = el; el.classList.add('ed-on'); show();
      var r = el.closest('.scene').getBoundingClientRect();
      if (e.target.classList.contains('ed-grip')) {
        // Scale about the piece's own base, the point it stands on, so growing
        // it never lifts it off the shelf or slides it along.
        var b = el.getBoundingClientRect();
        var cs = getComputedStyle(el);
        var bx = b.left + b.width * parseFloat(cs.getPropertyValue('--bx')) / 100;
        var by = b.top + b.height * parseFloat(cs.getPropertyValue('--by')) / 100;
        var d0 = Math.hypot(e.clientX - bx, e.clientY - by) || 1;
        dragging = { grip: true, bx: bx, by: by, d0: d0, s0: num(el, 'scale') };
      } else {
        dragging = { sx: e.clientX, sy: e.clientY, x: num(el, 'x'), y: num(el, 'y'), w: r.width, h: r.height };
      }
      el.setPointerCapture(e.pointerId);
    });
    el.addEventListener('pointermove', function (e) {
      if (!dragging || sel !== el) return;
      if (dragging.grip) {
        var d = Math.hypot(e.clientX - dragging.bx, e.clientY - dragging.by);
        el.dataset.scale = Math.max(0.15, dragging.s0 * (d / dragging.d0));
        document.getElementById('ed-scaleval').textContent = num(el, 'scale').toFixed(3);
        apply(el); mark(el);
        return;
      }
      el.dataset.x = dragging.x + (e.clientX - dragging.sx) / dragging.w;
      el.dataset.y = dragging.y + (e.clientY - dragging.sy) / dragging.h;
      place(el); mark(el);
    });
    el.addEventListener('pointerup', function () { dragging = null; });
  });

  Object.keys(f).forEach(function (k) {
    f[k].addEventListener('input', function () {
      if (!sel) return;
      sel.dataset[k] = f[k].value;
      f[k].nextElementSibling.textContent = (+f[k].value).toFixed(3);
      apply(sel); mark(sel);
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'e' && !e.metaKey && !e.ctrlKey && e.target === document.body) { setOn(!on); return; }
    if (!on) return;
    if (e.key === 'Escape') { setOn(false); return; }
    if (!sel || e.key.indexOf('Arrow') !== 0) return;
    e.preventDefault();
    var r = sel.closest('.scene').getBoundingClientRect();
    var step = (e.shiftKey ? 10 : 1);
    if (e.key === 'ArrowLeft') sel.dataset.x = num(sel, 'x') - step / r.width;
    if (e.key === 'ArrowRight') sel.dataset.x = num(sel, 'x') + step / r.width;
    if (e.key === 'ArrowUp') sel.dataset.y = num(sel, 'y') - step / r.height;
    if (e.key === 'ArrowDown') sel.dataset.y = num(sel, 'y') + step / r.height;
    place(sel); mark(sel);
  });

  document.getElementById('ed-reset').addEventListener('click', function () {
    if (!sel) return;
    sel.dataset.x = sel.dataset.x0; sel.dataset.y = sel.dataset.y0;
    sel.dataset.scale = sel.dataset.scale0;
    sel.dataset.warmth = 0; sel.dataset.bright = 1; sel.dataset.contrast = 1;
    place(sel); apply(sel); show(); mark(sel);
  });

  document.getElementById('ed-save').addEventListener('click', function () {
    var msg = panel.querySelector('.ed-msg');
    var pieces = Object.keys(dirty).map(function (k) {
      var el = dirty[k];
      var t = {};
      if (num(el, 'warmth')) t.warmth = +num(el, 'warmth').toFixed(4);
      if (num(el, 'bright') !== 1) t.bright = +num(el, 'bright').toFixed(4);
      if (num(el, 'contrast') !== 1) t.contrast = +num(el, 'contrast').toFixed(4);
      return { scene: el.dataset.scene, slug: el.dataset.slug,
               x: +num(el, 'x').toFixed(5), y: +num(el, 'y').toFixed(5),
               scale: +num(el, 'scale').toFixed(4), dx_px: Math.round(num(el, 'dx')),
               tone: Object.keys(t).length ? t : null };
    });
    if (!pieces.length) { msg.textContent = 'nothing changed'; return; }
    msg.textContent = 'saving ' + pieces.length + '...';
    fetch('/api/composition', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ pieces: pieces }) })
      .then(function (r) { return r.json(); })
      .then(function (r) {
        msg.textContent = r.error ? ('failed: ' + r.error) : ('saved ' + r.saved + ' — reload to see the built page');
        if (!r.error) dirty = {};
      })
      .catch(function (err) { msg.textContent = 'failed: ' + err.message; });
  });

  if (new URLSearchParams(location.search).has('edit')) setOn(true);
})();
</script>
</body></html>"""


# A patch of bare wall, matching plate_tone.py so the two agree.
WALL = (0.42, 0.58, 0.05, 0.28)
TONE_CLAMP = (0.86, 1.16)


def wall_balance(plate):
    """The plate's colour cast, normalised so it carries no brightness."""
    a = np.asarray(Image.open(plate).convert("RGB")).astype(float)
    H, W, _ = a.shape
    x0, x1, y0, y1 = WALL
    m = a[int(H * y0):int(H * y1), int(W * x0):int(W * x1)].reshape(-1, 3).mean(0)
    return m / m.mean()


def tone_to(sp, balance):
    """Move a sprite's cast onto the plate's, leaving its brightness alone.

    Balances are normalised on both sides, so this only ever rotates colour —
    a silver piece stays as light as it was, it just stops reading cool against
    warm plaster.
    """
    a = np.asarray(sp).astype(float)
    m = a[..., 3] > 200
    if not m.any():
        return sp
    own = a[..., :3][m].mean(0)
    gain = np.clip(balance / (own / own.mean()), *TONE_CLAMP)
    a[..., :3] = np.clip(a[..., :3] * gain, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def tone_matrix(t):
    """feColorMatrix values for a piece's tone.

    Kept as a matrix rather than a stack of CSS filter functions because warmth
    is a per-channel gain and CSS has no primitive for that — sepia and
    hue-rotate only approximate it. Green is the hinge, so warmth moves the cast
    without moving the brightness, the same convention used when correcting a
    sprite on disk.
    """
    w = float(t.get("warmth", 0.0))
    b = float(t.get("bright", 1.0))
    c = float(t.get("contrast", 1.0))
    gr, gg, gb = (1.0 + w) * b * c, b * c, (1.0 - w) * b * c
    off = 0.5 * (1.0 - c)
    return (f"{gr:.4f} 0 0 0 {off:.4f}  0 {gg:.4f} 0 0 {off:.4f}  "
            f"0 0 {gb:.4f} 0 {off:.4f}  0 0 0 1 0")


def main():
    comp = json.load(open(os.path.join(ROOT, "shelf/composition-dressed.json"), encoding="utf-8"))
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
    prod = {p["slug"]: p for p in cache["products"]}
    overrides = comp.get("mm", {})
    _ltv = stamp(os.path.join(OUT, "logotype.png"))
    _markv = int(os.path.getmtime(os.path.join(ROOT, "assets/goat-logo-warm.gif")))
    tagline = next((x["value"] for x in cache.get("settings", []) if x["key"] == "tagline"), "")
    os.makedirs(OUT, exist_ok=True)

    # _site is build output and is gitignored, so nothing hand-written may live
    # there. The stylesheet, the logotype and the faces are sources kept under
    # shelf/src and shelf/assets, and copied in on every build.
    shutil.copyfile(os.path.join(ROOT, "shelf/src/shelf.css"), os.path.join(OUT, "shelf.css"))
    for _asset in ("logotype.png", "gabriele-dark.woff2", "gabriele-light.woff2",
                   "ashcroft-light.woff2", "ashcroft-regular.woff2"):
        shutil.copyfile(os.path.join(ROOT, "shelf/assets", _asset), os.path.join(OUT, _asset))

    # Each carrier's own proportions, angle and centre, measured from the file.
    # The box follows the paper — never the other way — and the words are offset
    # and turned onto the sheet, which is neither level nor centred in its frame.
    GEO = json.load(open(os.path.join(ROOT, "shelf/carriers/geometry.json"), encoding="utf-8"))

    hero_copy = f'''
      <div class="hero-copy">
        <!-- Replaced by the logotype; kept in case the wording is wanted back.
        <p class="eyebrow">Studio Ma&ccedil;on</p>
        <h1>Cast by hand, one at a time</h1>
        -->
        <span class="logotype" role="img" aria-label="Studio Ma&ccedil;on"></span>
        <p class="tagline" data-type="Artifacts of Love &bull; Handmade in the U.S."></p>
        <!-- <p class="lede">{html.escape(tagline)}</p> -->
      </div>'''

    scenes_html = []
    tone_defs = []
    for si, scene in enumerate(comp["scenes"]):
        plate_src = os.path.join(ROOT, scene["plate"])
        plate = Image.open(plate_src)
        W, H = plate.size
        plate_name = f"plate-{scene['id']}.jpg"
        plate_path = os.path.join(OUT, plate_name)
        plate.convert("RGB").save(plate_path, quality=90)

        # measured on the source plate, before it is flattened to jpeg
        plate_balance = (wall_balance(os.path.join(ROOT, scene["plate"]))
                         if scene.get("tone_to_plate") else None)
        ppmm, sink = scene["px_per_mm"], scene.get("sink_px", 0)
        fronts = scene.get("shelf_fronts", [])

        def front_mid(y):
            """Centre of the shelf's front face — the band the label sits on.

            Measured off the plate rather than guessed at, because the visible
            front face is not where the piece stands: the shelf top is seen in
            slight perspective, so its front edge sits well below the surface
            the object rests on.
            """
            if not fronts:
                return y + 0.045
            f = min(fronts, key=lambda f: abs(f["y"] - y))["front"]
            return (f[0] + f[1]) / 2.0
        marks = []
        for o in scene["objects"]:
            slug = o["slug"]
            p = prod[slug]
            piece = pieces[slug]
            meta = json.load(open(os.path.join(ROOT, "shelf/sprites", f"{piece}.json")))
            mid = front_mid(o["y"])
            mm = overrides.get(slug) or longest_mm(p.get("notes"))
            s = (mm * ppmm) / max(meta["object"]) * float(o.get("scale", 1.0))

            sw, sh = meta["sprite"][0] * s, meta["sprite"][1] * s
            bx, by = meta["base"][0] * s, meta["base"][1] * s
            # Keep these in plate pixels; convert to percentages only when they
            # are written out. Mixing the two is what threw every label off.
            if o.get("flip"):
                bx = sw - bx                     # bx is already scaled; mirror it in the same units
            left_px = W * o["x"] - bx
            top_px = H * o["y"] - by + sink
            left, top = left_px / W * 100, top_px / H * 100

            sp = Image.open(os.path.join(ROOT, "shelf/sprites", f"{piece}.png")).convert("RGBA")
            if scene.get("tone_to_plate"):
                sp = tone_to(sp, plate_balance)
            if o.get("flip"):
                # Mirrored here rather than in CSS: scaleX(-1) gives the element a
                # negative-determinant matrix, which the browser decomposes into a
                # 180-degree rotation, so the hover transition span the piece round
                # instead of easing its scale.
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            tw = min(PIECE_W, sp.width)
            piece_path = os.path.join(OUT, f"piece-{slug}.webp")
            sp.resize((tw, max(1, round(sp.height * tw / sp.width))), Image.LANCZOS)\
              .save(piece_path, quality=88, method=6)
            piece_v = stamp(piece_path)

            # The card is positioned inside the piece element, so its offsets are
            # percentages of the SPRITE, not of the plate: drop from the object's
            # base by the shelf-front distance, and centre on the base, not on the
            # sprite (whose width includes the shadow and is off-centre).
            card_top = (mid * H - top_px) / sh * 100   # centred on the shelf front
            card_left = bx / sw * 100
            # Where the object actually meets the shelf, as a share of the sprite.
            # The sprite's own bottom is the far edge of its shadow, which is well
            # below the base — anchoring the light there put it under the shadow
            # rather than under the piece.
            base_x, base_y = bx / sw * 100, by / sh * 100
            obj_w = meta["object"][0] * s / sw * 100

            tilt = TILTS[len(marks) % len(TILTS)]
            carrier = CARRIERS[0]
            g = GEO[carrier]
            tone = o.get("tone") or {}
            if tone:
                tid = f"tone-{scene['id']}-{slug}"
                tone_defs.append(f'<filter id="{tid}" color-interpolation-filters="sRGB">'
                                 f'<feColorMatrix type="matrix" values="{tone_matrix(tone)}"/></filter>')
                tone_attr = f' style="filter:url(#{tid})"'
            else:
                tone_attr = ""
            marks.append(
                f'''      <a class="mark" href="/product/{slug}.html"
         aria-label="{html.escape(p['name'])}, view piece"
         data-scene="{scene['id']}" data-slug="{slug}"
         data-x="{o['x']}" data-y="{o['y']}" data-scale="{float(o.get('scale', 1.0))}"
         data-dx="{o.get('dx_px', 0)}"
         data-warmth="{tone.get('warmth', 0)}" data-bright="{tone.get('bright', 1)}"
         data-contrast="{tone.get('contrast', 1)}"
         style="left:{left:.4f}%;top:{top:.4f}%;width:{sw / W * 100:.4f}%;--bx:{base_x:.3f}%;--by:{base_y:.3f}%;--ow:{obj_w:.3f}%;--carrier:url(carrier-{carrier}.webp);--tilt:{tilt};--car-ar:{g['ar']:.4f};--paper-dx:{(g['cx'] - 0.5) * 8.80:.3f}em;--paper-dy:{(g['cy'] - 0.5) * 4.13:.3f}em;--paper-tilt:{g['tilt']}deg;--piece-dx:{o.get("dx_px", 0)}px">
        <img class="piece" src="piece-{slug}.webp?v={piece_v}" alt="{html.escape(p['name'])}" loading="lazy"{tone_attr}>
        <span class="card" style="top:{card_top:.4f}%;left:{card_left:.4f}%">
          <span class="ink">
            <span class="nm">{html.escape(p['name'])}</span>
            <span class="pr">{money(p.get('price'))}</span>
          </span>
        </span>
      </a>''')

        is_hero = si == 0
        scenes_html.append(
            f'''    <section class="scene{' hero' if is_hero else ''}{' inset' if scene.get('inset') else ''}">
      <img class="plate" src="{plate_name}?v={stamp(plate_path)}" alt=""{'' if is_hero else ' loading="lazy"'}>
{hero_copy if is_hero else ''}
{chr(10).join(marks)}
    </section>''')

    page = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shelf ⚚ Studio Maçon</title>
<meta name="description" content="Studio Maçon — cast bronze and silver, shelf concept.">
<link rel="icon" href="/assets/favicon.png">
<link rel="stylesheet" href="shelf.css?v={stamp(os.path.join(OUT, "shelf.css"))}">
</head><body class="intro">

  <div class="curtain" aria-hidden="true">
    <img src="/assets/goat-logo-warm.gif?v={_markv}" alt="">
  </div>

  <nav class="nav">
    <button class="menu" data-menu-toggle aria-label="Menu"><span class="bars"><i></i><i></i><i></i></span></button>
    <a class="logo" href="/index.html"><img src="/assets/goat-logo-warm.gif?v={_markv}" alt="Studio Maçon"></a>
    <a class="bag" href="/contact.html" aria-label="Bag">
      <svg class="urn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path class="lip" d="M8.4 2h7.2"/><path d="M10.3 2c.2 1.5.1 2.7-.2 3.6M13.7 2c-.2 1.5-.1 2.7.2 3.6"/><path d="M10.1 5.5C7.9 7.7 6.5 10.3 6.5 13.3c0 3.4 1.8 5.6 3.7 6.7M13.9 5.5c2.2 2.2 3.6 4.8 3.6 7.8 0 3.4-1.8 5.6-3.7 6.7"/><path d="M10.2 20.1h3.6M9.1 23.2h5.8"/><path d="M10.2 3.9C7.6 4.2 5.8 6.1 6.1 8.9M13.8 3.9c2.6.3 4.4 2.2 4.1 5"/></svg>
    </a>
  </nav>

  <div class="menu-overlay" role="dialog" aria-label="Menu">
    <a href="/index.html">Shop</a><a href="/story.html">Story</a><a href="/custom.html">Custom</a><a href="/shipping.html">Shipping &amp; Returns</a><a href="/contact.html">Contact</a>
  </div>

  <main>
{chr(10).join(scenes_html)}



<script>
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
window.scrollTo(0, 0);

document.querySelector('[data-menu-toggle]').addEventListener('click', function () {{
  document.body.classList.toggle('menu-open');
}});

// The logotype fades on scroll — but only once the opening has handed over to
// it. Setting opacity before then overrode the rule hiding it during the
// opening, so the logotype and the animated mark were on screen together.
(function () {{
  var copy = document.querySelector('.hero-copy'), hero = document.querySelector('.scene.hero');
  if (!copy || !hero) return;
  var armed = false, ticking = false;
  function place() {{
    ticking = false;
    if (!armed) return;
    var y = window.scrollY;
    copy.style.opacity = Math.max(0, 1 - y / (hero.offsetHeight * 0.22));
    hero.classList.toggle('pieces-in', y > 40);
  }}
  window.addEventListener('scroll', function () {{
    if (!ticking) {{ ticking = true; requestAnimationFrame(place); }}
  }}, {{passive: true}});
  // Type the line out after the logotype lands. The width is measured and fixed
  // first, so a centred line does not shuffle sideways as characters arrive.
  document.addEventListener('macon:introdone', function () {{
    var el = document.querySelector('.tagline');
    if (!el) return;
    var text = el.getAttribute('data-type') || '';
    // The bullet is set apart from the words, so it is written as its own element
    // as the line types rather than as a plain character.
    function render(n) {{
      var part = text.slice(0, n);
      el.innerHTML = part.split('\u2022').join('<span class="dot">\u2022</span>');
    }}
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{ render(text.length); return; }}
    // Reserve the finished line's box before typing. Clearing the text collapses
    // the element and lifts the logotype, which then drops again as it fills.
    render(text.length);
    var box = el.getBoundingClientRect();
    el.style.width = box.width + 'px';
    el.style.height = box.height + 'px';
    render(0);
    // starts a beat after the logotype has settled, and types unhurriedly
    // The line lands in two breaths: the phrase, a pause, then the place it is
    // made. Measured off the words rather than a fixed index so rewording the
    // tagline cannot put the pause mid-word.
    var PAUSE_AFTER = text.indexOf('Love');
    PAUSE_AFTER = PAUSE_AFTER < 0 ? -1 : PAUSE_AFTER + 4;
    setTimeout(function () {{
      var i = 0;
      (function tick() {{
        render(++i);
        if (i < text.length) setTimeout(tick, i === PAUSE_AFTER ? 1000 : 58);
      }})();
    }}, 400);
  }});

  document.addEventListener('macon:introdone', function () {{
    var skipped = document.body.classList.contains('intro-skipped');
    var arm = function () {{
      copy.style.transition = 'none';   // scroll drives opacity directly from here
      armed = true;
      place();
    }};
    if (skipped) arm(); else setTimeout(arm, 850);
  }});
}})();

// Replay the mark's blink on hover. The GIF is authored to play once, and
// nothing in CSS can rewind it — reassigning the source is what restarts it.
// The frames are already cached, so this costs no request.
(function () {{
  var img = document.querySelector('.nav .logo img');
  if (!img) return;
  // Alternating between two URLs is what forces the decoder to start over — a
  // fragment change is not reliable, and a fresh query each time would miss the
  // cache on every hover. Two URLs, both cached after first use.
  var base = img.getAttribute('src').split('#')[0], n = 0;
  document.querySelector('.nav .logo').addEventListener('mouseenter', function () {{
    n ^= 1;
    img.src = base + (base.indexOf('?') < 0 ? '?' : '&') + 'b=' + n;
  }});
}})();

// Nav is white over photography and ink once the Record is behind it.
(function () {{
  var nav = document.querySelector('.nav');
  function mark() {{ nav.classList.add('over-art'); }}   // the page is photography throughout
  mark();
  window.addEventListener('scroll', mark, {{passive: true}});
}})();

// Opening: the mark plays large and centred, fades out, then fades back in at
// nav size with the two icons following. Skipped entirely if motion is unwelcome.
(function () {{
  var body = document.body;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
    body.classList.remove('intro');
    document.dispatchEvent(new Event('macon:introdone'));
    return;
  }}
  // the mark's own animation runs 4.13s — let it finish before it fades
  var curtain = document.querySelector('.curtain'),
      mark = curtain && curtain.querySelector('img'),
      finished = false;

  // Hold the page still until the mark is actually on screen, so nobody scrolls
  // past it before it has appeared.
  var root = document.documentElement;
  root.style.overflow = 'hidden';
  setTimeout(function () {{ root.style.overflow = ''; }}, 780);

  function finish() {{
    if (finished) return;
    finished = true;
    clearTimeout(t1); clearTimeout(t2);
    body.classList.remove('intro');
    body.classList.add('intro-done');
    document.dispatchEvent(new Event('macon:introdone'));
  }}

  var t1 = setTimeout(function () {{ body.classList.add('intro-wipe'); }}, 4200);
  var t2 = setTimeout(finish, 4850);

  // Scrolling away during the opening dismisses the mark on the scroll itself,
  // rather than leaving it hanging there while the timers run out.
  window.addEventListener('scroll', function onEarly() {{
    if (finished) return;
    var y = window.scrollY;
    if (y <= 0) return;
    if (mark) mark.style.opacity = String(Math.max(0, 1 - y / 220));
    if (y > 200) {{
      window.removeEventListener('scroll', onEarly);
      // Scrolled away before the mark finished: the wordmark never gets its
      // entrance. Its opacity is handed straight to the scroll position, which
      // at this point is already zero.
      body.classList.add('intro-skipped');
      body.classList.add('intro-wipe');
      finish();
    }}
  }}, {{passive: true}});
}})();
</script>
''' + SHUFFLE.replace('__TONE_DEFS__', ''.join(tone_defs))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    n = sum(len(s["objects"]) for s in comp["scenes"])
    print(f"index.html — {len(comp['scenes'])} plates, {n} pieces as elements")


if __name__ == "__main__":
    main()
