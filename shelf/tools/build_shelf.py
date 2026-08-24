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
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "_site")
PIECE_W = 320          # plenty: pieces display around 90-180px


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


def main():
    comp = json.load(open(os.path.join(ROOT, "shelf/composition-dressed.json"), encoding="utf-8"))
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
    prod = {p["slug"]: p for p in cache["products"]}
    overrides = comp.get("mm", {})
    tagline = next((x["value"] for x in cache.get("settings", []) if x["key"] == "tagline"), "")
    os.makedirs(OUT, exist_ok=True)

    hero_copy = f'''
      <div class="hero-copy">
        <!-- Replaced by the logotype; kept in case the wording is wanted back.
        <p class="eyebrow">Studio Ma&ccedil;on</p>
        <h1>Cast by hand, one at a time</h1>
        -->
        <img class="logotype" src="logotype.png?v={stamp(os.path.join(OUT, "logotype.png"))}" alt="Studio Ma&ccedil;on">
        <!-- <p class="lede">{html.escape(tagline)}</p> -->
      </div>'''

    scenes_html = []
    for si, scene in enumerate(comp["scenes"]):
        plate_src = os.path.join(ROOT, scene["plate"])
        plate = Image.open(plate_src)
        W, H = plate.size
        plate_name = f"plate-{scene['id']}.jpg"
        plate_path = os.path.join(OUT, plate_name)
        plate.convert("RGB").save(plate_path, quality=90)

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
            left_px = W * o["x"] - bx
            top_px = H * o["y"] - by + sink
            left, top = left_px / W * 100, top_px / H * 100

            sp = Image.open(os.path.join(ROOT, "shelf/sprites", f"{piece}.png")).convert("RGBA")
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

            marks.append(
                f'''      <a class="mark" href="/product/{slug}.html"
         aria-label="{html.escape(p['name'])}, view piece"
         style="left:{left:.4f}%;top:{top:.4f}%;width:{sw / W * 100:.4f}%">
        <img class="piece" src="piece-{slug}.webp?v={piece_v}" alt="{html.escape(p['name'])}" loading="lazy">
        <span class="card" style="top:{card_top:.4f}%;left:{card_left:.4f}%">
          <span class="nm">{html.escape(p['name'])}</span>
          <span class="pr">{money(p.get('price'))}</span>
        </span>
      </a>''')

        is_hero = si == 0
        scenes_html.append(
            f'''    <section class="scene{' hero' if is_hero else ''}">
      <img class="plate" src="{plate_name}?v={stamp(plate_path)}" alt=""{'' if is_hero else ' loading="lazy"'}>
{hero_copy if is_hero else ''}
{chr(10).join(marks)}
    </section>''')

    live = [p for p in cache["products"] if p.get("status") == "live"]
    index_rows = "".join(
        f'''        <a class="row" href="/product/{p['slug']}.html">
          <span class="n">{html.escape(p['name'])}</span>
          <span class="m">{html.escape((p.get('notes') or [''])[0])}</span>
          <span class="p">{money(p.get('price'))}</span>
        </a>\n''' for p in live)

    page = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shelf ⚚ Studio Maçon</title>
<meta name="description" content="Studio Maçon — cast bronze and silver, shelf concept.">
<link rel="icon" href="/assets/favicon.png">
<link rel="stylesheet" href="shelf.css?v={stamp(os.path.join(OUT, "shelf.css"))}">
</head><body class="intro">

  <div class="curtain" aria-hidden="true">
    <img src="/assets/goat-logo.gif" alt="">
  </div>

  <nav class="nav">
    <button class="menu" data-menu-toggle aria-label="Menu"><span class="bars"><i></i><i></i><i></i></span></button>
    <a class="logo" href="/index.html"><img src="/assets/goat-logo.gif" alt="Studio Maçon"></a>
    <a class="bag" href="/contact.html" aria-label="Bag">
      <svg class="urn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M8 3h8M9 3c0 2 1 3 3 3s3-1 3-3M7 8c0-1.5 2-2 5-2s5 .5 5 2c0 5-2 8-5 12-3-4-5-7-5-12Z"/></svg>
    </a>
  </nav>

  <div class="menu-overlay" role="dialog" aria-label="Menu">
    <a href="/index.html">Shop</a><a href="/story.html">Story</a><a href="/custom.html">Custom</a><a href="/shipping.html">Shipping &amp; Returns</a><a href="/contact.html">Contact</a>
  </div>

  <main>
{chr(10).join(scenes_html)}

    <section class="index">
      <h2>The Record</h2>
      <div class="rows">
{index_rows}      </div>
    </section>
  </main>

  <footer><div class="fine">HANDMADE IN L.A.</div></footer>

<script>
document.querySelector('[data-menu-toggle]').addEventListener('click', function () {{
  document.body.classList.toggle('menu-open');
}});

// The logotype fades the moment scrolling starts; opacity is tied straight to
// scroll position, with no movement of its own.
(function () {{
  var copy = document.querySelector('.hero-copy'), hero = document.querySelector('.scene.hero');
  if (!copy || !hero) return;
  var ticking = false;
  function place() {{
    var span = hero.offsetHeight * 0.45;
    copy.style.opacity = Math.max(0, 1 - window.scrollY / span);
    ticking = false;
  }}
  window.addEventListener('scroll', function () {{
    if (!ticking) {{ ticking = true; requestAnimationFrame(place); }}
  }}, {{passive: true}});
  place();
}})();

// Nav is white over photography and ink once the Record is behind it.
(function () {{
  var nav = document.querySelector('.nav'), rec = document.querySelector('.index');
  function mark() {{ nav.classList.toggle('over-art', window.scrollY + 80 < rec.offsetTop); }}
  mark();
  window.addEventListener('scroll', mark, {{passive: true}});
}})();

// Opening: the mark plays large and centred, fades out, then fades back in at
// nav size with the two icons following. Skipped entirely if motion is unwelcome.
(function () {{
  var body = document.body;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
    body.classList.remove('intro'); return;
  }}
  // the mark's own animation runs 4.13s — let it finish before it fades
  setTimeout(function () {{ body.classList.add('intro-wipe'); }}, 4200);
  setTimeout(function () {{ body.classList.remove('intro'); body.classList.add('intro-done'); }}, 4850);
}})();
</script>
</body></html>
'''
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    n = sum(len(s["objects"]) for s in comp["scenes"])
    print(f"index.html — {len(comp['scenes'])} plates, {n} pieces as elements, {len(live)} in the record")


if __name__ == "__main__":
    main()
