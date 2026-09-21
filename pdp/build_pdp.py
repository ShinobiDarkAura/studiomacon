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

import hashlib
import subprocess
import sys
import content as _content          # the studio's own edits, made in pdp/_editor

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
    "ooak-vessel": "Halves Hiding a Secret",
    "ooak-pendant": "Mane Caught Mid-Stride",
    "ooak-pouch": "Worn Nearest the Heart",
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
    "ooak-vessel": "A small solid bronze vessel in fitted parts, the lid lifting away to reveal a hollow meant for a single small thing. Whatever is placed inside is said to keep better than expected; keepers report finding it exactly where they left it. Unique, carved and patinated by hand.",
    "ooak-pendant": "A long silver head in profile, cut as if the wind had just passed through. Wearers report a pull toward open ground and early mornings. The only one of its kind, carved in wax and polished by hand.",
    "ooak-pouch": "A small pouch of glass beads and soft leather, sized to carry a single totem against the chest. Those who wear it report steadier breathing on crowded days. The only one of its kind, beaded and stitched by hand."
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
    "ooak-vessel": "Hollow Keeper was made to hold exactly one thing, and to keep quiet about what it is. Its lid settles back with a low, satisfying weight. Those who own it tend to check inside more often than they need to, just to be sure.",
    "ooak-pendant": "Long Gallop was drawn in a single line and carved before the line could change its mind. It rests against the chest as though it has only stopped for breath. Wearers say it is hard to sit still for long while it is on.",
    "ooak-pouch": "Heartward Pouch was made for travellers who would rather not leave their keepers at home. Each bead was chosen and set by hand, row after patient row. Whatever rides inside is said to feel the heartbeat, and to find it steadying."
}

MADE = ("Each piece is made to order. It begins as a sketch on paper, is carved by hand in wax, "
        "and passes through a local foundry before being refined and polished at the bench. Allow up to two weeks for yours to take shape.")
MADE_LINE = {
    "eleph": "Eleph is cast only when summoned. The wax is carved by hand, the bronze poured at a local foundry, and the patina coaxed slowly at the bench, so each one arrives carrying a little of the waiting.",
    "ibi": "Ibi is cast on request and never kept on a shelf for long. Each is carved in wax, poured at a local foundry, and patinated by hand until its long watch settles into the surface.",
    "macon-cap": "The cap is made in small runs, with the mark stitched on the front and a brim cut for long days between the studio and the sun. When a colour disappears, it may be some time before it returns.",
}

# pictures kept on disk (the shop hover may use them) but left off a product page's gallery
# pieces whose page still builds but which are left off the shop and Also Worth Keeping for now
HIDE_FROM_SHOP = {"macon-cap"}          # remove a slug here to bring it back

# Photographs that repeat one already in the gallery: same framing, sometimes only a higher-resolution
# copy of it. Measured by comparing normalised thumbnails, then checked by eye.
HIDE_FROM_GALLERY = ({"img/ori/plain-2.jpg", "img/ori/hires-1.jpg", "img/zuma/plain-1.jpg",
                      "img/lunar-canyon-ring/hand-2.jpg", "img/zuma-ring/hand-1.jpg",
                      "img/eclipse-ring/hand-1.jpg", "img/starshipkey-pendant/hand-1.jpg",
                      "img/wonderhorn-talisman/hand-1.jpg"}          # these two rings lead with hand-2, so the repeat is hand-1
                     | {f"img/{t}/hand-1.jpg" for t in ("pip", "rebi", "ren", "zuma", "ori", "yael", "milo", "eleph", "ibi")})          # totems: the first in-hand shot repeats the second

TODO = '<span class="todo">{}</span>'


def kind(slug, notes, name=""):
    if slug == "macon-cap":
        return "apparel"
    if "bronze" in " ".join(notes).lower():
        return "totem"
    if slug.endswith("ring") or name.strip().lower().endswith("ring"):          # "Sietch Ring" is a ring too
        return "ring"
    if "chain" in " ".join(notes).lower():
        return "pendant"
    return "jewellery"


# One-of-one pieces (Ephemeral). Pages are built so they're ready, but they stay off the shop.
# Names, overlines and lore are first drafts, to be settled; photographs are grey stand-ins.
OOAK = [
    {"slug": "ooak-vessel", "name": "Hollow Keeper", "price": 780,
     "notes": ["Solid bronze", "Two parts: a base and a fitted lid", "One of one"]},
    {"slug": "ooak-pendant", "name": "Long Gallop", "price": 640,
     "notes": ["Sterling silver", "Worn on a 30\" chain", "One of one"]},
    {"slug": "ooak-pouch", "name": "Heartward Pouch", "price": 620,
     "notes": ["Glass beads and vegetable-tanned leather", "Worn on a long cord, close to the chest", "One of one"]},
]
OOAK_SLUGS = {x["slug"] for x in OOAK}
HIDE_FROM_SHOP |= OOAK_SLUGS          # one-of-ones stay off the shop until Ephemeral returns


def read_port(slug):
    if slug in OOAK_SLUGS:
        return "", next(x["notes"] for x in OOAK if x["slug"] == slug)
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
    """Bring a photograph over from the Pieces Master, then frame it.

    The photograph as shot is kept in _originals; what the site shows is the framed
    copy in img/. Keeping the two apart means a rebuild can never overwrite the
    framing, which is what happened when both lived in the same place.
    """
    keep_dir = os.path.join(OUT, "_originals", slug)
    live_dir = os.path.join(OUT, "img", slug)
    os.makedirs(keep_dir, exist_ok=True)
    os.makedirs(live_dir, exist_ok=True)
    keep = os.path.join(keep_dir, name + ".jpg")
    live = os.path.join(live_dir, name + ".jpg")

    # a studio edit placed by hand (tools/place_hires.py) is marked and never re-exported over
    pinned = os.path.exists(keep + ".studio")
    stale = False
    if os.path.exists(keep) and not pinned:
        with Image.open(keep) as cur:
            stale = cur.width < width and Image.open(src).width > cur.width
    if not pinned and (not os.path.exists(keep) or stale or os.path.getmtime(src) > os.path.getmtime(keep)):
        im = Image.open(src).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(keep, quality=88)

    if not os.path.exists(live) or os.path.getmtime(keep) > os.path.getmtime(live):
        frame_one(keep, live)
    return f"img/{slug}/{name}.jpg"


def frame_one(keep, live):
    """The photograph goes to the site as it was shot. How it sits inside its frame is
    the studio's to set, by hand, in the editor."""
    import shutil
    shutil.copy2(keep, live)


def accordions(slug, k, notes):
    mat = notes[0] if notes else TODO.format("materials to confirm")
    dims = next((n for n in notes if re.search(r"\d+\s*x\s*\d+", n)), None)
    chain = re.search(r'(\d+)"\s*chain', " ".join(notes), re.I)

    care = {
        "totem": "",          # bronze care is not written anywhere on the site: a handwritten card goes in the parcel
        "ring": "<p>Sterling silver darkens with time and air. Wear it often and it stays bright; bring back the shine with a soft polishing cloth.</p><p>Take it off to swim or clean, and store it on its own so it stays unscratched.</p>",
        "pendant": "<p>Worn long, it rests just below the breastbone and turns with you as you move.</p><p>Sterling silver darkens with time and air. Wear it often and it stays bright, or bring back the shine with a soft polishing cloth. Take it off to swim.</p>",
        "jewellery": "<p>Sterling silver darkens with time and air. Wear it often and it stays bright; bring back the shine with a soft polishing cloth. Take it off to swim.</p>",
        "apparel": "<p>Hand wash cold and reshape while damp. Dry flat, out of direct sun.</p>",
    }[k]

    # Only real measurements are shown. A row saying "to confirm" on a $370 ring reads as an
    # unfinished page, which is worse than the row not being there.
    rows = []
    if dims:
        rows.append(("Dimensions", dims.replace(" x ", " × ")))
    if chain:
        rows.append(("Chain", f"{chain.group(1)} inches"))
    sizing = ("<dl>" + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in rows) + "</dl>") if rows else ""
    if k != "apparel":
        note = ('If your piece needs resizing, takes a knock, or needs adjusting, write to '
                '<a href="mailto:hello@studiomacon.co">hello@studiomacon.co</a> and '
                "we'll look after it.")          # settled copy, not a placeholder
        if k == "ring":          # a ring that does not fit is the one real risk of buying online
            note = ('Unsure of your size? <button type="button" class="linkish" data-open-sizer>Find your size</button> '
                    'or measure a ring you already wear. If it arrives and it is not right, '
                    'we will resize or exchange it: write to '
                    '<a href="mailto:hello@studiomacon.co?subject=Ring%20size">hello@studiomacon.co</a>.')
        sizing += f'<p class="after-dl">{_content.shared("sizing:" + k, note)}</p>'

    # Care belongs to the kind of piece: a change on one totem is a change on every totem.
    def one_para(m, n=[0]):
        n[0] += 1
        key = f"care:{k}:{n[0]}"
        return f'<p>{_content.shared(key, m.group(1))}</p>'
    care_html = re.sub(r"<p>(.*?)</p>", one_para, care, flags=re.S)
    items = []
    if care_html.strip():
        items.append(("Care" if k in ("totem", "apparel") else "Wear &amp; Care", care_html))
    if "todo" not in mat.lower():          # no half-written row goes to a customer
        items.append(("Materials", f"<p>{html.escape(mat)}</p>"))
    if k == "totem":                       # a totem has a size, just nothing to size it to
        if dims:
            shown = dims.replace(" x ", " \u00d7 ")
            nums = re.findall(r"[\d.]+", dims)
            unit = (re.search(r"[a-zA-Z\"']+\s*$", dims.strip()) or [""])[0].strip()
            if len(nums) == 3:
                shown = " \u00d7 ".join(n + L for n, L in zip(nums, "hwd")) + (" " + unit if unit else "")
            items.append(("Dimensions", '<dl><dd class="lone">' + shown + '</dd></dl>'))
    elif rows or k != "apparel":
        items.append(("Sizing", sizing))
    # Shipping reads the same on every piece, so it is edited once for the whole shop.
    ship_a = ("Each piece is made to order; please allow up to 10 business days before it ships. "
              "Shipping is free on all orders within the continental US, and every order arrives "
              "in a special box, wrapped with care.")
    ship_b = ("Pieces in original condition may be returned within 30 days of delivery for store credit. "
              "If a piece doesn't fit, we'll gladly help you find the right size.")
    items.append(("Shipping &amp; Returns",
                  f'<p class="keep-para">{_content.shared("shipping:1", ship_a)}</p>'
                  f'<p>{_content.shared("shipping:2", ship_b)}</p>'
                  '<p class="acc-more"><a href="shipping.html">Full details</a></p>'))
    return "\n".join(
        f'''        <div class="acc-item">
          <button class="acc-head" aria-expanded="false">{t}</button>
          <div class="acc-panel"><div class="acc-inner"><div class="acc-body">{b}</div></div></div>
        </div>''' for t, b in items)


with open(os.path.join(OUT, "shopify", "variants.json")) as _f:
    SHOPIFY = json.load(_f)
LIVE_PRICE = {v["id"].split("/")[-1]: v["price"] for d in SHOPIFY.values() for v in d.get("variants", [])}          # variant number -> current Shopify price


SIZER = """      <div class="sizer-panel" id="sizer-panel" data-no-emerge hidden>
        <h2 class="st">Finding your size</h2>
        <p class="lede st">Two ways to find it: print the sizer below, which is the most accurate, or measure a ring you already wear. If the piece arrives and it is not right, we resize or exchange it. Print at 100%, with page scaling switched off, then hold a ruler against the bar: it must read exactly 100&#160;mm, or the print was scaled and the sizer will be wrong.</p>
        <div class="printbtn st"><button type="button" data-print-sizer>Print the sizer</button></div>
        <div class="step st">
          <div class="bar"></div>
          <div class="cap"><span>0</span><span>50 mm</span><span>100 mm</span></div>
        </div>
        <div class="step st">
          <h2><mark class="hl b">1.</mark> Cut and wrap</h2>
          <p>Cut out the strip and the slot in it. Wrap it around the base of your finger, pointed end first, and feed it through the slot.</p>
          <div class="sizer">
            <div class="slot"></div>
            <div class="ticks" data-ticks></div>
            <p class="edge">Pull to fit, then read the size</p>
          </div>
          <p class="cut">Measure at the end of the day, when fingers are at their largest, and warm. A ring should pass the knuckle with a little resistance.</p>
        </div>
        <div class="step st">
          <h2><mark class="hl c">2.</mark> Or measure a ring you own</h2>
          <p>Measure straight across the inside of a ring that already fits, edge to edge, in millimetres.</p>
          <div class="tablewrap"><div><table><thead><tr><th>US size</th><th>Inside diameter</th><th>Circumference</th></tr></thead><tbody data-sizes></tbody></table></div></div>
          <p class="more-rows linky"><button type="button" data-more-sizes aria-expanded="false">Show all sizes</button></p>
        </div>
        <aside class="helpnote st"><p class="note-label">Maker’s note</p><p>Still unsure? Write to <a href="mailto:hello@studiomacon.co?subject=Ring%20size">hello@studiomacon.co</a> with the finger and hand, and we will talk it through.</p></aside>
      </div>
"""


def page(p, template, related=""):
    slug = p["slug"]
    name = _content.product(slug, "name", p["name"])
    price = _content.product(slug, "price", p["price"])
    desc, notes = read_port(slug)
    notes = _content.product(slug, "notes", notes)
    k = kind(slug, notes, name)
    plain, hand, drawn = photos(slug, k)

    if plain or hand:
        hero_src = os.path.join(OUT, "img", "wonderhorn-hero-src.jpg") if slug == "wonderhorn-talisman" else (plain[0] if plain else hand[0])
        hero = export(hero_src, slug, "hero", 3600)
        gallery = [export(f, slug, f"plain-{i}", 3600) for i, f in enumerate(plain[1 if slug != "wonderhorn-talisman" else 0:], 1)]
        gallery += [export(f, slug, f"hand-{i}", 2400) for i, f in enumerate(hand, 1)]
        drawing = None                     # the charcoal sketches are never used on the site
    else:                                  # no Pieces Master on this machine: use the photographs already in img/
        have = sorted(os.listdir(os.path.join(OUT, "img", slug)))
        num = lambda f: int(re.search(r"(\d+)", f).group(1))
        hero = f"img/{slug}/hero.jpg"
        gallery = [f"img/{slug}/{f}" for f in sorted((f for f in have if re.match(r"plain-\d+\.jpg$", f)), key=num)]
        gallery += [f"img/{slug}/{f}" for f in sorted((f for f in have if re.match(r"hand-\d+\.jpg$", f)), key=num)]
        drawing = None

    # three large images close the page, separating the two text chunks
    # drawing first, then a hand shot and the first plain shot — the two ends of
    # the gallery, which are least likely to be near-duplicates of each other
    hero = _content.product(slug, "hero", hero)
    chosen = _content.product(slug, "gallery", None)
    if chosen:                                   # the studio's own order and selection
        gallery = [g for g in chosen if g != hero]

    hands = [g for g in gallery if "/hand-" in g]
    plains = [g for g in gallery if "/plain-" in g]
    closing = [x for x in [drawing, hands[0] if hands else None, plains[0] if plains else None,
                           hero, *gallery] if x]
    closing = list(dict.fromkeys(closing))[:3]

    # the studio's own wording wins wherever it exists
    eyebrow = _content.product(slug, "eyebrow", EYEBROW[slug])
    blurb = _content.product(slug, "description", DESC[slug])
    lore = _content.product(slug, "lore", LORE[slug])
    made = _content.product(slug, "made", MADE_LINE.get(slug, MADE))
    edited = set(_content.CONTENT["products"].get(slug, {}))

    # The voice rules are enforced on my defaults and only pointed out on the studio's
    # own edits: their copy is theirs, and a build should never refuse to run over it.
    def check(field, text, *tests):
        for ok, why in tests:
            if ok(text):
                continue
            if field in edited:
                print(f"   note: {slug} {field} — {why}")
            else:
                raise AssertionError((slug, field, why))

    small = {"of", "in", "for", "from", "a", "the", "and", "to", "than", "it", "into", "looks"}
    echo = {w for w in re.findall(r"[a-z]+", eyebrow.lower()) if w not in small} & set(re.findall(r"[a-z]+", blurb.lower()))
    voice = (lambda t: not re.search(r"\b(we|i|our|us|sells?|sold|stock)\b", t, re.I), "first person or sales talk")
    check("description", blurb, voice, (lambda t: not echo, f"repeats the overline ({', '.join(sorted(echo))})"))
    check("lore", lore, voice, (lambda t: len(t.split()) >= 30, "shorter than 30 words"))
    check("made", made, voice, (lambda t: len(t.split()) >= 30, "shorter than 30 words"))

    ph = '<div class="big" role="presentation"></div>'
    # Words only for now: the three grey panels between them are placeholders with no photograph
    # behind them, and an empty grey box reads worse than no box at all.
    close = (f'<p class="chunk" data-edit="lore">{html.escape(lore)}</p>'
             f'\n    <p class="chunk" data-edit="made">{html.escape(made)}</p>')

    # sizes and styles come from Shopify (shopify/variants.json, made by tools/shopify_sync.py)
    shop = SHOPIFY.get(slug, {})
    variants = shop.get("variants", [])
    size_select, buy_variant = "", ""
    # A piece that has sold cannot be added to a bag. Every piece here is one of one, so this
    # is the normal end of a product's life, not an error state.
    # only one-of-ones can sell out; every other piece is made to order and never runs out
    in_stock = slug not in OOAK_SLUGS or (any(v.get("available", True) for v in variants) if variants else True)
    if in_stock:
        buy_block = ('<div class="buy" id="bag" data-variant="{{VARIANT}}">'
                     '<button class="cta">Add to Bag</button>'
                     '<button class="buy-now shop-pay" type="button" aria-label="Buy with Shop Pay">'
                     'Buy with <svg class="shop-word" viewBox="0 0 101 42" aria-hidden="true" focusable="false"><path d="M12.0288 18.2598C7.97006 17.3793 6.16191 17.0348 6.16191 15.4708C6.16191 13.9997 7.38555 13.2669 9.83283 13.2669C11.9851 13.2669 13.5584 14.2075 14.7165 16.0504C14.8039 16.1926 14.9841 16.2418 15.1316 16.1653L19.6984 13.8575C19.8623 13.7755 19.9224 13.5677 19.8295 13.4091C17.934 10.1224 14.4324 8.32324 9.82191 8.32324C3.76379 8.32324 0 11.3091 0 16.0559C0 21.098 4.58319 22.3722 8.64743 23.2527C12.7117 24.1331 14.5253 24.4776 14.5253 26.0417C14.5253 27.6057 13.2033 28.344 10.5648 28.344C8.12848 28.344 6.32033 27.2284 5.22779 25.0628C5.14585 24.9042 4.95466 24.8386 4.79624 24.9206L0.240358 27.1791C0.0819403 27.2612 0.0163881 27.4526 0.0983284 27.6166C1.90648 31.2533 5.61564 33.2986 10.5703 33.2986C16.8797 33.2986 20.6927 30.3619 20.6927 25.4675C20.6927 20.573 16.0876 19.1512 12.0288 18.2707V18.2598Z"/><path d="M36.5018 8.32341C33.9125 8.32341 31.6236 9.24214 29.9794 10.8773C29.8756 10.9757 29.7062 10.9046 29.7062 10.7624V0.322772C29.7062 0.142307 29.5642 0.00012207 29.3839 0.00012207H23.67C23.4897 0.00012207 23.3477 0.142307 23.3477 0.322772V32.7245C23.3477 32.905 23.4897 33.0472 23.67 33.0472H29.3839C29.5642 33.0472 29.7062 32.905 29.7062 32.7245V18.5115C29.7062 15.7662 31.8094 13.6608 34.6445 13.6608C37.4796 13.6608 39.5336 15.7225 39.5336 18.5115V32.7245C39.5336 32.905 39.6756 33.0472 39.8559 33.0472H45.5699C45.7501 33.0472 45.8922 32.905 45.8922 32.7245V18.5115C45.8922 12.5397 41.9809 8.32887 36.5018 8.32887V8.32341Z"/><path d="M57.4962 7.39915C54.3934 7.39915 51.4764 8.34522 49.3896 9.71785C49.2476 9.81082 49.1984 10.0022 49.2858 10.1499L51.8041 14.4537C51.897 14.6068 52.0937 14.6615 52.2466 14.5685C53.8308 13.6115 55.6444 13.1139 57.4962 13.1248C62.4837 13.1248 66.1491 16.6466 66.1491 21.3005C66.1491 25.2652 63.2157 28.2019 59.4956 28.2019C56.4638 28.2019 54.3607 26.4355 54.3607 23.9418C54.3607 22.5145 54.967 21.3442 56.5457 20.5184C56.7096 20.4309 56.7697 20.2286 56.6714 20.07L54.2951 16.0451C54.2186 15.9138 54.0548 15.8537 53.9073 15.9084C50.7225 17.0896 48.4883 19.9333 48.4883 23.7504C48.4883 29.5253 53.0824 33.8346 59.4901 33.8346C66.974 33.8346 72.3548 28.6448 72.3548 21.202C72.3548 13.2233 66.0945 7.39368 57.4853 7.39368L57.4962 7.39915Z"/><path d="M89.0635 8.27964C86.1738 8.27964 83.5954 9.34603 81.7108 11.2272C81.607 11.3311 81.4376 11.2546 81.4376 11.1124V8.84838C81.4376 8.66791 81.2956 8.52573 81.1153 8.52573H75.5489C75.3686 8.52573 75.2266 8.66791 75.2266 8.84838V41.2009C75.2266 41.3814 75.3686 41.5236 75.5489 41.5236H81.2628C81.4431 41.5236 81.5851 41.3814 81.5851 41.2009V30.5917C81.5851 30.4495 81.7545 30.3784 81.8583 30.4714C83.7374 32.2214 86.2229 33.244 89.069 33.244C95.7717 33.244 101 27.8137 101 20.7591C101 13.7045 95.7663 8.27417 89.069 8.27417L89.0635 8.27964ZM87.9874 27.7644C84.1744 27.7644 81.2847 24.7293 81.2847 20.7153C81.2847 16.7014 84.169 13.6663 87.9874 13.6663C91.8058 13.6663 94.6846 16.6521 94.6846 20.7153C94.6846 24.7786 91.844 27.7644 87.9819 27.7644H87.9874Z"/></svg></button></div>')
    else:
        buy_block = ('<div class="buy sold" id="bag" data-variant="{{VARIANT}}">'
                     '<button class="cta" type="button" disabled>Sold out</button>'
                     '<p class="sold-note">This one has found its person. '
                     '<a href="custom.html">Begin a story of your own</a></p></div>')
    if len(variants) > 1:
        label = "Size" if shop["option"].lower() == "size" else shop["option"]
        size_select = ('<div class="size" data-size>'
                       '<button type="button" class="size-toggle" aria-haspopup="listbox" aria-expanded="false">'
                       f'<span class="size-label">{html.escape(label)}</span><span class="size-value">Select {html.escape(label.lower())}</span><i class="chev" aria-hidden="true"></i></button>'
                       f'<div class="size-panel"><div class="size-inner"><ul class="size-list" role="listbox" aria-label="{html.escape(label)}">'
                       + "".join(f'<li role="option" aria-selected="false" tabindex="0" data-value="{html.escape(v["value"])}" data-variant="{v["id"]}" data-price="{v["price"]:g}">{html.escape(v["value"])}</li>' for v in variants)
                       + '</ul></div></div></div>')
    elif variants:
        buy_variant = variants[0]["id"]

    # a short film of the piece sits third, after the hero and first still; a lifestyle composite closes the gallery
    gallery = [g for g in gallery if g not in HIDE_FROM_GALLERY]
    def framed(src, extra=""):
        """A picture with however the studio has set it inside its frame."""
        f = (_content.product(slug, "frames", {}) or {}).get(src)
        style = ""
        if f:
            style = (f' style="object-position:{f.get("x", 50):g}% {f.get("y", 50):g}%'
                     f';transform-origin:{f.get("x", 50):g}% {f.get("y", 50):g}%'
                     f';transform:scale({f.get("z", 1):g})"')
        # a real description, not an empty alt: these photographs are how the piece is found in image search
        shot = src.rsplit("/", 1)[-1].split(".")[0].replace("--m", "").rstrip("-0123456789").strip("-")
        how = {"hand": "held in the hand", "plain": "seen on its own", "hires": "close up",
               "hero": "", "composite": "at home on a shelf"}.get(shot, "")
        alt = f'{name}, {how}' if how else name
        return f'<figure><img src="{src}"{style} alt="{html.escape(alt)}"{extra}></figure>'

    figs = [framed(g, ' loading="lazy"') for g in gallery]
    hf = (_content.product(slug, "frames", {}) or {}).get(hero)
    hero_style = ("" if not hf else
                  f' style="object-position:{hf.get("x", 50):g}% {hf.get("y", 50):g}%'
                  f';transform-origin:{hf.get("x", 50):g}% {hf.get("y", 50):g}%'
                  f';transform:scale({hf.get("z", 1):g})"')
    if os.path.exists(os.path.join(OUT, "video", "pieces", f"{slug}.mp4")):
        figs.insert(1, f'<figure class="film-still"><video autoplay muted loop playsinline preload="metadata" poster="video/pieces/{slug}.jpg" aria-label="{html.escape(name)} in motion"><source src="video/pieces/{slug}.mp4" type="video/mp4"></video></figure>')
    if os.path.exists(os.path.join(OUT, "img", slug, "composite.jpg")):
        figs.append(framed(f"img/{slug}/composite.jpg", ' loading="lazy"'))
    # pictures the studio has hidden leave the page but stay in the folder
    hidden = _content.product(slug, "hidden", []) or []
    if hidden:
        figs = [f for f in figs if not any(h in f for h in hidden)]

    return (template
            .replace("{{TITLE}}", html.escape(name))
            .replace("{{SLUG}}", slug)
            .replace("{{EYEBROW}}", html.escape(eyebrow))
            .replace("{{PRICE}}", f"${price}")
            .replace("{{DESC}}", html.escape(blurb))
            .replace("{{BUY}}", buy_block)
            .replace('<section class="product">', '<section class="product' + ('' if in_stock else ' claimed') + '">')
            .replace("{{SIZE}}", size_select)
            .replace("{{VARIANT}}", buy_variant)
            .replace("{{HEROSTYLE}}", hero_style)
            .replace("{{HERO}}", hero)
            .replace("{{GALLERY}}", "\n      ".join(figs))
            .replace("{{ACCORDIONS}}", accordions(slug, k, notes))
            .replace("{{SIZER}}", SIZER if k == "ring" else "")
            .replace("{{CLOSING}}", close)
            .replace("{{RELATED}}", related))


def one_block(doc):
    """Accordion text reads as a single block: paragraphs inside a panel are joined.
    A panel marked keep-para is left alone -- shipping and returns are two separate things."""
    join = lambda b: b if "keep-para" in b else re.sub(r"</p>\s*<p>", " ", b)
    return re.sub(r'(<div class="acc-body">)(.*?)(</div></div></div>)',
                  lambda m: m.group(1) + join(m.group(2)) + m.group(3),
                  doc, flags=re.S)


def shop_config():
    with open(os.path.join(OUT, "shopify", "config.json")) as f:
        c = json.load(f)
    tc = SHOPIFY.get("totem-commission", {}).get("variants", [{}])[0].get("id", "")
    return ('<script>window.MACON_SHOP = ' + json.dumps({"shop": c["shop"], "token": c["storefrontToken"], "api": c["apiVersion"],
                                                          "enquiry": c.get("enquiryUrl", ""), "totemCommission": tc,
                                                          "subscribeUrl": c.get("subscribeUrl", "")}) + ';</script>\n')


# The arriving half of the page wipe goes in the head, ahead of everything else.
# The panel has to be on screen and already moving before the page's own scripts
# run: they stall the main thread for a frame or two while they set up, and a
# reveal that starts after that stall is what reads as a stutter.
WIPE_HEAD = """<style>
.wipe{position:fixed;inset:0;z-index:2147483000;pointer-events:none;will-change:transform;
  transform:translate3d(0,-100%,0);background:#000}
.wipe.cover{transform:translate3d(0,0,0);transition:transform 420ms cubic-bezier(.5,0,.25,1)}
.wipe.gone{transform:translate3d(0,100%,0);transition:transform 500ms cubic-bezier(.5,0,.25,1)}
</style>
<link rel="preconnect" href="https://connect.facebook.net" crossorigin>
<link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
<script>
(function () {
  try { if (sessionStorage.getItem('macon-wipe') !== '1') return; sessionStorage.removeItem('macon-wipe'); } catch (e) { return; }
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var el = document.createElement('div');
  el.className = 'wipe';
  el.style.transform = 'translate3d(0,0,0)';
  var put = function () { (document.body || document.documentElement).appendChild(el); };
  put();
  requestAnimationFrame(function () { requestAnimationFrame(function () {
    if (!el.isConnected) put();
    el.style.transform = '';
    el.classList.add('gone');
    // Wait for the slide to actually finish. On a timer the tail gets clipped
    // whenever the animation starts a frame or two late, and the panel appears
    // to vanish instead of leaving.
    var done = false;
    var off = function () { if (done) return; done = true; el.remove(); };
    el.addEventListener('transitionend', function (e) { if (e.propertyName === 'transform') off(); });
    setTimeout(off, 1400);          // only a backstop, never the usual path
  }); });
})();
// the soft fade between pages: arriving, the page starts under a white veil that lifts
(function () {
  var fromDrawer = false;
  try {
    if (sessionStorage.getItem('macon-fade') !== '1') return; sessionStorage.removeItem('macon-fade');
    fromDrawer = sessionStorage.getItem('macon-menu') === '1';
  } catch (e) { return; }
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var st = document.createElement('style');
  st.textContent = '.veil{position:fixed;inset:0;z-index:2147482000;background:#fff;pointer-events:none;opacity:1}';
  document.head.appendChild(st);
  var v = document.createElement('div'); v.className = 'veil';
  if (fromDrawer) v.style.zIndex = '59';               // beneath the drawer, over the page
  var put = function () { (document.body || document.documentElement).appendChild(v); }; put();
  var gone = function () { v.remove(); };
  // animated directly rather than by a style change: a style change this close to the page's first frame
  // is sometimes skipped by the browser, and the veil vanished instead of lifting
  var lift = function () {
    if (!v.isConnected) put();
    if (!v.animate) { gone(); return; }
    var a = v.animate([{opacity: 1}, {opacity: 0}], {duration: 450, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards'});
    a.onfinish = gone;
  };
  setTimeout(gone, 2600);                            // never left over the page
  // lift once the pictures on the first screen are ready to show, so the page fades in whole rather than
  // the veil lifting off a blank page and the photographs popping in after (never waits more than 0.7s)
  var ready = function () {
    var imgs = [].filter.call(document.images, function (i) { var r = i.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && r.width > 40; });
    var done = false, go = function () { if (!done) { done = true; lift(); } };
    // the browser keeps the old page on screen until the new one first draws real content; start lifting
    // only after that, or the fade runs where no one can see it
    var drawn = new Promise(function (res) {
      try {
        if (performance.getEntriesByName('first-contentful-paint').length) return res();
        new PerformanceObserver(function (l) { if (l.getEntriesByName('first-contentful-paint').length) res(); }).observe({type: 'paint', buffered: true});
      } catch (e) { res(); }
    });
    Promise.all([drawn].concat(imgs.map(function (i) { return (i.decode ? i.decode() : Promise.resolve()).catch(function () {}); }))).then(go);
    setTimeout(go, 900);
  };
  if (document.readyState !== 'loading') ready(); else document.addEventListener('DOMContentLoaded', ready);
})();
// arriving for the shop grid: the film at the top is kept hidden until the page has moved down to the grid,
// or its first frame shows the dark film for an instant before the jump
(function () { if (location.hash === '#pieces') document.documentElement.classList.add('to-pieces'); })();
// reached from the mobile drawer: open already pushed aside, with the drawer over the page
(function () { try { if (sessionStorage.getItem('macon-menu') === '1') document.documentElement.classList.add('menu-arriving'); } catch (e) {} })();
</script>
"""


# ── Ads and analytics: the same Meta Pixel and Google tags the Wix site used ──────────────────
# They run only on studiomacon.co itself, so the preview and local copies never reach the studio's
# ad data. Products are named the way Shopify's own Meta app names them (shopify_US_<product>_<variant>),
# so a purchase at Shopify's checkout is credited to the ad and catalog item that led to it.
META_PIXEL, GA4, GOOGLE_ADS = "501136812574699", "G-B5GNGQ1WME", "AW-16466703173"
META_DOMAIN_TAG = "ae0yp3uhbruy2um27iahgcmha7bnph"          # Meta domain verification, carried over from Wix
with open(os.path.join(OUT, "shopify", "ids.json")) as _f:
    SHOP_IDS = json.load(_f)
VARIANT_TO_ITEM = {v["variant"]: f'shopify_US_{v["product"]}_{v["variant"]}' for vs in SHOP_IDS.values() for v in vs}
TRACKING = ("""<meta name="facebook-domain-verification" content="%s">
<script>
(function () {
  window.maconTrack = function () {};
  if (!/(^|\\.)studiomacon\\.co$/.test(location.hostname)) return;          // the real site only
  !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;
  s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
  // An email address, scrambled beyond recovery, lets Meta match an event to a person.
  // Without it a visitor is only a cookie, which often fails: match quality sat at 4.4/10.
  var PIXEL = '%s';
  window.maconIdentify = function (email) {
    try {
      email = String(email || '').trim().toLowerCase();
      if (!email || !crypto.subtle) return;
      crypto.subtle.digest('SHA-256', new TextEncoder().encode(email)).then(function (buf) {
        var hex = [].map.call(new Uint8Array(buf), function (b) { return b.toString(16).padStart(2, '0'); }).join('');
        try { localStorage.setItem('macon-em', hex); } catch (e) {}
        fbq('init', PIXEL, {em: hex});          // from here on, every event carries it
      }).catch(function () {});
    } catch (e) {}
  };
  var known = null;
  try { known = localStorage.getItem('macon-em'); } catch (e) {}
  if (known) fbq('init', PIXEL, {em: known}); else fbq('init', PIXEL);

  // A click id only reaches Shopify if we carry it there ourselves: the cookie it becomes
  // belongs to this domain, and checkout happens on another.
  try {
    var q = new URLSearchParams(location.search), keep = {};
    if (q.get('fbclid')) keep.fbclid = q.get('fbclid');
    ['utm_source','utm_medium','utm_campaign','utm_content','utm_term'].forEach(function (k) { if (q.get(k)) keep[k] = q.get(k); });
    if (Object.keys(keep).length) sessionStorage.setItem('macon-click', JSON.stringify(keep));
  } catch (e) {}

  // The same event, twice: once from the browser, once from our own server, sharing an id
  // so Meta counts it once. Browser events alone are lost to blockers and ITP; that gap is
  // what Meta reports as event coverage.
  var eid = function () {
    try { if (crypto.randomUUID) return crypto.randomUUID(); } catch (e) {}
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  };
  var relay = function (name, id, custom) {
    try {
      fetch('/_e', {
        method: 'POST', keepalive: true, credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ev: name, id: id, url: location.href, em: known || null, custom: custom || {}})
      }).catch(function () {});
    } catch (e) {}
  };
  window.maconSend = function (name, params, custom) {
    var id = eid();
    fbq('track', name, params || {}, {eventID: id});          // eventID, not event_id: the browser key
    relay(name, id, custom || params || {});
  };

  maconSend('PageView', {});
  var g = document.createElement('script'); g.async = true; g.src = 'https://www.googletagmanager.com/gtag/js?id=%s'; document.head.appendChild(g);
  window.dataLayer = window.dataLayer || []; window.gtag = function () { dataLayer.push(arguments); };
  gtag('js', new Date()); gtag('config', '%s'); gtag('config', '%s');
  var ITEMS = %s;                                     // Shopify variant id -> catalog id
  var idOf = function (v) { v = String(v || '').split('/').pop(); return ITEMS[v] || v; };
  window.maconTrack = function (kind, x) {
    try {
      var list = [].concat(x || []), ids = list.map(function (i) { return idOf(i.variant); });
      var value = list.reduce(function (n, i) { return n + (i.price || 0) * (i.qty || 1); }, 0);
      var g4 = list.map(function (i) { return {item_id: idOf(i.variant), item_name: i.name || i.slug, price: i.price, quantity: i.qty || 1}; });
      if (kind === 'signup') { if (window.maconIdentify) maconIdentify(x); return; }
      if (kind === 'view') { maconSend('ViewContent', {content_ids: ids, content_type: 'product', content_name: list[0].name, value: value, currency: 'USD'});
                             gtag('event', 'view_item', {currency: 'USD', value: value, items: g4}); }
      if (kind === 'add') { maconSend('AddToCart', {content_ids: ids, content_type: 'product', value: value, currency: 'USD'});
                            gtag('event', 'add_to_cart', {currency: 'USD', value: value, items: g4}); }
      // Shopify's own checkout fires InitiateCheckout with an id Meta can deduplicate against.
      // Ours carried no id, so the two could never be matched and checkouts counted twice.
      if (kind === 'checkout') { gtag('event', 'begin_checkout', {currency: 'USD', value: value, items: g4}); }
      if (kind === 'lead') { maconSend('Contact', {}); gtag('event', 'generate_lead', {form: x}); }
    } catch (e) {}
  };
})();
</script>
""" % (META_DOMAIN_TAG, META_PIXEL, GA4, GA4, GOOGLE_ADS,
          json.dumps(VARIANT_TO_ITEM, separators=(",", ":"))))


def shared(doc):
    """Fill the pieces every page has in common: header, footer, shared script."""
    def part(n):
        with open(os.path.join(OUT, "partials", n), encoding="utf-8") as f:
            return f.read().rstrip()
    doc = doc.replace("</head>", WIPE_HEAD + TRACKING + "</head>", 1)
    doc = doc.replace('<link rel="stylesheet" href="site.css', '<link rel="preload" href="fonts/instrument-serif.woff2" as="font" type="font/woff2" crossorigin>\n<link rel="stylesheet" href="site.css', 1)
    return (doc.replace("{{NAV}}", part("nav.html"))
               .replace("{{FOOTER}}", part("footer.html"))
               .replace("{{SITEJS}}", shop_config() + part("site.js"))
               .replace("{{CSSV}}", str(int(os.path.getmtime(os.path.join(OUT, "site.css"))))))


_sizes = {}


def tile_src(src):
    """The light copy of a picture, when one has been made for the grids."""
    light_copy = src.rsplit(".", 1)[0] + "--tile.jpg.webp"
    return light_copy if os.path.exists(os.path.join(OUT, light_copy)) else src


def tint_gains(warm, tint):
    """Colour balance for a grid picture, set per piece in the lab (content "tile": warm, tint, each about -20..20).
    warm > 0 is warmer (more red, less blue); tint > 0 is greener, < 0 more magenta."""
    return (1 + warm * 0.01 - tint * 0.005, 1 + tint * 0.01, 1 - warm * 0.01 - tint * 0.005)


def tinted(slug, src):
    """The grid picture with the piece's colour balance baked in (a separate copy; the original is untouched)."""
    t = _content.product(slug, "tile", None) or {}
    warm, tint = round(float(t.get("warm", 0)), 1), round(float(t.get("tint", 0)), 1)
    if not (warm or tint) or not src.endswith(".webp"):
        return src
    fmt = lambda v: ("p" if v >= 0 else "m") + f"{abs(v):g}"
    out = src[:-len(".jpg.webp")] + f"--c{fmt(warm)}{fmt(tint)}.jpg.webp"          # e.g. hero--tile--cm1.5p0.5.jpg.webp
    path = os.path.join(OUT, out)
    if not os.path.exists(path):
        from PIL import Image
        import numpy as np
        im = Image.open(os.path.join(OUT, src)).convert("RGB")
        a = np.asarray(im, float) * np.array(tint_gains(warm, tint))
        Image.fromarray(np.uint8(np.clip(a, 0, 255))).save(path, "WEBP", quality=82, method=6)
    return out


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


SITE = "https://studiomacon.co"
PAGE_META = {          # search and share descriptions for the non-product pages
    "index.html": "Handmade bronze totems and silver jewelry, sketched, carved in wax and cast by hand in Southern California. Made to order.",
    "custom.html": "Commission a one-of-a-kind bronze totem or piece of jewelry, sketched for you, carved by hand in wax and cast at a local foundry.",
    "story.html": "Studio Maçon was founded by Alex and Hannah, whose work is inspired by ancient artifacts and the objects they cared for as children.",
    "contact.html": "Questions about a piece, an order or a commission. Write to Studio Maçon.",
    "shipping.html": "Every piece is made to order. Delivery times, international shipping, sizing and returns.",
    "inspiration.html": "The images, objects and places behind Studio Maçon's artifacts.",
    "ring-sizing.html": "Find your ring size at home: print the Studio Maçon sizer, or measure a ring you already wear.",
    "bag.html": "Your bag at Studio Maçon.",
}
NOINDEX = {"bag.html", "checkout.html", "confirmation.html", "404.html"} | {f"{x}.html" for x in ("ooak-vessel", "ooak-pendant", "ooak-pouch", "macon-cap")}
SITEMAP = []


def _shots(doc, slug, hero):
    """Every photograph on the page, for Product.image: Google Images and Lens are one of the
    few places a piece like this is found, and the field takes a list."""
    seen, out = set(), [hero]
    for m in re.finditer(rf'src="(img/{re.escape(slug)}/[a-z0-9.-]+\.jpg)', doc):
        u = f"{SITE}/{m.group(1)}"
        if u not in seen and u != hero and "--tile" not in u:
            seen.add(u); out.append(u)
    return out[:6]


def seo(name, doc, product=None):
    """Description, canonical, share tags, and product details for Google, added to <head>."""
    title = re.search(r"<title>(.*?)</title>", doc).group(1)
    url = SITE + ("/" if name == "index.html" else "/" + name)
    if product:
        desc, image = DESC[product["slug"]], f'{SITE}/img/{product["slug"]}/hero.jpg'
    else:
        desc, image = PAGE_META.get(name, PAGE_META["index.html"]), f"{SITE}/video/poster-process.jpg"
    desc = html.escape(desc[:300], quote=True)
    tags = [f'<meta name="description" content="{desc}">', f'<link rel="canonical" href="{url}">',
            '<meta property="og:site_name" content="Studio Maçon">', f'<meta property="og:title" content="{title}">',
            f'<meta property="og:description" content="{desc}">', f'<meta property="og:url" content="{url}">',
            f'<meta property="og:image" content="{image}">', f'<meta property="og:type" content="{"product" if product else "website"}">',
            '<meta name="twitter:card" content="summary_large_image">']
    if name in NOINDEX:
        tags.append('<meta name="robots" content="noindex">')
    else:
        SITEMAP.append(url)
    if name == "index.html":
        # who the studio is, and where else it lives: branded searches from the ads land on this
        org = {"@context": "https://schema.org", "@type": "Organization", "name": "Studio Ma\u00e7on",
               "url": SITE, "logo": f"{SITE}/img/favicon.png", "email": "hello@studiomacon.co",
               "sameAs": ["https://www.instagram.com/studiomacon/"]}
        tags.append('<script type="application/ld+json">' + json.dumps(org, ensure_ascii=False).replace("</", "<\\/") + '</script>')
    if product:
        # availability follows Shopify, the same flag the feeds read: every piece is one of one,
        # so a page that keeps saying InStock after it sells is a catalogue mismatch waiting to happen
        def _avail(v):
            return "https://schema.org/InStock" if v.get("available", True) or name[:-5] not in OOAK_SLUGS else "https://schema.org/SoldOut"
        offers = [{"@type": "Offer", "price": f'{v["price"]:.2f}', "priceCurrency": "USD", "availability": _avail(v),
                   "url": url} for v in SHOPIFY.get(product["slug"], {}).get("variants", [])] or \
                 [{"@type": "Offer", "price": f'{float(product["price"]):.2f}', "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": url}]
        ld = {"@context": "https://schema.org", "@type": "Product", "name": product["name"], "description": DESC[product["slug"]],
              "image": _shots(doc, product["slug"], image), "brand": {"@type": "Brand", "name": "Studio Maçon"}, "sku": product["slug"], "offers": offers}
        tags.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + '</script>')
    return doc.replace("</title>", "</title>\n" + "\n".join(tags), 1)


def editable(doc, page):
    """Mark every heading and paragraph on an information page so it can be edited in
    place, and put the studio's own wording in where they have written some.

    Each block is keyed by the page and a short hash of my original words, so the key
    survives blocks moving around. If I later rewrite a default, the old edit simply
    detaches and my new words show: safer than silently keeping stale copy.
    """
    def one(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "data-edit" in attrs or "data-no-edit" in attrs or "{{" in inner:
            return m.group(0)
        key = f"{page}:{hashlib.sha1(inner.strip().encode()).hexdigest()[:8]}"
        return f'<{tag}{attrs} data-edit="page:{key}">{_content.page(key, inner)}</{tag}>'
    return re.sub(r"<(h1|h2|h3|p)([^>]*)>(.*?)</\1>", one, doc, flags=re.S)


def save(name, doc, product=None):
    doc = seo(name, doc, product)
    doc = light(doc)
    # home-screen icon for iPhones, and the two Search Console tags the Wix site carried (keeps those
    # URL-prefix properties verified after the switch)
    doc = doc.replace('<link rel="icon" href="img/favicon.png">',
                      '<link rel="icon" href="img/favicon.png"><link rel="apple-touch-icon" href="img/apple-touch-icon.png">'
                      '<meta name="google-site-verification" content="UEObIGdEnOoIRdBe4jtGb3HLqJgLBge1lnn0HqgOmNs">'
                      '<meta name="google-site-verification" content="9SgxVt1BO36yXRainJxHVzcSkmpf8mZAYfmHSm4phnw">', 1)
    # large photographs also offer their phone-sized copy, so phones do not download the 2400 px one
    def phone(m):
        tag, src, w = m.group(0), m.group(1), m.group(2)
        small = src.replace(".jpg.webp", "--m.jpg.webp")
        # not the top picture: on phones it fills the whole screen height, cropped, and needs every pixel
        if "srcset" in tag or 'fetchpriority="high"' in tag or int(w) <= 1380 or not os.path.exists(os.path.join(OUT, small)):
            return tag
        return tag.replace(f'src="{src}"', f'src="{src}" srcset="{small} 1200w, {src} {w}w" '
                                            f'sizes="(max-width: 767px) 100vw, 60vw"', 1)
    doc = re.sub(r'<img width="(?:\d+)"[^>]*?src="(img/[^"]+\.jpg\.webp)"[^>]*>',
                 lambda m: phone(type("M", (), {"group": lambda self, i: [m.group(0), m.group(1),
                     re.search(r'width="(\d+)"', m.group(0)).group(1)][i]})()), doc)
    left = re.findall(r"\{\{[A-Z]+\}\}", doc)
    assert not left, (name, "unfilled template tokens", left)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(doc)


def align_style(slug):
    """Frame the in-hand photograph so the piece sits where it does in the still, at the size it
    reads there, and hovering a tile no longer makes the piece jump (img/hover-align.json, written
    by tools/align_hover.py)."""
    path = os.path.join(OUT, "img", "hover-align.json")
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        a = json.load(f).get(slug)
    return (f' style="--hx:{a["hx"]:g}%;--hy:{a["hy"]:g}%;--hz:{a["hz"]:g}"' if a else "")


def tile_style(slug):
    """How the studio has framed a piece's tile on the home grid (set in the lab)."""
    t = _content.product(slug, "tile", None)
    if not isinstance(t, dict):
        return ""
    hz = _content.product(slug, "hover_z", None)          # extra zoom on the in-hand picture alone
    # framing set by hand in the grid editor: a scale, a nudge and a turn, about the picture's centre
    fr = _content.product(slug, "frame", None) or {}
    bits = ""
    for key, pre in (("default", "fd"), ("hover", "fh")):
        f = fr.get(key)
        if not f:
            continue
        bits += (f';--{pre}z:{f.get("z", 1):g};--{pre}x:{f.get("x", 0):g}%'
                 f';--{pre}y:{f.get("y", 0):g}%;--{pre}r:{f.get("r", 0):g}deg')
    return (f' style="--x:{t.get("x", 50):g}%;--y:{t.get("y", 50):g}%;--z:{t.get("z", 1.12):g}'
            + (f';--hz:{hz:g}' if hz else "") + bits + '"')


def category(slug, family):
    """Google's product category (Meta reads the same field): totems as art, jewelry by kind. Matches Shopify."""
    if family == "Totems":
        return "Home & Garden > Decor > Artwork > Sculptures & Statues"
    if slug == "ear-cuff":
        return "Apparel & Accessories > Jewelry > Earrings"
    if slug in ("starshipkey-pendant", "wonderhorn-talisman"):
        return "Apparel & Accessories > Jewelry > Necklaces"
    if slug == "macon-cap":
        return "Apparel & Accessories > Clothing Accessories > Hats"
    return "Apparel & Accessories > Jewelry > Rings"


def feeds(products):
    """Product feeds for Meta's catalog (meta-catalog.csv) and Google Merchant Center (google-products.xml).
    Each lists every size of every piece on the shop, with its real page, its photographs, price and stock,
    named as Shopify's own apps name them so ads, catalog and checkout all agree. Meta and Google are set to
    re-read them daily (see the handover plan)."""
    import csv, io, xml.sax.saxutils as sx
    rows = []
    for p in products:
        slug = p["slug"]
        if slug in HIDE_FROM_SHOP or slug not in SHOP_IDS:
            continue
        lead = "plain-3.jpg" if slug == "wonderhorn-talisman" else "hero.jpg"
        shots = [f"img/{slug}/{lead}"] + [g for g in ([_content.product(slug, "hero", "")] + list(_content.product(slug, "gallery", []) or []))
                                           if g and g.endswith(".jpg") and os.path.exists(os.path.join(OUT, g))]
        shots = list(dict.fromkeys(shots))[:10]
        desc = re.sub(r"<[^>]+>", "", _content.product(slug, "description", DESC[slug])).strip()
        family = "Totems" if kind(slug, read_port(slug)[1]) == "totem" else "Jewelry"
        for v in SHOP_IDS[slug]:
            sized = v["value"] not in ("Default Title", "")
            rows.append({
                "id": f'shopify_US_{v["product"]}_{v["variant"]}', "item_group_id": f'shopify_US_{v["product"]}',
                "title": p["name"] + (f' ({v["value"]})' if sized else ""), "description": desc,
                "availability": "in stock" if v["available"] or slug not in OOAK_SLUGS else "out of stock", "condition": "new",
                "price": f'{LIVE_PRICE.get(v["variant"], v["price"]):.2f} USD', "link": f"{SITE}/{slug}.html", "image_link": f"{SITE}/{shots[0]}",
                "additional_image_link": ",".join(f"{SITE}/{x}" for x in shots[1:]), "brand": "Studio Maçon",
                "product_type": family, "size": v["value"] if sized else "", "google_product_category": category(slug, family),
            })
    cols = list(rows[0])
    buf = io.StringIO(); w = csv.DictWriter(buf, cols); w.writeheader(); w.writerows(rows)
    with open(os.path.join(OUT, "meta-catalog.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    e = sx.escape
    items = "".join(
        "<item>" + "".join(f"<g:{k}>{e(str(r[k]))}</g:{k}>" for k in ("id", "item_group_id", "title", "description", "availability",
                                                                      "condition", "price", "image_link", "brand", "product_type", "google_product_category") if r[k])
        + f"<link>{e(str(r['link']))}</link>"
        + "".join(f"<g:additional_image_link>{e(u)}</g:additional_image_link>" for u in r["additional_image_link"].split(",") if u)
        + (f"<g:size>{e(r['size'])}</g:size>" if r["size"] else "") + "<g:identifier_exists>no</g:identifier_exists></item>\n"
        for r in rows)
    with open(os.path.join(OUT, "google-products.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel>'
                f"<title>Studio Maçon</title><link>{SITE}</link><description>Studio Maçon pieces</description>\n{items}</channel></rss>\n")
    print(f"   feeds: {len(rows)} items (meta-catalog.csv, google-products.xml)")


def grid_still(slug):
    """The picture a piece shows in the grids: the studio's choice (content "tile_image"), else its still."""
    return _content.product(slug, "tile_image", None) or f'img/{slug}/{"plain-3.jpg" if slug == "wonderhorn-talisman" else "hero.jpg"}'


def rel_tile(x):
    return tinted(x["slug"], tile_src(grid_still(x["slug"])))


def related_block(p, products):
    """Three other pieces from the same family (totems with totems, jewelry with jewelry)."""
    def family(x):
        if x["slug"] == "macon-cap":
            return "cap"
        k = kind(x["slug"], read_port(x["slug"])[1], x.get("name", ""))
        return k if k in ("totem", "ring", "pendant") else "jewelry"
    mine = family(p)
    products = [x for x in products if x["slug"] not in HIDE_FROM_SHOP]
    same = [x for x in products if x["slug"] != p["slug"] and family(x) == mine]
    # only two pendants exist, so a pendant fills up from the other worn pieces rather than from totems
    worn = {"ring", "pendant", "jewelry"}
    near = [x for x in products if x["slug"] != p["slug"] and family(x) != mine
            and ({family(x), mine} <= worn or {family(x), mine} <= {"totem", "cap"})]
    far = [x for x in products if x["slug"] != p["slug"] and family(x) != mine and x not in near]
    rest = near + far
    slugs = [x["slug"] for x in products]
    start = (slugs.index(p["slug"]) if p["slug"] in slugs else 0) % max(1, len(same))
    pick = (same[start:] + same[:start] + rest)[:3]           # three across; rotated so neighbours differ from page to page
    tiles = "".join(
        f'<a class="rel-piece" href="{x["slug"]}.html"><span class="rel-frame"><img src="{rel_tile(x)}" alt="" loading="lazy"></span>'
        f'<span class="rel-name">{html.escape(x["name"])}</span><span class="rel-cost">${x["price"]}</span></a>'
        for x in pick)
    return ('<section class="related" aria-label="Other pieces">'
            '<p class="eyebrow">Kindred</p><h2>Also Worth<br>Keeping</h2>'
            '<p class="rel-blurb">We’d like to introduce you to a few friends</p>'
            f'<div class="rel-grid">{tiles}</div></section>')


def main():
    with open(os.path.join(ROOT, "_source/products.json")) as f:
        products = json.load(f) + OOAK
    # the studio's own names and prices, applied once so the shop grid, the related
    # pieces and the product pages all speak with the same voice
    for x in products:
        x["name"] = _content.product(x["slug"], "name", x["name"])
        # Shopify is the one source of prices: the lowest size's price (e.g. Caldera Arc from $260)
        vs = (SHOPIFY.get(x["slug"]) or {}).get("variants") or []
        if vs:
            low = min(v["price"] for v in vs)
            x["price"] = int(low) if float(low).is_integer() else low
        x["price"] = _content.product(x["slug"], "price", x["price"])
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
                      .replace("{{PASTCOUNT}}", str(len(imgs)))
                      .replace("{{REMOVED}}", html.escape(json.dumps(sorted(gone)))))
        if "{{GRID}}" in doc:
            imgs = json.load(open(os.path.join(OUT, "img", "inspiration", "index.json")))
            doc = (doc.replace("{{COUNT}}", str(len(imgs)))
                      .replace("{{GRID}}", "\n".join(
                          f'    <figure><img src="img/inspiration/{n}" width="{w}" height="{h}" alt="" loading="{"eager" if i < 8 else "lazy"}"></figure>'
                          for i, (n, w, h) in enumerate(imgs))))
        save(f, editable(one_block(doc), f))
        print("  ", f)
    for p in products:
        doc = one_block(page(p, template, related_block(p, products)))
        first = (SHOP_IDS.get(p["slug"]) or [None])[0]
        if first:                                     # tell Meta and Google a piece was looked at
            # the price Shopify charges today, not the one cached in ids.json: seven pieces were
            # telling Meta and Google the wrong value on every product view
            view = json.dumps({"variant": first["variant"], "name": p["name"], "slug": p["slug"],
                               "price": float(LIVE_PRICE.get(str(first["variant"]).split("/")[-1], first["price"])),
                               "image": f"{SITE}/img/email/wide-{p['slug']}.jpg"})
            doc = doc.replace("</body>", f"<script>maconTrack('view', {view});</script>\n</body>", 1)
        save(f"{p['slug']}.html", doc, product=p)
        print("  ", p["slug"])
    # Shop: every piece on one wall, linking to its page
    tiles = []
    # totems together, then jewellery, then the cap at the very end
    group = lambda p: 2 if p["slug"] == "macon-cap" else (0 if kind(p["slug"], read_port(p["slug"])[1]) == "totem" else 1)
    order = _content.CONTENT.get("order") or []            # the studio's own running order, set by set
    rank = lambda p: order.index(p["slug"]) if p["slug"] in order else len(order)
    products = sorted((x for x in products if x["slug"] not in HIDE_FROM_SHOP), key=lambda p: (group(p), rank(p)))
    totems = [p for p in products if group(p) == 0]
    for i, p in enumerate(products):
        # the Wonder Horn's hero is a pale cut-out; its linen photograph sits with the others
        # pendants show the photograph of the piece being worn; everything else, in the hand
        hover = _content.product(p["slug"], "tile_hover", None) or \
            f'img/{p["slug"]}/' + {"wonderhorn-talisman": "plain-2.jpg", "starshipkey-pendant": "plain-1.jpg"}.get(p["slug"], "hand-1.jpg")
        held = os.path.exists(os.path.join(OUT, hover))
        still_src = tinted(p["slug"], tile_src(grid_still(p["slug"])))          # the grid shows them small, colour-matched
        hover_src = tile_src(hover)
        lazy = "eager" if i < 3 else "lazy"
        tiles.append(
            # the framing sits on the link, so the in-hand picture shown on hover zooms with the still
            f'    <figure><a class="piece" href="{p["slug"]}.html"{tile_style(p["slug"])}>'
            f'<span class="pic"><img src="{still_src}" alt="{html.escape(p["name"])}" loading="{lazy}">'
            + (f'<img class="held" src="{hover_src}" alt="" loading="lazy"{align_style(p["slug"])}>' if held else "")
            + f'</span><span class="over"><span class="name">{html.escape(p["name"])}</span><span class="cost">${p["price"]}</span></span>'
            f'</a></figure>')
    shop = shared(open(os.path.join(OUT, "pages", "shop.html"), encoding="utf-8").read())
    st = {"w": 13, "right": 11.4, "drop": 98.3, "tilt": -14}
    st.update({k: v for k, v in (_content.CONTENT.get("stamp") or {}).items() if isinstance(v, (int, float))})
    shop = shop.replace("{{STAMP}}", f':root{{--stamp-w:clamp(60px,{st["w"]}vw,40vw);--stamp-right:{st["right"]}vw;'
                                     f'--stamp-drop:{st["drop"]}%;--stamp-tilt:{st["tilt"]}deg}}')
    shop = (shop.replace("{{TOTEMCOUNT}}", str(len(totems))).replace("{{JEWELRYCOUNT}}", str(len(products) - len(totems)))
                .replace("{{TOTEMGRID}}", "\n".join(tiles[:len(totems)])).replace("{{JEWELRYGRID}}", "\n".join(tiles[len(totems):])))
    save("index.html", editable(shop, "index.html"))
    feeds(products)
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "".join(f"  <url><loc>{u}</loc></url>\n" for u in sorted(set(SITEMAP))) + "</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nDisallow: /pages/\nDisallow: /partials/\nDisallow: /tools/\nDisallow: /_picker/\nSitemap: {SITE}/sitemap.xml\n")
    print(f"{len(products)} pages")
    # the emails name prices by hand (a marketing email has no cart to read from),
    # so re-write them from Shopify before anyone copies a template out
    subprocess.run([sys.executable, os.path.join(OUT, "tools", "sync_email_prices.py")], check=True)


if __name__ == "__main__":
    main()
