#!/usr/bin/env python3
"""Build the Kindred Black-style product page preview, one page per piece.

    python3 pdp/build_pdp.py

Copy comes from the port's own product pages (the personal story), the Wix
export (the mythic lore line), and the port's notes (materials, dimensions).
Photographs come from Pieces Master in ~/Downloads and are copied into
pdp/img/<slug>/ so the preview never reaches outside the repo.
"""
import html, json, os, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pdp")
MASTER = os.path.expanduser(os.environ.get("MACON_PIECES", "~/Downloads/Maçon/Pieces Master"))

EYEBROW = {
    "pip": "Tiny Keeper of Tenderness",
    "rebi": "Silhouette in Flux",
    "ren": "Steward of Forgotten Paths",
    "zuma": "Desert Spirit",
    "ori": "Guardian of Forests and Rivers",
    "yael": "Prophecy in Metal",
    "zuma-ring": "Sand Spirit, Distilled",
    "milo": "Ancient Wanderer",
    "eclipse-ring": "Ellipses in Patient Equilibrium",
    "sietch-aperture": "Shelter Cut Into Rock",
    "lunar-canyon-ring": "Forged From a Distant Moon",
    "eleph": "Breath Suspended",
    "wonderhorn-talisman": "Horn for Undiscovered Chords",
    "macon-cap": "Modicum of Solar Protection",
    "ibi": "Eternal Watcher",
    "ear-cuff": "Perfect Geometries",
    "starshipkey-pendant": "Device of Stellar Origin",
    "meridian-egg-ring": "Heavier Than It Looks",
}

# The description under the price. Third person throughout, in the Kindred
# Black manner: the object, its material and making, then its lore.
DESC = {
    "pip": "Solid bronze, small enough to vanish into a closed fist, with an ombré patina. Proximity induces unexpected calm; scholars remain blissfully baffled. The patina is built up slowly by hand and deepens wherever the thumb rests.",
    "rebi": "Solid bronze with an ombré patina, and a different outline from every side of the room. Handling is known to sharpen the reflexes; owners report catching things before they fall. Each plane is refined by hand after casting.",
    "ren": "Solid bronze with a bright crest, drawn from a painted toy on a Swedish shelf. Dawn light lingers on it longer than it should; hikers report arriving home early. The crest is polished by hand while the body is left to darken.",
    "zuma": "Pocket-sized solid bronze, drawn at the same table as its namesake ring. Ancient runes suggest the two belong together; kept apart, both grow restless. Its sun-worn surface is filed and patinated by hand.",
    "ori": "Broad, round-shouldered solid bronze that sits heavy and quiet in the palm. Each winter solstice it gives off a faint warmth; keepers report fewer drafts. Its wide planes are smoothed and patinated slowly by hand.",
    "yael": "Slender solid bronze, balanced on the narrowest of footings. Altar bells resonate in its presence; neighbors report faint chimes at dusk. Its fine upper curves are refined patiently by hand after casting.",
    "zuma-ring": "Sterling silver carrying the shoulder line of the Zuma totem around the finger. Unearthed glyphs record rituals performed with its pair; wearers report an urge to walk barefoot. Each band is sized and polished by hand.",
    "milo": "The first piece made to carry the Maçon mark, in solid bronze with an ombré patina. Its surface adapts to whoever holds it; the bond deepens every season. Each Milo is worked by hand until its surface turns quiet.",
    "eclipse-ring": "Two uneven ovals in sterling silver, set at the exact distance where they stop competing. The gap between them is said to hold questions only stars can answer; astronomers decline to comment. Balanced and polished by hand.",
    "sietch-aperture": "Sterling silver with a single opening, recovered from the wake of a passing comet. Through it appear landscapes found on no map; cartographers have stopped asking. The opening is polished by hand from the inside out.",
    "lunar-canyon-ring": "Sterling silver folded like white stone after a long dry season. Social gatherings ebb and flow around the wearer; hosts plan accordingly. Every fold is brought to a soft polish by hand.",
    "eleph": "Heavy and rounded, with an ombré patina, caught halfway through a long exhale. A low, distant call has been reported by independent observers, always just out of sight. Cast on request and finished entirely by hand.",
    "wonderhorn-talisman": "A silver spiral on a thirty inch chain, after the instrument Ida played until the goblins danced out the window. Nearby children develop perfect pitch; lab equipment hums along. Its inner curl is filed and polished by hand.",
    "macon-cap": "A cotton cap with the Maçon mark stitched on the front. It offers a little shade on bright days; wearers report being asked where they found it. Each cap is checked by hand before it ships.",
    "ibi": "Tall, still solid bronze with a long and patient posture. Attempts to photograph it end in lens fog; photographers blame the weather. Cast on request and patinated by hand.",
    "ear-cuff": "A clean silver line that rests on the ear, no piercing required. Light breaks into odd colours across its mirrored edge. Shaped and polished by hand to hold securely.",
    "starshipkey-pendant": "Chrome-bright sterling silver on a thirty inch chain, shaped like a key to something far above. Prolonged exposure causes wanderlust; researchers take long sabbaticals abroad. Its hull is polished meticulously by hand.",
    "meridian-egg-ring": "Smooth sterling silver, far denser than it looks. Metaphysical analysis detects an abyss gazing back. Each ring is hand polished and sized to order.",
}

# The two centred blocks at the bottom of each page — at least 30 words each.
# First: the lore, grown from the Wix line. Second: how it comes to you.
LORE = {
    "pip": "Pip spent its early years on a windowsill, keeping watch over whoever needed it most. Visitors tend to pick it up without asking and put it down reluctantly. Those who carry it report calmer mornings, and a curious habit of checking their pockets.",
    "rebi": "Rebi has never looked the same way twice in the same light. Some see one thing, some another, and a few insist it is something with no name at all. Each is right, and Rebi seems quietly pleased by the disagreement.",
    "ren": "Ren knows the way through any wood, including the ones that no longer appear on maps. Its bright crest catches the first light of the day and holds it far longer than it should. Travellers who keep it close rarely take a wrong turn.",
    "zuma": "Zuma carries the stillness of the desert at noon, when even the wind stops to rest. Kept in a pocket, it warms slowly and holds that warmth well into the evening. Paired with its ring, it is said to remember the way home across the sand.",
    "ori": "Ori keeps a patient watch over forests, rivers and the households that take it in. It asks for very little beyond a windowsill and the occasional hand. In the depths of winter, keepers swear the room feels a degree or two warmer.",
    "yael": "Yaël stands where the footing is narrowest and the air is thinnest, entirely unbothered by either. Those who keep it close tend to find their balance in unlikely places. At dusk, a faint ringing is sometimes heard, like bells from a very distant mountain.",
    "zuma-ring": "The Zuma Ring carries a small piece of the desert wherever it is worn. Unearthed glyphs suggest it was once exchanged between travellers crossing the same stretch of sand. Wearers report an unexpected fondness for long walks, wide horizons and very quiet afternoons.",
    "milo": "Milo has crossed a great deal of country to arrive here, and seems glad, in its quiet way, to finally stop moving. Its surface takes on the character of whoever holds it most. Over the years, the two tend to grow alike.",
    "eclipse-ring": "The Eclipse Ring holds two shapes that never quite match, and never quite need to. Between them sits a small, bright space that seems to change with the hour. Astronomers have been asked what it means, and each has politely declined to guess.",
    "sietch-aperture": "The Sietch Ring was found where a comet had passed, still faintly warm to the touch. Held up to the eye, its aperture frames places that do not appear on any map. Those who look through it too long start keeping their own secrets.",
    "lunar-canyon-ring": "Lunar Canyon was shaped from a place that looks more like the moon than anywhere on earth should. Its folds stay cool until they are worn, then warm slowly, the way moonlight seems to. Rooms tend to rearrange themselves around whoever wears it.",
    "eleph": "Eleph remembers everything, and forgives most of it. It is cast only when someone asks, which suits its patient and unhurried nature perfectly. Late at night, independent observers still report a low, distant call, always from just beyond the edge of the room.",
    "wonderhorn-talisman": "In the old story, Ida plays her wonder horn so sweetly that the goblins cannot help but dance. They dance faster and faster, until they tumble clean out of the window and away. The horn has kept a little of that music ever since.",
    "macon-cap": "The Maçon Cap was made for long days outside, somewhere between the studio and the sun. Its mystic symbol is small enough to miss and strange enough to notice. Wearers report being stopped in the street and asked, very politely, where it came from.",
    "ibi": "Ibi has kept its long watch for longer than anyone can say. It guards its secrets closely, including, it seems, its own likeness. Every attempt to photograph it has ended in fog, and those who hold it agree no picture comes close.",
    "ear-cuff": "The Caldera Arc follows the rim of a volcano, a long drop on one side the whole way round. It needs no piercing, only a gentle press, and soon disappears from notice entirely. In certain light, its edge scatters colours not found anywhere else.",
    "starshipkey-pendant": "The Starship Key opens nothing that can be found on earth, which has never stopped anyone from trying. Worn close, it seems to hum faintly whenever the night sky is especially clear. Researchers who study it are rarely seen at their desks for long.",
    "meridian-egg-ring": "Everyone who picks up the Meridian Egg says the same thing about its weight, and then declines to put it down. Its smooth surface gives nothing away. Those who stare into it for too long report the distinct feeling of being studied in return.",
}

MADE = ("Each piece is made to order. It begins as a sketch on paper, is carved by hand in wax, "
        "and passes through a local foundry before being refined and polished at the bench. Allow up to two weeks for yours to take shape.")
MADE_LINE = {
    "eleph": "Eleph is cast only when summoned. The wax is carved by hand, the bronze poured at a local foundry, and the patina coaxed slowly at the bench, so each one arrives carrying a little of the waiting.",
    "ibi": "Ibi is cast on request and never kept on a shelf for long. Each is carved in wax, poured at a local foundry, and patinated by hand until its long watch settles into the surface.",
    "macon-cap": "The cap is made in small runs, with the mark stitched on the front and a brim cut for long days between the studio and the sun. When a colour disappears, it may be some time before it returns.",
}

# pictures kept on disk (the shop hover may use them) but left off a product page's gallery
HIDE_FROM_GALLERY = {"img/rebi/hand-1.jpg"}

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


def photos(slug, k):
    base = os.path.join(MASTER, "apparel" if k == "apparel" else ("totems" if k == "totem" else "jewellery"))
    def pick(sub):
        d = os.path.join(base, sub)
        if not os.path.isdir(d):
            return []
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
    ]
    if k != "totem":                       # totems carry no sizing row
        items.append(("Sizing", sizing))
    items.append(("Shipping &amp; Returns",
                  "<p>Each piece is made to order; please allow up to 10 business days before it ships. Standard shipping takes 3–7 business days, international 5–10.</p>"
                  "<p>Pieces in original condition (excluding custom work) may be returned within 14 days of delivery for store credit. If a piece doesn't fit, we'll gladly help you find the right size. "
                  '<a href="mailto:hello@studiomacon.co?subject=Starting%20a%20return">Contact us</a> to begin.</p>'))
    return "\n".join(
        f'''        <div class="acc-item">
          <button class="acc-head" aria-expanded="false">{t}</button>
          <div class="acc-panel"><div class="acc-inner"><div class="acc-body">{b}</div></div></div>
        </div>''' for t, b in items)


def page(p, template, related=""):
    slug, name, price = p["slug"], p["name"], p["price"]
    desc, notes = read_port(slug)
    k = kind(slug, notes)
    plain, hand, drawn = photos(slug, k)

    if plain or hand:
        hero_src = os.path.join(OUT, "img", "wonderhorn-hero-src.jpg") if slug == "wonderhorn-talisman" else (plain[0] if plain else hand[0])
        hero = export(hero_src, slug, "hero", 1600)
        gallery = [export(f, slug, f"plain-{i}", 1800) for i, f in enumerate(plain[1 if slug != "wonderhorn-talisman" else 0:], 1)]
        gallery += [export(f, slug, f"hand-{i}", 1600) for i, f in enumerate(hand, 1)]
        drawing = export(drawn[0], slug, "drawing", 900) if drawn else None
    else:                                  # no Pieces Master on this machine: use the photographs already in img/
        have = sorted(os.listdir(os.path.join(OUT, "img", slug)))
        num = lambda f: int(re.search(r"(\d+)", f).group(1))
        hero = f"img/{slug}/hero.jpg"
        gallery = [f"img/{slug}/{f}" for f in sorted((f for f in have if re.match(r"plain-\d+\.jpg$", f)), key=num)]
        gallery += [f"img/{slug}/{f}" for f in sorted((f for f in have if re.match(r"hand-\d+\.jpg$", f)), key=num)]
        drawing = f"img/{slug}/drawing.jpg" if "drawing.jpg" in have else None

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
    small = {"of", "in", "for", "from", "a", "the", "and", "to", "than", "it", "into", "looks"}
    echo = {w for w in re.findall(r"[a-z]+", EYEBROW[slug].lower()) if w not in small} & set(re.findall(r"[a-z]+", DESC[slug].lower()))
    assert not echo, (slug, "description repeats the overline", echo)
    made = MADE_LINE.get(slug, MADE)
    for block in (DESC[slug], lore, made):          # field-notes voice throughout: never "we" or "I", never about sales
        assert not re.search(r"\b(we|i|our|us|sells?|sold|stock)\b", block, re.I), (slug, block[:60])
    for block in (lore, made):
        assert len(block.split()) >= 30, (slug, len(block.split()))

    ph = '<div class="big" role="presentation"></div>'
    close = f'{ph}\n    <p class="chunk">{html.escape(lore)}</p>\n    {ph}\n    <p class="chunk">{html.escape(made)}</p>\n    {ph}'

    size_select = ""
    if k == "ring":
        sizes = ["4", "4.5", "5", "5.5", "6", "6.5", "7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11"]
        size_select = ('<div class="size" data-size>'
                       '<button type="button" class="size-toggle" aria-haspopup="listbox" aria-expanded="false">'
                       '<span class="size-label">Size</span><span class="size-value">Select size</span><i class="chev" aria-hidden="true"></i></button>'
                       '<div class="size-panel"><div class="size-inner"><ul class="size-list" role="listbox" aria-label="Ring size">'
                       + "".join(f'<li role="option" aria-selected="false" tabindex="0" data-value="{v}">{v}</li>' for v in sizes)
                       + '</ul></div></div></div>')

    # a short film of the piece sits third, after the hero and first still; a lifestyle composite closes the gallery
    gallery = [g for g in gallery if g not in HIDE_FROM_GALLERY]
    figs = [f'<figure><img src="{g}" alt="" loading="lazy"></figure>' for g in gallery]
    if os.path.exists(os.path.join(OUT, "video", "pieces", f"{slug}.mp4")):
        figs.insert(1, f'<figure class="film-still"><video autoplay muted loop playsinline preload="metadata" poster="video/pieces/{slug}.jpg" aria-label="{html.escape(name)} in motion"><source src="video/pieces/{slug}.mp4" type="video/mp4"></video></figure>')
    if os.path.exists(os.path.join(OUT, "img", slug, "composite.jpg")):
        figs.append(f'<figure><img src="img/{slug}/composite.jpg" alt="" loading="lazy"></figure>')

    return (template
            .replace("{{TITLE}}", html.escape(name))
            .replace("{{EYEBROW}}", html.escape(EYEBROW[slug]))
            .replace("{{PRICE}}", f"${price}")
            .replace("{{DESC}}", html.escape(DESC[slug]))
            .replace("{{SIZE}}", size_select)
            .replace("{{HERO}}", hero)
            .replace("{{GALLERY}}", "\n      ".join(figs))
            .replace("{{ACCORDIONS}}", accordions(slug, k, notes))
            .replace("{{CLOSING}}", close)
            .replace("{{RELATED}}", related))


def one_block(doc):
    """Accordion text reads as a single block: paragraphs inside a panel are joined."""
    return re.sub(r'(<div class="acc-body">)(.*?)(</div></div></div>)',
                  lambda m: m.group(1) + re.sub(r"</p>\s*<p>", " ", m.group(2)) + m.group(3),
                  doc, flags=re.S)


def shared(doc):
    """Fill the pieces every page has in common: header, footer, shared script."""
    def part(n):
        with open(os.path.join(OUT, "partials", n), encoding="utf-8") as f:
            return f.read().rstrip()
    doc = doc.replace('<link rel="stylesheet" href="site.css', '<link rel="preload" href="fonts/instrument-serif.woff2" as="font" type="font/woff2" crossorigin>\n<link rel="stylesheet" href="site.css', 1)
    return (doc.replace("{{NAV}}", part("nav.html"))
               .replace("{{FOOTER}}", part("footer.html"))
               .replace("{{SITEJS}}", part("site.js"))
               .replace("{{CSSV}}", str(int(os.path.getmtime(os.path.join(OUT, "site.css"))))))


_sizes = {}


def light(doc):
    """Point every picture at its lighter WebP copy (made by tools/optimize_media.py) and give it its
    real proportions, so nothing shifts while it loads."""
    def one(m):
        tag, src = m.group(0), m.group(1)
        path = os.path.join(OUT, src)
        if not os.path.exists(path):
            return tag
        if " width=" not in tag:
            if src not in _sizes:
                with Image.open(path) as im:
                    _sizes[src] = im.size
            w, h = _sizes[src]
            tag = tag.replace("<img ", f'<img width="{w}" height="{h}" ', 1)
        if os.path.exists(path + ".webp"):
            tag = tag.replace(f'src="{src}"', f'src="{src}.webp"')
        return tag
    return re.sub(r'<img [^>]*?src="(img/[^"]+?\.(?:jpg|png))"[^>]*>', one, doc)


def save(name, doc):
    doc = light(doc)
    left = re.findall(r"\{\{[A-Z]+\}\}", doc)
    assert not left, (name, "unfilled template tokens", left)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(doc)


def align_style(slug):
    """Move the in-hand photograph so the piece sits where it does in the still (img/hover-align.json)."""
    path = os.path.join(OUT, "img", "hover-align.json")
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        a = json.load(f).get(slug)
    return (f' style="--ox:{a["ox"]}%;--oy:{a["oy"]}%;--tx:{a["tx"]}%;--ty:{a["ty"]}%;--s:{a["s"]}"' if a else "")


def related_block(p, products):
    """Phones: four other pieces from the same family (totems with totems, jewelry with jewelry), as a 2 × 2 grid."""
    def family(x):
        return "cap" if x["slug"] == "macon-cap" else ("totem" if kind(x["slug"], read_port(x["slug"])[1]) == "totem" else "jewelry")
    mine = family(p)
    same = [x for x in products if x["slug"] != p["slug"] and family(x) == mine]
    rest = [x for x in products if x["slug"] != p["slug"] and family(x) != mine]
    start = [x["slug"] for x in products].index(p["slug"]) % max(1, len(same))
    pick = (same[start:] + same[:start] + rest)[:4]           # rotate so neighbours differ from page to page
    tiles = "".join(
        f'<a class="rel-piece" href="{x["slug"]}.html"><span class="rel-frame"><img src="img/{x["slug"]}/{"plain-3.jpg" if x["slug"] == "wonderhorn-talisman" else "hero.jpg"}" alt="" loading="lazy"></span>'
        f'<span class="rel-name">{html.escape(x["name"])}</span><span class="rel-cost">${x["price"]}</span></a>'
        for x in pick)
    return ('<section class="related" aria-label="Other pieces">'
            '<p class="eyebrow">Kindred</p><h2>Also Worth<br>Keeping</h2>'
            '<p class="rel-blurb">Pieces that tend to share a pocket, a shelf or a story with this one.</p>'
            f'<div class="rel-grid">{tiles}</div></section>')


def main():
    with open(os.path.join(ROOT, "_source/products.json")) as f:
        products = json.load(f)
    template = shared(open(os.path.join(OUT, "template.html"), encoding="utf-8").read())
    # info pages: story, custom, contact, shipping
    for f in sorted(x for x in os.listdir(os.path.join(OUT, "pages")) if x != "shop.html"):
        doc = shared(open(os.path.join(OUT, "pages", f), encoding="utf-8").read())
        if "{{EXAMPLES}}" in doc:
            base = os.path.join(OUT, "img", "commissions-cut")
            imgs = json.load(open(os.path.join(base, "index.json")))
            lay = json.load(open(os.path.join(base, "layout.json"))) if os.path.exists(os.path.join(base, "layout.json")) else {}
            rank = {n: i for i, n in enumerate(lay.get("order", []))}
            gone = set(lay.get("removed", []))
            imgs = [x for x in imgs if x[0] not in gone]                  # removed in the editor; the file itself is kept
            imgs.sort(key=lambda x: rank.get(x[0], len(rank)))          # saved order first, anything new after
            tweaks = lay.get("pieces", {})
            figs = []
            for i, (n, w, h, cut) in enumerate(imgs):
                t = tweaks.get(n, {})
                figs.append(
                    f'    <figure class="{"cutout" if cut else "photo"}" data-name="{html.escape(n)}" '
                    f'style="--s:{t.get("s", 1)};--x:{t.get("x", 0)};--y:{t.get("y", 0)}">'
                    f'<img src="img/commissions-cut/{html.escape(n)}" width="{w}" height="{h}" alt="{html.escape(t.get("name", ""))}" loading="{"eager" if i < 4 else "lazy"}" draggable="false">'
                    f'<span class="over"><span class="date">{html.escape(t.get("date", ""))}</span>'
                    f'<span class="name">{html.escape(t.get("name", ""))}</span></span></figure>')
            figs.insert(0, '    <figure class="lead" data-lead><img src="img/commissions-cut/hero-band.jpg" alt="A gold band carved with a spiral, a custom commission" fetchpriority="high"></figure>')
            doc = (doc.replace("{{EXAMPLES}}", "\n".join(figs)).replace("{{FRAME}}", lay.get("frame", "3/4"))
                      .replace("{{REMOVED}}", html.escape(json.dumps(sorted(gone)))))
        if "{{GRID}}" in doc:
            imgs = json.load(open(os.path.join(OUT, "img", "inspiration", "index.json")))
            doc = (doc.replace("{{COUNT}}", str(len(imgs)))
                      .replace("{{GRID}}", "\n".join(
                          f'    <figure><img src="img/inspiration/{n}" width="{w}" height="{h}" alt="" loading="{"eager" if i < 8 else "lazy"}"></figure>'
                          for i, (n, w, h) in enumerate(imgs))))
        save(f, one_block(doc))
        print("  ", f)
    for p in products:
        save(f"{p['slug']}.html", one_block(page(p, template, related_block(p, products))))
        print("  ", p["slug"])
    # Shop: every piece on one wall, linking to its page
    tiles = []
    # totems together, then jewellery, then the cap at the very end
    group = lambda p: 2 if p["slug"] == "macon-cap" else (0 if kind(p["slug"], read_port(p["slug"])[1]) == "totem" else 1)
    products = sorted(products, key=group)
    totems = [p for p in products if group(p) == 0]
    for i, p in enumerate(products):
        # the Wonder Horn's hero is a pale cut-out; its linen photograph sits with the others
        still = "plain-3.jpg" if p["slug"] == "wonderhorn-talisman" else "hero.jpg"
        # pendants show the photograph of the piece being worn; everything else, in the hand
        hover = {"wonderhorn-talisman": "plain-2.jpg", "starshipkey-pendant": "plain-1.jpg"}.get(p["slug"], "hand-1.jpg")
        held = os.path.exists(os.path.join(OUT, "img", p["slug"], hover))
        lazy = "eager" if i < 3 else "lazy"
        tiles.append(
            f'    <figure><a class="piece" href="{p["slug"]}.html">'
            f'<img src="img/{p["slug"]}/{still}" alt="{html.escape(p["name"])}" loading="{lazy}">'
            + (f'<img class="held" src="img/{p["slug"]}/{hover}" alt="" loading="lazy"{align_style(p["slug"])}>' if held else "")
            + f'<span class="over"><span class="name">{html.escape(p["name"])}</span><span class="cost">${p["price"]}</span></span>'
            f'</a></figure>')
    shop = shared(open(os.path.join(OUT, "pages", "shop.html"), encoding="utf-8").read())
    shop = (shop.replace("{{TOTEMCOUNT}}", str(len(totems))).replace("{{JEWELRYCOUNT}}", str(len(products) - len(totems)))
                .replace("{{TOTEMGRID}}", "\n".join(tiles[:len(totems)])).replace("{{JEWELRYGRID}}", "\n".join(tiles[len(totems):])))
    save("index.html", shop)
    print(f"{len(products)} pages")


if __name__ == "__main__":
    main()
