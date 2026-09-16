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

# The two centred blocks at the bottom of each page — at least 30 words each.
# First: the lore, grown from the Wix line. Second: how it comes to you.
LORE = {
    "pip": "Tiny keeper of tenderness. Proximity induces unexpected comfort, and scholars remain blissfully baffled as to why. Kept in a pocket, Pip has been known to settle a racing heart and soften the edges of a long, difficult day.",
    "rebi": "Exhibits fluid properties; the perceived silhouette is always in flux. Researchers report heightened reflexes after handling. Turn Rebi in the light and a hare becomes something else entirely, and the animal you find is usually the one you needed.",
    "ren": "Steward of forgotten paths. Dawn light lingers unusually long upon the golden mane. Ren is said to know the way back through any wood, and to carry whoever holds it a little further than they meant to go.",
    "zuma": "A desert spirit, present and patient. Its namesake ring awakens a dormant essence, and ancient runes suggest a sacred link between the two. Zuma keeps the warmth of a long afternoon in the sand, long after the sun has gone down.",
    "ori": "Faithful guardian of the forests and rivers. A subtle warmth radiates from Ori during the winter solstice. Set on a windowsill, it keeps watch over the house through the long nights, asking nothing in return but the occasional hand.",
    "yael": "Inimitable poise suggests prophecy in metal. Mountaintop altar bells are said to resonate in its presence. Yaël stands where the footing is narrowest and the air is thinnest, and seems entirely unbothered by either, which is the whole lesson.",
    "zuma-ring": "Sand spirit, distilled to a sacred heirloom. Unearthed glyphs show evidence of rituals performed with its paired totem. Worn on the hand, the Zuma Ring carries a small piece of the desert with you, warm and quiet and very old.",
    "milo": "An ancient wanderer, seeking home. The surface adapts to its handler, and the bond deepens with patina over time. Milo has crossed a great deal of country to reach you, and seems glad, in its quiet way, to finally stop moving.",
    "eclipse-ring": "Asymmetric ellipses, locked in patient equilibrium. The space between them holds questions only the stars can answer. Two shapes that never quite match, held at exactly the distance where they stop competing and begin, very quietly, to belong together.",
    "sietch-aperture": "Recovered from the wake of a passing comet. The aperture reveals an oscillating presence of landscapes that appear on no map. Hold it to your eye and look through; what you see on the other side is yours to keep secret.",
    "lunar-canyon-ring": "A sundered artifact, forged from the core of a distant moon. Social gatherings reportedly ebb and flow in time with the wearer's presence. The folds of white rock are cool to the touch, and warm slowly, the way moonlight does.",
    "eleph": "Breath suspended in solid bronze. Distant trumpeting has been reported by independent observers, usually late at night and always just out of sight. Eleph remembers everything, and forgives most of it, and asks only to be held now and then.",
    "wonderhorn-talisman": "In the story Hannah grew up with, a girl named Ida plays her wonder horn so sweetly that the goblins who stole her sister cannot help but dance, faster and faster, until they dance themselves clean out of the window and away.",
    "macon-cap": "A tasteful cap adorned with a mystic symbol. It offers a modicum of protection from the sun, and a considerable amount of protection from people who might otherwise ask what you've been making lately. Wear it to the studio, or anywhere.",
    "ibi": "The eternal watcher, believed to guard ancestral secrets. Every attempt to transmit its likeness has been met with lens fog. Ibi does not photograph well because it would rather be held than looked at, and it makes no apology for that.",
    "ear-cuff": "Perfect geometries betray a cosmic provenance. Light fractures into otherworldly spectra across the mirrored edge. The Caldera Arc follows the rim of a volcano, a long drop on one side the whole way round, held gently against the curve of the ear.",
    "starshipkey-pendant": "An elegant device of stellar origin. Prolonged exposure is known to cause wanderlust, and researchers who study it tend to forget to come back. Worn close, the Starship Key seems to hum faintly whenever the night sky is especially clear.",
    "meridian-egg-ring": "Its weight exceeds every material expectation. Metaphysical analysis detects an abyss gazing back. Everyone who picks up the Meridian Egg says the same thing about how heavy it is, and then, a moment later, quietly declines to put it down.",
}

MADE = ("Every piece is made to order in our studio. Each begins as a sketch, is carved by hand in wax, "
        "and is cast at a local foundry before we refine and polish it. Please allow up to two weeks for us to make yours.")
MADE_LINE = {
    "eleph": "We love Eleph, though it rarely sells, so it is cast only when someone asks for one. If that is you, write to us, and we will carve, cast and polish yours by hand in our studio, just for you.",
    "ibi": "Ibi is cast on request rather than kept in stock. Write to us and we will make one for you by hand, carved in wax, cast at a local foundry, and refined and polished in our studio before it comes to you.",
    "macon-cap": "We made these because we each wanted one, with our mark on the front and a little shade for long days outside. They are made in small runs, so when a colour is gone, it may be gone for a while.",
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
    if k != "apparel":
        sizing += ('<p class="after-dl">If your piece needs resizing, takes a knock, or needs adjusting, write to '
                   '<a href="mailto:hello@studiomacon.co">hello@studiomacon.co</a> and '
                   + TODO.format("we'll look after it") + ".</p>")

    items = [
        ("Care" if k in ("totem", "apparel") else "Wearing &amp; Care", care),
        ("Materials", f"<p>{html.escape(mat)}</p>"),
        ("Sizing &amp; Info", sizing),
    ]
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

    lore = LORE[slug]
    made = MADE_LINE.get(slug, MADE)
    for block in (lore, made):
        assert len(block.split()) >= 30, (slug, len(block.split()))

    ph = '<div class="big" role="presentation"></div>'
    close = f'{ph}\n    <p class="chunk">{html.escape(lore)}</p>\n    {ph}\n    <p class="chunk">{html.escape(made)}</p>\n    {ph}'

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
