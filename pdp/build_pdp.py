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

# The description under the price. Third person throughout, in the Kindred
# Black manner: the object, its material and making, then its lore.
DESC = {
    "pip": "A tiny keeper of tenderness, cast in solid bronze with an ombré patina. Its form recalls an old cast iron piggy bank. Proximity induces unexpected comfort; scholars remain blissfully baffled. Its patina is built up slowly by hand and deepens wherever the thumb rests.",
    "rebi": "A small totem of solid bronze, finished with an ombré patina. Its form is a hare from some angles and something else entirely from others. Handling is known to heighten the reflexes; owners report catching things before they fall. Each shifting plane is refined by hand after casting.",
    "ren": "A steward of forgotten paths, cast in solid bronze. Its form recalls a painted Swedish horse. Dawn light is known to linger on its golden mane; hikers report arriving home earlier than expected. The mane is polished bright by hand while the body is left to darken.",
    "zuma": "A desert spirit in solid bronze, small enough for a coat pocket. Its form was drawn alongside its namesake ring. Ancient runes suggest a sacred link between the two; kept apart, both are said to grow restless. Its sand-worn surface is filed and patinated by hand.",
    "ori": "A faithful guardian of forests and rivers, cast in solid bronze. Its form recalls a bear, with no claws and barely a snout. A subtle warmth radiates from it each winter solstice; keepers report fewer drafts. Its broad planes are smoothed and patinated slowly by hand.",
    "yael": "An ibex of solid bronze, poised as if in prophecy. Its form recalls the narrow ledges of high mountains. Altar bells are known to resonate in its presence; neighbors report faint chimes at dusk. Its slender horns are refined patiently by hand after casting.",
    "zuma-ring": "A band of distilled sand spirit, cast in sterling silver. Its form repeats the shoulder line of the Zuma totem. Unearthed glyphs show evidence of rituals performed with its pair; wearers report an urge to walk barefoot. Each band is sized and polished by hand after casting.",
    "milo": "An ancient wanderer seeking home, cast in solid bronze with an ombré patina. Its form was the first made to embody the Maçon mark. Its surface adapts to whoever holds it; the bond deepens with every season. Each Milo is worked by hand until its surface turns quiet.",
    "eclipse-ring": "Two asymmetric ellipses, cast in sterling silver. Its form holds both shapes at the exact distance where they stop competing. The space between is said to hold questions only stars can answer; astronomers decline to comment. Each ring is balanced and polished by hand after casting.",
    "sietch-aperture": "A ring recovered from the wake of a passing comet, cast in sterling silver. Its form recalls a shelter cut deep into desert rock. Its aperture reveals landscapes that appear on no map; cartographers have stopped asking. The opening is polished by hand from the inside out.",
    "lunar-canyon-ring": "A sundered artifact forged from the core of a distant moon, cast in sterling silver. Its form recalls a canyon of white folded rock. Social gatherings ebb and flow with the wearer's presence; hosts plan accordingly. Every fold is brought to a soft polish by hand.",
    "eleph": "Breath suspended in solid bronze, finished with an ombré patina. Its form recalls a small elephant at rest. Distant trumpeting has been reported by independent observers, always just out of sight. Each Eleph is cast on request and finished entirely by hand.",
    "wonderhorn-talisman": "A spiral resonator in sterling silver, worn on a thirty inch chain. Its form recalls the horn Ida played until the goblins danced out the window. Nearby children develop perfect pitch; lab equipment vibrates sympathetically. Its inner curl is filed and polished slowly by hand.",
    "macon-cap": "A tasteful cap adorned with a mystic symbol. Its front carries the Maçon mark. It offers a modicum of solar protection; wearers report being asked where they found it. Each cap is checked by hand before it ships.",
    "ibi": "An eternal watcher believed to guard ancestral secrets, cast in solid bronze. Its form keeps a long and patient watch. Attempts to transmit its likeness are met with lens fog; photographers blame the weather. Each Ibi is cast on request and patinated by hand.",
    "ear-cuff": "An ear cuff of perfect geometries, cast in sterling silver. Its form recalls the rim of a volcanic caldera. Light fractures into otherworldly spectra across its mirrored edge; no piercing is required. Its edge is polished and shaped by hand to hold the ear securely.",
    "starshipkey-pendant": "An elegant device of stellar origin, cast in sterling silver and worn on a thirty inch chain. Its form recalls a chrome starship. Prolonged exposure is known to cause wanderlust; researchers studying it take long sabbaticals abroad. Its hyper-reflective hull is polished meticulously by hand after casting.",
    "meridian-egg-ring": "A ring of improbable density, cast in sterling silver. Its form recalls a smooth and weighted egg. Its weight exceeds every material expectation; metaphysical analysis detects an abyss gazing back. Each ring is hand polished and sized to order.",
}

# The two centred blocks at the bottom of each page — at least 30 words each.
# First: the lore, grown from the Wix line. Second: how it comes to you.
LORE = {
    "pip": "Pip spent its early years on a windowsill, keeping watch over whoever needed it most. Visitors tend to pick it up without asking and put it down reluctantly. Those who carry it report calmer mornings, and a curious habit of checking their pockets.",
    "rebi": "Rebi has never looked the same way twice in the same light. Some see a hare, some a fox, and a few insist it is something with no name at all. Each is right, and Rebi seems quietly pleased by the disagreement.",
    "ren": "Ren knows the way through any wood, including the ones that no longer appear on maps. Its golden mane catches the first light of the day and holds it far longer than it should. Travellers who keep it close rarely take a wrong turn.",
    "zuma": "Zuma carries the stillness of the desert at noon, when even the wind stops to rest. Kept in a pocket, it warms slowly and holds that warmth well into the evening. Paired with its ring, it is said to remember the way home across the sand.",
    "ori": "Ori keeps a patient watch over forests, rivers and the households that take it in. It asks for very little beyond a windowsill and the occasional hand. In the depths of winter, keepers swear the room feels a degree or two warmer.",
    "yael": "Yaël stands where the footing is narrowest and the air is thinnest, entirely unbothered by either. Those who keep it close tend to find their balance in unlikely places. At dusk, a faint ringing is sometimes heard, like bells from a very distant mountain.",
    "zuma-ring": "The Zuma Ring carries a small piece of the desert wherever it is worn. Unearthed glyphs suggest it was once exchanged between travellers crossing the same stretch of sand. Wearers report an unexpected fondness for long walks, wide horizons and very quiet afternoons.",
    "milo": "Milo has crossed a great deal of country to arrive here, and seems glad, in its quiet way, to finally stop moving. Its surface takes on the character of whoever holds it most. Over the years, the two tend to grow alike.",
    "eclipse-ring": "The Eclipse Ring holds two shapes that never quite match, and never quite need to. Between them sits a small, bright space that seems to change with the hour. Astronomers have been asked what it means, and each has politely declined to guess.",
    "sietch-aperture": "The Sietch Ring was found where a comet had passed, still faintly warm to the touch. Held up to the eye, its aperture frames places that do not appear on any map. Those who look through it too long start keeping their own secrets.",
    "lunar-canyon-ring": "Lunar Canyon was shaped from a place that looks more like the moon than anywhere on earth should. Its folds stay cool until they are worn, then warm slowly, the way moonlight seems to. Rooms tend to rearrange themselves around whoever wears it.",
    "eleph": "Eleph remembers everything, and forgives most of it. It is cast only when someone asks, which suits its patient and unhurried nature perfectly. Late at night, independent observers still report a distant trumpeting, always from just beyond the edge of the room.",
    "wonderhorn-talisman": "In the old story, Ida plays her wonder horn so sweetly that the goblins cannot help but dance. They dance faster and faster, until they tumble clean out of the window and away. The horn has kept a little of that music ever since.",
    "macon-cap": "The Maçon Cap was made for long days outside, somewhere between the studio and the sun. Its mystic symbol is small enough to miss and strange enough to notice. Wearers report being stopped in the street and asked, very politely, where it came from.",
    "ibi": "Ibi has kept its long watch for longer than anyone can say. It guards its secrets closely, including, it seems, its own likeness. Every attempt to photograph it has ended in fog, and those who hold it agree no picture comes close.",
    "ear-cuff": "The Caldera Arc follows the rim of a volcano, a long drop on one side the whole way round. It needs no piercing, only a gentle press, and soon disappears from notice entirely. In certain light, its edge scatters colours not found anywhere else.",
    "starshipkey-pendant": "The Starship Key opens nothing that can be found on earth, which has never stopped anyone from trying. Worn close, it seems to hum faintly whenever the night sky is especially clear. Researchers who study it are rarely seen at their desks for long.",
    "meridian-egg-ring": "Everyone who picks up the Meridian Egg says the same thing about its weight, and then declines to put it down. Its smooth surface gives nothing away. Those who stare into it for too long report the distinct feeling of being studied in return.",
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
        ("Care" if k in ("totem", "apparel") else "Wear &amp; Care", care),
        ("Materials", f"<p>{html.escape(mat)}</p>"),
        ("Sizing", sizing),
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
    assert not re.search(r"\b(we|i|our|us)\b", DESC[slug], re.I), (slug, "first person in description")
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
            .replace("{{DESC}}", html.escape(DESC[slug]))
            .replace("{{SIZE}}", size_select)
            .replace("{{HERO}}", hero)
            .replace("{{GALLERY}}", "\n      ".join(
                f'<figure><img src="{g}" alt="" loading="lazy"></figure>' for g in gallery))
            .replace("{{ACCORDIONS}}", accordions(slug, k, notes))
            .replace("{{CLOSING}}", close))


def one_block(doc):
    """Accordion text reads as a single block: paragraphs inside a panel are joined."""
    return re.sub(r'(<div class="acc-body">)(.*?)(</div></div></div>)',
                  lambda m: m.group(1) + re.sub(r"</p>\s*<p>", " ", m.group(2)) + m.group(3),
                  doc, flags=re.S)


def shared(doc):
    """Fill the pieces every page has in common: header, footer, shared script."""
    part = lambda n: open(os.path.join(OUT, "partials", n), encoding="utf-8").read().rstrip()
    return (doc.replace("{{NAV}}", part("nav.html"))
               .replace("{{FOOTER}}", part("footer.html"))
               .replace("{{SITEJS}}", part("site.js"))
               .replace("{{CSSV}}", str(int(os.path.getmtime(os.path.join(OUT, "site.css"))))))


def main():
    products = json.load(open(os.path.join(ROOT, "_source/products.json")))
    template = shared(open(os.path.join(OUT, "template.html"), encoding="utf-8").read())
    links = []
    # info pages: story, custom, contact, shipping
    for f in sorted(os.listdir(os.path.join(OUT, "pages"))):
        doc = shared(open(os.path.join(OUT, "pages", f), encoding="utf-8").read())
        open(os.path.join(OUT, f), "w", encoding="utf-8").write(one_block(doc))
        print("  ", f)
    for p in products:
        open(os.path.join(OUT, f"{p['slug']}.html"), "w", encoding="utf-8").write(one_block(page(p, template)))
        links.append(f'<li><a href="{p["slug"]}.html">{html.escape(p["name"])}</a> <span>${p["price"]}</span></li>')
        print("  ", p["slug"])
    # Layout study: photographs edge to edge, product column a pinned white panel over them.
    bleed = """<style>
  @media (min-width:768px){
    .product{grid-template-columns:1fr;margin:0}
    .gallery{grid-column:1;grid-row:1}
    .gallery figure + figure{margin-top:0}
    .gallery .hero img,.gallery figure + figure img{aspect-ratio:3/2;object-fit:cover}
    .info{grid-column:1;grid-row:1;justify-self:end;align-self:start;width:calc(38% + 24px);height:100vh;top:0;
      background:linear-gradient(to right,rgba(0,0,0,0),rgba(0,0,0,.3) 30%,rgba(0,0,0,.45));color:#fff;padding:calc(var(--head) + 8px) var(--pad) 48px 64px;--rule:rgba(255,255,255,.35)}
    .info .label{color:rgba(255,255,255,.7)}
    .info .acc-head{color:#fff}
    .info .acc-head::after{color:#fff}
    .info .cta{background:#fff;color:#000}
    .info .size{border-color:rgba(255,255,255,.5)}
    .info .size select{color:#fff}
    .info .acc-body a{color:#fff}
    .head:not(.ink) .right{color:#fff}
  }
</style>
</head>"""
    study = open(os.path.join(OUT, "starshipkey-pendant.html"), encoding="utf-8").read().replace("</head>", bleed, 1)
    open(os.path.join(OUT, "study-edge-to-edge.html"), "w", encoding="utf-8").write(study)

    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>Product pages · preview</title>'
        '<style>body{font:17px/1.8 "Helvetica Neue",Arial,sans-serif;margin:60px}a{color:#111}span{color:#888}</style>'
        "<h1>Product pages</h1><ul>" + "".join(links) + "</ul>")
    print(f"{len(products)} pages")


if __name__ == "__main__":
    main()
