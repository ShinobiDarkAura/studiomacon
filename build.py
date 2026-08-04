#!/usr/bin/env python3
"""Build the Studio Maçon static site from Supabase content.

  python3 build.py             # fetch live content from Supabase, then build
  python3 build.py --offline   # build from the last cached fetch (_source/content-cache.json)

Content lives in Supabase (store_products / store_product_images / store_pages /
store_settings). The generated site is fully static — remote images are downloaded
at build time so the deployed pages have no runtime dependency on Supabase.
"""
import json, os, re, sys, html, urllib.request, urllib.parse, hashlib, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

OFFLINE = "--offline" in sys.argv
CACHE = "_source/content-cache.json"

# ---------------------------------------------------------------- config
def _config():
    cfg = json.load(open("supabase-config.json", encoding="utf-8"))
    return (os.environ.get("SUPABASE_URL", cfg["supabase_url"]),
            os.environ.get("SUPABASE_ANON_KEY", cfg["supabase_anon_key"]))

def v(path):
    """Append a content version so browsers pick up replaced assets immediately."""
    try:
        return f"{path}?v={int(os.path.getmtime(path))}"
    except OSError:
        return path

# ---------------------------------------------------------------- fetch
def fetch(path):
    url_base, key = _config()
    url = f"{url_base}/rest/v1/{path}"
    req = urllib.request.Request(url, headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

def load_content():
    if OFFLINE:
        print("  (offline) using cached content")
        return json.load(open(CACHE, encoding="utf-8"))
    products = fetch("store_products?select=*,store_product_images(*)"
                     "&order=sort_order")
    pages = fetch("store_pages?select=*")
    settings = fetch("store_settings?select=*")
    data = {"products": products, "pages": pages, "settings": settings,
            "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    os.makedirs("_source", exist_ok=True)
    json.dump(data, open(CACHE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return data

# ---------------------------------------------------------------- images
def resolve_image(url):
    """Local repo paths pass through; Storage URLs are downloaded so the site stays static."""
    if not url.startswith("http"):
        return url
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".jpg"
    name = hashlib.sha1(url.encode()).hexdigest()[:16] + ext
    dest = f"images/remote/{name}"
    if not os.path.exists(dest):
        os.makedirs("images/remote", exist_ok=True)
        urllib.request.urlretrieve(url, dest)
        print(f"    downloaded {url.split('/')[-1]} -> {dest}")
    return dest

# ---------------------------------------------------------------- derivatives
# Sizes the site actually renders (CSS px), doubled for retina:
#   PDP thumbnail  56px -> 200      card 294px -> 800      PDP hero 1080px -> 1800
DERIVED_DIR = "images/derived"
SIZES = (200, 800, 1800)

def derive(src, width):
    """Return a WebP derivative at `width`, generating it on first use.

    WebP carries alpha, so transparent product shots stop being multi-MB PNGs.
    Derivatives are build artifacts (gitignored) — originals stay the archive.
    """
    if not os.path.exists(src):
        return src
    stem = hashlib.sha1(src.encode()).hexdigest()[:12]
    out = f"{DERIVED_DIR}/{stem}-{width}.webp"
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src):
        return out
    try:
        from PIL import Image
    except ImportError:
        return src                                  # no Pillow -> ship originals
    os.makedirs(DERIVED_DIR, exist_ok=True)
    im = Image.open(src)
    if im.mode == "P":
        im = im.convert("RGBA")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(out, "WEBP", quality=82, method=6)
    return out

def srcset(src):
    """srcset across the derivative sizes, letting the browser pick."""
    parts = []
    for w in SIZES:
        d = derive(src, w)
        if d != src:
            parts.append(f"../{d} {w}w" if False else f"{d} {w}w")
    return ", ".join(parts)

def images_for(p):
    imgs = sorted(p.get("store_product_images") or [], key=lambda i: i["sort_order"])
    out = []
    for i in imgs:
        src = resolve_image(i["url"])
        out.append({
            "url": src,
            "alt": i.get("alt") or p["name"],
            "variant": i.get("variant"),          # 'hand' | 'plain' | None
            "thumb": derive(src, 200),
            "card": derive(src, 800),
            "hero": derive(src, 1800),
            "srcset": srcset(src),
        })
    return out

def pick_variant(imgs, want):
    """First image tagged `want`, else None."""
    return next((i for i in imgs if i.get("variant") == want), None)

# ---------------------------------------------------------------- visibility
def is_public(p, now):
    """Which products get a page built at all."""
    if p["status"] in ("draft",):
        return False
    if p["status"] == "scheduled":
        rel = p.get("release_at")
        if not rel:
            return False
        return datetime.datetime.fromisoformat(rel.replace("Z", "+00:00")) <= now
    return p["status"] in ("live", "sold_out", "archived")

def buyable(p):
    return p["status"] == "live"

# ---------------------------------------------------------------- shell
NAVLINKS = [("index.html", "Shop"), ("story.html", "Story"),
            ("custom.html", "Custom"), ("shipping.html", "Shipping & Returns"),
            ("contact.html", "Contact")]

def nav(up=""):
    links = "".join(f'<a href="{up}{href}">{html.escape(label)}</a>' for href, label in NAVLINKS)
    return f'''  <nav class="nav">
    <svg class="urn" viewBox="0 0 24 24" fill="none" stroke="var(--ink)" stroke-width="1.3"><path d="M8 3h8M9 3c0 2 1 3 3 3s3-1 3-3M7 8c0-1.5 2-2 5-2s5 .5 5 2c0 5-2 8-5 12-3-4-5-7-5-12Z"/></svg>
    <a class="logo" href="{up}index.html" aria-label="Studio Maçon"><span class="goat" role="img" aria-label="Studio Maçon"></span></a>
    <button class="menu" data-menu-toggle aria-label="Menu"><span class="bars"><i></i><i></i><i></i></span></button>
  </nav>
  <div class="menu-overlay" role="dialog" aria-label="Menu">
    {links}
  </div>'''

def footer(up=""):
    return f'''  <footer>
    <div class="links"><a href="{up}story.html">Story</a><a href="{up}custom.html">Custom</a><a href="{up}shipping.html">Shipping &amp; Returns</a></div>
    <div class="fine">HANDMADE IN CALIFORNIA</div>
  </footer>'''

def page(title, body, up="", desc=""):
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="{up}assets/favicon.png">
<link rel="stylesheet" href="{up}{v("assets/site.css")}">
</head><body>
{nav(up)}
{body}
{footer(up)}
<script src="{up}{v("assets/site.js")}"></script>
</body></html>'''

# ---------------------------------------------------------------- cards
def card(p, imgs, hand_first=False):
    """Shop card.

    Products that have both an in-hand and a plain shot alternate which one leads
    (hand_first), and swap to the counterpart on hover — a crossfade only, never
    any movement of the image or the text beneath it.
    """
    price = p.get("price")
    price_txt = f"${float(price):,.0f}" if price else ""
    sold = p["status"] in ("sold_out", "archived")
    badge = '<span class="sold">Claimed</span>' if sold else ""
    cls = "card" + (" is-sold" if sold else "")

    hand, plain = pick_variant(imgs, "hand"), pick_variant(imgs, "plain")
    if hand and plain:
        lead, alt = (hand, plain) if hand_first else (plain, hand)
    else:
        lead, alt = (imgs[0] if imgs else {}), None

    def tag(i, extra_cls):
        ss = (f' srcset="{i["srcset"]}" sizes="(max-width:520px) 90vw,'
              f' (max-width:820px) 45vw, 30vw"') if i.get("srcset") else ""
        src = i.get("card") or i.get("url", "")
        name = html.escape(p["name"])
        return (f'<img class="{extra_cls}" src="{src}"{ss} alt="{name}" '
                f'loading="lazy" decoding="async">')

    imgs_html = tag(lead, "ci-lead")
    if alt:
        imgs_html += tag(alt, "ci-alt")
        cls += " has-alt"

    return f'''      <a class="{cls}" href="product/{p['slug']}.html" data-slug="{p['slug']}">
        <div class="card-img">{imgs_html}{badge}</div>
        <div class="card-name">{html.escape(p['name'])}</div>
        <div class="card-price">{price_txt}</div>
      </a>'''

# ---------------------------------------------------------------- build
def main():
    print("Building Studio Maçon…")
    data = load_content()
    now = datetime.datetime.now(datetime.timezone.utc)

    products = [p for p in data["products"] if is_public(p, now)]
    settings = {s["key"]: s["value"] for s in data["settings"]}
    by_collection = {"ephemeral": [], "perennial": []}
    for p in products:
        by_collection.setdefault(p.get("collection", "perennial"), []).append(p)

    imgs_of = {p["slug"]: images_for(p) for p in products}

    # ---------- homepage ----------
    tagline = settings.get("tagline", "")
    hero = settings.get("hero_image", "assets/hero.png")
    sections = []
    eph = [p for p in by_collection.get("ephemeral", []) if imgs_of[p["slug"]]]
    per = [p for p in by_collection.get("perennial", []) if imgs_of[p["slug"]]]

    def render_cards(items):
        """Alternate the lead shot across products that have both variants."""
        out, n = [], 0
        for p in items:
            ims = imgs_of[p["slug"]]
            both = pick_variant(ims, "hand") and pick_variant(ims, "plain")
            out.append(card(p, ims, hand_first=(both and n % 2 == 1)))
            if both:
                n += 1
        return "\n".join(out)

    if eph:   # only rendered once ephemeral pieces exist
        sections.append(
            '  <section class="shop ephemeral">\n'
            '    <div class="coll-head"><div class="overline">One of One</div>'
            '<h2>Ephemeral</h2></div>\n'
            '    <div class="grid grid-2">\n'
            + render_cards(eph)
            + "\n    </div>\n  </section>")

    crest = f'      <img class="crest" src="{v("assets/crest.png")}" alt="Maçon Bureau of Provenance">\n'
    sections.append(
        '  <section class="shop">\n'
        + ('    <div class="coll-head"><h2>The Collection</h2></div>\n' if eph else '')
        + '    <div class="grid">\n' + (crest if not eph else "")
        + render_cards(per)
        + "\n    </div>\n  </section>")

    hero_src = derive(hero, 1800)
    home_body = (f'  <section class="hero">\n'
                 f'    <img class="hero-art" src="{v(hero_src)}" alt="Maçon" fetchpriority="high">\n'
                 f'    <p class="tagline"><span class="dash">&mdash;</span>'
                 f'<span class="tl">{html.escape(tagline)}</span>'
                 f'<span class="dash">&mdash;</span></p>\n  </section>\n'
                 + "\n".join(sections))
    open("index.html", "w", encoding="utf-8").write(
        page("Shop ⚚ Studio Maçon", home_body, "", tagline))

    # ---------- product pages ----------
    os.makedirs("product", exist_ok=True)
    built = 0
    for p in products:
        imgs = imgs_of[p["slug"]]
        if not imgs:
            print(f"  ! {p['slug']} has no images — skipped")
            continue
        thumbs = "".join(
            f'<img src="../{i["thumb"]}" data-full="../{i["hero"]}" loading="lazy" '
            f'class="{"on" if k == 0 else ""}" alt="">' for k, i in enumerate(imgs))
        notes = p.get("notes") or []
        notes_html = ""
        if notes:
            rows = "".join(f'<div class="row">{html.escape(n)}</div>' for n in notes)
            notes_html = f'''    <section class="notes-block">
      <button class="notes-head" data-notes-toggle aria-expanded="false">
        <span class="lbl">NOTES</span><span class="sign" aria-hidden="true"></span>
      </button>
      <div class="notes-body"><div class="notes-inner">{rows}</div></div>
    </section>'''
        price = p.get("price")
        price_fmt = f"${float(price):,.2f}" if price else ""
        subj = f"Hi!%20I%27d%20like%20to%20order%20{p['slug'].replace('-', '%20')}."
        if buyable(p):
            actions = (f'        <a class="btn-bag" href="mailto:hello@studiomacon.co?subject={subj}">Add to Bag</a>\n'
                       f'        <a class="btn-buy" href="mailto:hello@studiomacon.co?subject={subj}">Buy Now</a>')
        else:
            actions = '        <div class="btn-bag is-disabled" aria-disabled="true">Claimed</div>'
        one_of_one = ('<div class="overline">One of One</div>'
                      if p.get("collection") == "ephemeral" else "")
        body = f'''  <article class="pdp" data-slug="{p['slug']}">
    <div class="pdp-hero"><img id="mainImg" src="../{imgs[0]['hero']}" alt="{html.escape(p['name'])}" fetchpriority="high"></div>
    <div class="thumbs">{thumbs}</div>
    <div class="pdp-info">
      <div class="pdp-left">
        {one_of_one}<h1>{html.escape(p['name'])}</h1>
        <div class="desc">{html.escape(p.get('description') or '')}</div>
      </div>
      <div class="pdp-right">
        <div class="price">{price_fmt}</div>
{actions}
      </div>
    </div>
{notes_html}
  </article>'''
        open(f"product/{p['slug']}.html", "w", encoding="utf-8").write(
            page(f"{p['name']} | Studio Maçon", body, "../", p.get("description") or ""))
        built += 1

    # ---------- prune pages for products that are no longer public ----------
    keep = {f"{p['slug']}.html" for p in products if imgs_of[p["slug"]]}
    for f in os.listdir("product"):
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join("product", f))
            print(f"  pruned product/{f} (no longer published)")

    # ---------- content pages ----------
    build_content_pages({pg["key"]: pg for pg in data["pages"]})

    print(f"  {built} product pages | {len(eph)} ephemeral, {len(per)} perennial")
    print(f"  content fetched {data.get('fetched_at', 'from cache')}")

def page_img(src, alt="", width=1200, cls="", style=""):
    if not src:
        return ""
    d = derive(resolve_image(src), width)
    c = f' class="{cls}"' if cls else ""
    st = f' style="{style}"' if style else ""
    return (f'<img{c} src="{d}" alt="{html.escape(alt)}"{st} '
            f'loading="lazy" decoding="async">')

def blocks_to_html(body):
    """Render editor block JSON. Empty body -> fall back to the built-in copy.

    Block types mirror what the pages actually use, so editing never forces
    content into a shape the design doesn't have.
    """
    out = []
    for b in body:
        t = b.get("type")
        txt = html.escape(b.get("text", ""))
        if t == "h3":
            out.append(f"    <h3>{txt}</h3>")
        elif t == "lead":
            out.append(f'    <p class="lead">{txt}</p>')
        elif t == "p":
            out.append(f"    <p>{txt}</p>")
        elif t == "caption":
            out.append('    <p style="text-align:center;color:var(--olive);'
                       f'font-size:13px;letter-spacing:.06em">{txt}</p>')
        elif t == "html":                       # escape hatch for links etc.
            out.append(f'    <p>{b.get("html","")}</p>')
        elif t == "img":
            out.append("    " + page_img(b.get("src", ""), b.get("alt", ""),
                                         style=b.get("style", "")))
        elif t == "twoup":
            a = page_img(b.get("src1", ""), b.get("alt1", ""), 900)
            c = page_img(b.get("src2", ""), b.get("alt2", ""), 900)
            out.append(f'    <div class="twoup">{a}{c}</div>')
        elif t == "steps":
            figs = ""
            for s in b.get("items", []):
                figs += (f'<figure>{page_img(s.get("src",""), s.get("caption",""), 600)}'
                         f'<figcaption>{html.escape(s.get("caption",""))}</figcaption></figure>')
            out.append(f'    <div class="steps">{figs}</div>')
    return "\n".join(out)

def swap_derivatives(markup, width=1200):
    """Point <img src> in built-in page copy at WebP derivatives."""
    def repl(m):
        tag, src = m.group(0), m.group(1)
        if src.startswith("http"):
            return tag
        tag = tag.replace(src, derive(src, width))
        if "loading=" not in tag:
            # insert INSIDE the tag — appending after '>' renders as visible text
            tag = tag[:-1].rstrip().rstrip("/") + ' loading="lazy" decoding="async">'
        return tag
    return re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', repl, markup)

def build_content_pages(pages):
    from content_fallback import FALLBACK          # built-in copy, used until edited
    for key, meta in FALLBACK.items():
        rec = pages.get(key, {})
        title = rec.get("title") or meta["title"]
        body_blocks = rec.get("body") or []
        inner = blocks_to_html(body_blocks) if body_blocks else swap_derivatives(meta["html"])
        extra = meta.get("wrap_class", "")
        pre = (meta.get("pre", "") + "\n") if meta.get("pre") else ""
        post = ("\n" + meta["post"]) if meta.get("post") else ""
        body = (f'  <div class="content {extra}">\n{pre}'
                f'    <h1>{html.escape(title)}</h1>\n{inner}{post}\n  </div>')
        open(meta["file"], "w", encoding="utf-8").write(
            page(meta["page_title"], body, "", meta["desc"]))

if __name__ == "__main__":
    main()
