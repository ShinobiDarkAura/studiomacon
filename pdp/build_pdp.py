#!/usr/bin/env python3
"""Build the Kindred Black-style product page preview, one page per piece.

    python3 pdp/build_pdp.py

Copy comes from the port's own product pages (the personal story), the Wix
export (the mythic lore line), and the port's notes (materials, dimensions).
Photographs come from Pieces Master in ~/Downloads and are copied into
pdp/img/<slug>/ so the preview never reaches outside the repo.
"""
import html, json, os, re, shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pdp")
MASTER = os.path.expanduser("~/Downloads/Maçon/Pieces Master")

EYEBROW = {
    "pip": "Tiny Keeper of Tenderness",
    "rebi": "A Silhouette in Flux",
    "ren": "Steward of Forgotten Paths",
    "zuma": "A Desert Spirit",
    "ori": "Guardian of Forests and Rivers",
    "yael": "Prophecy in Metal",
    "zuma-ring": "Sand Spirit, Distilled",
    "milo": "An Ancient Wanderer",
    "eclipse-ring": "Ellipses in Patient Equilibrium",
    "sietch-aperture": "Shelter Cut Into Rock",
    "lunar-canyon-ring": "Forged From a Distant Moon",
    "eleph": "Breath Suspended in Bronze",
    "wonderhorn-talisman": "A Horn for Undiscovered Chords",
    "macon-cap": "A Modicum of Solar Protection",
    "ibi": "The Eternal Watcher",
    "ear-cuff": "Perfect Geometries",
    "starshipkey-pendant": "A Device of Stellar Origin",
    "meridian-egg-ring": "Heavier Than It Looks",
}

# Pieces whose closing line says something other than "made to order".
MADE_LINE = {
    "eleph": "Cast only when someone asks. If that is you, write to us and we'll make one.",
    "ibi": "Cast on request. Write to us and we'll make one for you.",
    "macon-cap": "Made in small runs, with our mark on the front.",
}

# Hand-written story for the exemplar; every other piece uses its Wix lore line.
LORE = {
    "wonderhorn-talisman": "In the story Hannah grew up with, a girl named Ida plays her wonder horn so sweetly that the goblins who stole her sister cannot help but dance — faster and faster, until they dance themselves clean out of the window and away. We can't promise goblins. We can promise every horn is made with that much love.",
}

TODO = '<span class="todo">{}</span>'


def kind(slug, notes):
    if slug == "macon-cap":
        return "apparel"
    if "bronze" in " ".join(notes).lower():
        return "totem"
    if slug.endswith("ring"):
        return "ring"
    if "chain" in " ".join(notes).lower():
        return "pendant"
    return "jewellery"


def read_port(slug):
    t = open(os.path.join(ROOT, "product", f"{slug}.html"), encoding="utf-8").read()
    desc = html.unescape(re.search(r'<div class="desc">(.*?)</div>', t, re.S).group(1)).strip()
    notes = [html.unescape(re.sub("<[^>]+>", "", x)).strip()
             for x in re.findall(r'<div class="row">(.*?)</div>', t, re.S)]
    return desc, notes


def lore_line(wix):
    """The Wix copy is two mythic sentences and then a practical one; keep the myth."""
    wix = html.unescape(wix)
    cut = re.split(r"\s(?:Each (?:totem|piece) is made to order|\w+ is currently on preorder)", wix)[0]
    return cut.strip()


def photos(slug, k):
    base = os.path.join(MASTER, "apparel" if k == "apparel" else ("totems" if k == "totem" else "jewellery"))
    def pick(sub):
        d = os.path.join(base, sub)
        return sorted(os.path.join(d, f) for f in os.listdir(d)
                      if f.split("--")[0].split(".")[0] == slug) if os.path.isdir(d) else []
    return pick("plain"), pick("in-hand"), pick("drawn-charcoal")


def export(src, slug, name, width):
    d = os.path.join(OUT, "img", slug)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, name + ".jpg")
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        im = Image.open(src).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(dst, quality=88)
    return f"img/{slug}/{name}.jpg"


def accordions(slug, k, notes):
    mat = notes[0] if notes else TODO.format("materials to confirm")
    dims = next((n for n in notes if re.search(r"\d+\s*x\s*\d+", n)), None)
    chain = re.search(r'(\d+)"\s*chain', " ".join(notes), re.I)

    care = {
        "totem": "<p>Bronze is meant to be handled. The patina darkens where your thumb sits and brightens where it rubs, so over time it records how you hold it.</p><p>To keep the surface as it is, wipe it with a soft dry cloth. Avoid polish; it takes the patina with it.</p>",
        "ring": "<p>Sterling silver darkens with time and air. Wear it often and it stays bright; bring back the shine with a soft polishing cloth.</p><p>Take it off to swim or clean, and store it on its own so it stays unscratched.</p>",
        "pendant": "<p>Worn long, it rests just below the breastbone and turns with you as you move.</p><p>Sterling silver darkens with time and air. Wear it often and it stays bright, or bring back the shine with a soft polishing cloth. Take it off to swim.</p>",
        "jewellery": "<p>Sterling silver darkens with time and air. Wear it often and it stays bright; bring back the shine with a soft polishing cloth. Take it off to swim.</p>",
        "apparel": "<p>Hand wash cold and reshape while damp. Dry flat, out of direct sun.</p>",
    }[k]

    rows = []
    if dims:
        rows.append(("Dimensions", dims.replace(" x ", " × ")))
    if chain:
        rows.append(("Chain", f"{chain.group(1)} inches"))
    if k == "ring":
        rows.append(("Size", TODO.format("size range to confirm")))
    if k in ("pendant", "ring", "jewellery") and not dims:
        rows.append(("Dimensions", TODO.format("to confirm")))
    if k == "apparel":
        rows.append(("Fit", TODO.format("to confirm")))
    sizing = "<dl>" + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in rows) + "</dl>"

    items = [
        ("Care" if k in ("totem", "apparel") else "Wearing &amp; Care", care),
        ("Materials", f"<p>{html.escape(mat)}</p>"),
        ("Sizing &amp; Info", sizing),
    ]
    if k != "apparel":
        items.append(("Resizing &amp; Repair",
                      '<p>If your piece takes a knock or needs adjusting, write to '
                      '<a href="mailto:hello@studiomacon.co">hello@studiomacon.co</a> and '
                      + TODO.format("we'll look after it") + ".</p>"))
    items.append(("Shipping &amp; Returns",
                  "<p>Each piece is made to order. Please allow up to 10 business days for us to make yours before it heads out to you. Standard shipping takes 3–7 business days; international shipping generally takes 5–10.</p>"
                  "<p>We accept pieces (excluding custom work) in their original condition for store credit toward your next purchase, within 14 days of delivery. If a piece doesn't fit, we'll gladly work with you to find the right size. "
                  '<a href="mailto:hello@studiomacon.co?subject=Starting%20a%20return">Contact us</a> to begin.</p>'))
    return "\n".join(
        f'''        <div class="acc-item">
          <button class="acc-head" aria-expanded="false">{t}</button>
          <div class="acc-panel"><div class="acc-inner"><div class="acc-body">{b}</div></div></div>
        </div>''' for t, b in items)


def page(p, template):
    slug, name, price = p["slug"], p["name"], p["price"]
    desc, notes = read_port(slug)
    k = kind(slug, notes)
    plain, hand, drawn = photos(slug, k)

    hero_src = os.path.join(OUT, "img", "wonderhorn-hero-src.jpg") if slug == "wonderhorn-talisman" else (plain[0] if plain else hand[0])
    hero = export(hero_src, slug, "hero", 1600)
    gallery = [export(f, slug, f"plain-{i}", 1800) for i, f in enumerate(plain[1 if slug != "wonderhorn-talisman" else 0:], 1)]
    gallery += [export(f, slug, f"hand-{i}", 1600) for i, f in enumerate(hand, 1)]
    drawing = export(drawn[0], slug, "drawing", 900) if drawn else None

    # three large images close the page, separating the two text chunks
    # drawing first, then a hand shot and the first plain shot — the two ends of
    # the gallery, which are least likely to be near-duplicates of each other
    hands = [g for g in gallery if "/hand-" in g]
    plains = [g for g in gallery if "/plain-" in g]
    closing = [x for x in [drawing, hands[0] if hands else None, plains[0] if plains else None,
                           hero, *gallery] if x]
    closing = list(dict.fromkeys(closing))[:3]

    lore = LORE.get(slug) or lore_line(p["desc"])
    made = MADE_LINE.get(slug, "Made to order. Please allow up to two weeks for us to make yours.")

    def pic(src, cls=""):
        return f'<figure class="big{cls}"><img src="{src}" alt="" loading="lazy"></figure>'

    close = pic(closing[0], " drawing" if closing[0] == drawing else "")
    close += f'\n    <p class="chunk">{html.escape(lore)}</p>\n    '
    close += pic(closing[1]) if len(closing) > 1 else ""
    close += f'\n    <p class="chunk">{html.escape(made)}</p>\n    '
    close += pic(closing[2]) if len(closing) > 2 else ""

    size_select = ""
    if k == "ring":
        size_select = ('<label class="size"><span>Size</span><select><option>Select size</option>'
                       + "".join(f"<option>{s}</option>" for s in
                                 ["4", "4.5", "5", "5.5", "6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11"])
                       + "</select></label>")

    return (template
            .replace("{{TITLE}}", html.escape(name))
            .replace("{{EYEBROW}}", html.escape(EYEBROW[slug]))
            .replace("{{PRICE}}", f"${price}")
            .replace("{{DESC}}", html.escape(desc))
            .replace("{{SIZE}}", size_select)
            .replace("{{HERO}}", hero)
            .replace("{{GALLERY}}", "\n      ".join(
                f'<figure><img src="{g}" alt="" loading="lazy"></figure>' for g in gallery))
            .replace("{{ACCORDIONS}}", accordions(slug, k, notes))
            .replace("{{CLOSING}}", close))


def main():
    products = json.load(open(os.path.join(ROOT, "_source/products.json")))
    template = open(os.path.join(OUT, "template.html"), encoding="utf-8").read()
    links = []
    for p in products:
        open(os.path.join(OUT, f"{p['slug']}.html"), "w", encoding="utf-8").write(page(p, template))
        links.append(f'<li><a href="{p["slug"]}.html">{html.escape(p["name"])}</a> <span>${p["price"]}</span></li>')
        print("  ", p["slug"])
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>Product pages · preview</title>'
        '<style>body{font:17px/1.8 "Helvetica Neue",Arial,sans-serif;margin:60px}a{color:#111}span{color:#888}</style>'
        "<h1>Product pages</h1><ul>" + "".join(links) + "</ul>")
    print(f"{len(products)} pages")


if __name__ == "__main__":
    main()
