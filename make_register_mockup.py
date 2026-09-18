#!/usr/bin/env python3
"""Build register-mockup.html — a standalone preview of the Register concept.

Not wired into the site. Uses the whole real catalogue, grouped by type, with a
few pieces cast as singular/claimed so every state is visible.
"""
import json, os, html, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
src = open("build.py", encoding="utf-8").read().split('if __name__ == "__main__":')[0]
B = {"__file__": os.path.abspath("build.py")}
sys.argv = ["build.py", "--offline"]
exec(compile(src, "build.py", "exec"), B)

data = json.load(open("_source/content-cache.json", encoding="utf-8"))
products = {p["slug"]: p for p in data["products"]}
settings = {s["key"]: s["value"] for s in data["settings"]}

# cast a few pieces so the mockup shows singular + claimed states
ENTRIES = {"starshipkey-pendant": "0001", "wonderhorn-talisman": "0002"}
CLAIMED = {"meridian-egg-ring": "0003"}

# the register runs in one sequence; entries punctuate the editions
# perennial editions lead the register; the singular entries follow
ORDER = ["pip", "rebi", "ren", "zuma", "ori", "yael", "milo", "eleph", "ibi",
         "zuma-ring", "eclipse-ring", "sietch-aperture", "lunar-canyon-ring",
         "ear-cuff", "macon-cap",
         "starshipkey-pendant", "wonderhorn-talisman", "meridian-egg-ring"]

def imgs(slug): return B["images_for"](products[slug])

PLACEMENTS = ["seal-tr", "seal-bl", "seal-tl", "seal-br"]
_placed = {"n": 0}

def entry_card(slug, num, claimed=False):
    p, im = products[slug], imgs(slug)
    lead = im[0]; alt = im[1] if len(im) > 1 else None
    stamp = "stamp-3-claimed-flooded-vermilion.png" if claimed else "stamp-2-seal-aniline.png"
    place = PLACEMENTS[_placed["n"] % len(PLACEMENTS)]
    _placed["n"] += 1
    price = f"${float(p['price']):,.0f}" if p.get("price") else ""
    altimg = f'<img class="ci-alt" src="{alt["card"]}" alt="">' if alt else ""
    return f'''      <a class="entry{' is-claimed' if claimed else ''}" href="product/{slug}.html">
        <div class="entry-figure">
          <div class="entry-img">
            <img class="ci-lead" src="{lead["hero"]}" alt="{html.escape(p["name"])}">{altimg}
          </div>
          <img class="entry-seal {place}" src="assets/register/{stamp}" alt="">
        </div>
        <div class="entry-meta">
          <div class="entry-name">{html.escape(p["name"])}</div>
          <div class="entry-mark">
            <span class="entry-price">{price}</span>
            <span class="overline">{"Claimed" if claimed else "One of One"} &middot; &#8470;&nbsp;{num}</span>
          </div>
        </div>
      </a>'''

# two proportions only — enough rhythm to avoid a lattice, not so much it reads untidy
SHAPES = ["ed-tall", "ed-tall", "ed-square", "ed-tall", "ed-square", "ed-tall"]
_shaped = {"n": 0}

def edition_card(slug):
    p, im = products[slug], imgs(slug)
    shape = SHAPES[_shaped["n"] % len(SHAPES)]
    _shaped["n"] += 1
    lead = im[0]; alt = im[1] if len(im) > 1 else None
    price = f"${float(p['price']):,.0f}" if p.get("price") else ""
    altimg = f'<img class="ci-alt" src="{alt["card"]}" alt="">' if alt else ""
    return f'''      <a class="edition {shape}" href="product/{slug}.html">
        <div class="ed-img"><img class="ci-lead" src="{lead["card"]}" alt="{html.escape(p["name"])}">{altimg}</div>
        <div class="ed-name">{html.escape(p["name"])}</div>
        <div class="ed-price">{price}</div>
      </a>'''

cells = []
for slug in ORDER:
    if slug not in products:
        continue
    if slug in CLAIMED:   cells.append(entry_card(slug, CLAIMED[slug], claimed=True))
    elif slug in ENTRIES: cells.append(entry_card(slug, ENTRIES[slug]))
    else:                 cells.append(edition_card(slug))

register = ('  <section class="reg-group">\n    <div class="reg-grid">\n'
            + chr(10).join(cells) + '\n    </div>\n  </section>')

hero = B["derive"](settings.get("hero_image", "assets/hero.png"), 1800)
body = (f'''  <section class="reg-hero">
    <img class="hero-art" src="{hero}" alt="Maçon" fetchpriority="high">
  </section>
''' + register + '''
  <section class="reg-foot">
    <img src="assets/register/stamp-5-edition-mark-green.png" alt="">
    <p>Pieces marked <strong>&#8470;</strong> are one of one. Once claimed they remain in the
       register, struck through, as a record of where they went.</p>
  </section>''')

open("register-mockup.html", "w", encoding="utf-8").write(
    B["page"]("The Register ⚚ Studio Maçon", body, "",
              "A mockup of the Maçon register — singular entries and editions in one record."))
print(f"wrote register-mockup.html — {len(cells)} products in one register")
