#!/usr/bin/env python3
"""Emit the shelf page: scenes, labels, hotspots, nav, index.

Positions come from the same composition file the images were rendered from, so a
label can never drift away from the piece it names — move a piece and its label
and its click target move with it.

    python3 shelf/tools/build_shelf.py
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "_site")


def money(v):
    return f"${float(v):,.0f}" if v else ""


def main():
    comp = json.load(open(os.path.join(ROOT, "shelf/composition-dressed.json"), encoding="utf-8"))
    pieces = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
    cache = json.load(open(os.path.join(ROOT, "_source/content-cache.json"), encoding="utf-8"))
    prod = {p["slug"]: p for p in cache["products"]}
    excl = set(pieces.get("_shelf_exclude", {}))

    tagline = next((x["value"] for x in cache.get("settings", []) if x["key"] == "tagline"), "")

    hero_copy = f'''
      <div class="hero-copy">
        <p class="eyebrow">Studio Ma&ccedil;on</p>
        <h1>Cast by hand, one at a time</h1>
        <p class="lede">{html.escape(tagline)}</p>
      </div>'''

    scenes_html = []
    for si, scene in enumerate(comp["scenes"]):
        marks = []
        # Labels sit on the shelf's front face, below the surface the piece stands
        # on, the way a museum card is fixed to the shelf edge rather than floating.
        dy = scene.get("label_dy", 0.045)
        for o in scene["objects"]:
            p = prod[o["slug"]]
            # Label sits just under the piece on the shelf, the way a museum card does.
            marks.append(
                f'''      <a class="mark" style="left:{o['x']*100:.3f}%;top:{(o['y']+dy)*100:.3f}%"
         href="/product/{o['slug']}.html" aria-label="{html.escape(p['name'])}, view piece">
        <span class="hit" style="height:{dy*100:.2f}vw"></span>
        <span class="card"><span class="nm">{html.escape(p['name'])}</span>'''
                f'''<span class="pr">{money(p.get('price'))}</span></span>
      </a>''')
        # The first scene is the hero: full viewport, title centred over it. It is
        # cropped to fill, which would drag any label off its piece — so it carries
        # none, and its pieces live on the shelves below.
        is_hero = si == 0
        scenes_html.append(
            f'''    <section class="scene{' hero' if is_hero else ''}">
      <img src="scene-{scene['id']}.jpg" alt=""{'' if is_hero else ' loading="lazy"'}>
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
<link rel="stylesheet" href="shelf.css">
</head><body>

  <nav class="nav">
    <svg class="urn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M8 3h8M9 3c0 2 1 3 3 3s3-1 3-3M7 8c0-1.5 2-2 5-2s5 .5 5 2c0 5-2 8-5 12-3-4-5-7-5-12Z"/></svg>
    <a class="logo" href="/index.html"><img src="/assets/goat-logo.gif" alt="Studio Maçon"></a>
    <button class="menu" data-menu-toggle aria-label="Menu"><span class="bars"><i></i><i></i><i></i></span></button>
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

  <footer>
    <div class="fine">HANDMADE IN L.A.</div>
  </footer>

<script>
document.querySelector('[data-menu-toggle]').addEventListener('click', function () {{
  document.body.classList.toggle('menu-open');
}});
// The nav sits on cream over the hero and on photography below it.
(function () {{
  var nav = document.querySelector('.nav'), rec = document.querySelector('.index');
  function mark() {{
    // white while the nav is over photography, ink once the Record is behind it
    nav.classList.toggle('over-art', window.scrollY + 80 < rec.offsetTop);
  }}
  mark();
  window.addEventListener('scroll', mark, {{passive: true}});
}})();
</script>
</body></html>
'''
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    n = sum(len(s["objects"]) for s in comp["scenes"])
    print(f"index.html — {len(comp['scenes'])} scenes, {n} labelled pieces, {len(live)} in the record")


if __name__ == "__main__":
    main()
