#!/usr/bin/env python3
"""Regenerate the Studio Maçon static site from _source/ data + assets/."""
import json, re, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
prods = json.load(open("_source/products.json"))
man = json.load(open("_source/image-manifest.json"))

# ---------- shared fragments ----------
NAVLINKS = [("index.html", "Shop"), ("story.html", "Story"),
            ("custom.html", "Custom"), ("shipping.html", "Shipping & Returns"),
            ("contact.html", "Contact")]

def nav(up=""):
    links = "".join(f'<a href="{up}{href}">{html.escape(label)}</a>' for href, label in NAVLINKS)
    return f'''  <nav class="nav">
    <svg class="urn" viewBox="0 0 24 24" fill="none" stroke="var(--ink)" stroke-width="1.3"><path d="M8 3h8M9 3c0 2 1 3 3 3s3-1 3-3M7 8c0-1.5 2-2 5-2s5 .5 5 2c0 5-2 8-5 12-3-4-5-7-5-12Z"/></svg>
    <a class="logo" href="{up}index.html"><img src="{up}assets/goat-logo.gif" alt="Studio Maçon"></a>
    <button class="menu" data-menu-open aria-label="Open menu">Menu</button>
  </nav>
  <div class="menu-overlay" role="dialog" aria-label="Menu">
    <button class="close" data-menu-close aria-label="Close menu">Close</button>
    {links}
  </div>'''

def footer(up=""):
    return f'''  <footer>
    <div class="links"><a href="{up}story.html">Story</a><a href="{up}custom.html">Custom</a><a href="{up}shipping.html">Shipping &amp; Returns</a></div>
    <a class="mail" href="mailto:hello@studiomacon.co">hello@studiomacon.co</a>
    <div class="fine">MAÇON · HANDMADE IN CALIFORNIA</div>
  </footer>'''

def page(title, body, up="", desc=""):
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="{up}assets/favicon.png">
<link rel="stylesheet" href="{up}assets/site.css">
</head><body>
{nav(up)}
{body}
{footer(up)}
<script src="{up}assets/site.js"></script>
</body></html>'''

def notes_for(slug):
    try: md = open(f"_source/pages/{slug}.md").read()
    except FileNotFoundError: return []
    m = re.search(r"## NOTES(.*?)\$[\d.,]+Price", md, re.S)
    if not m: return []
    return [l.strip() for l in m.group(1).splitlines()
            if l.strip() and "$" not in l and l.strip().lower() != "price"][:4]

# ---------- homepage ----------
cards = []
for p in prods:
    imgs = man.get(p["slug"], [])
    if not imgs: continue
    cards.append(f'''      <a class="card" href="product/{p['slug']}.html">
        <div class="card-img"><img src="images/products/{imgs[0]}" alt="{html.escape(p['name'])}" loading="lazy"></div>
        <div class="card-name">{html.escape(p['name'])}</div>
        <div class="card-price">${p.get('price','')}</div>
      </a>''')
home_body = f'''  <section class="hero">
    <img class="hero-art" src="assets/hero.png" alt="Maçon">
    <img class="crest" src="assets/crest.png" alt="Maçon Bureau of Provenance">
    <p class="tagline"><span class="dash">&mdash;</span><span class="tl">Limited-run and custom artifacts and jewelry designed, cast and finished by hand in California.</span><span class="dash">&mdash;</span></p>
  </section>
  <section class="shop">
    <h2>Shop</h2>
    <div class="grid">
{chr(10).join(cards)}
    </div>
  </section>'''
open("index.html", "w").write(page("Shop ⚚ Studio Maçon", home_body, "",
    "Limited-run and custom artifacts and jewelry designed, cast and finished by hand in California."))

# ---------- product pages ----------
os.makedirs("product", exist_ok=True)
for p in prods:
    slug = p["slug"]; imgs = man.get(slug, [])
    if not imgs: continue
    thumbs = "".join(f'<img src="../images/products/{im}" data-full="../images/products/{im}" class="{"on" if i==0 else ""}" alt="">' for i, im in enumerate(imgs))
    notes = notes_for(slug)
    notes_html = ("<div class=\"notes\"><div class=\"lbl\">Notes</div>" +
                  "".join(f'<div class="row">{html.escape(n)}</div>' for n in notes) + "</div>") if notes else ""
    subj = f"Hi!%20I%27d%20like%20to%20order%20{slug.replace('-','%20')}."
    body = f'''  <section class="product">
    <div class="gallery">
      <img class="main" id="mainImg" src="../images/products/{imgs[0]}" alt="{html.escape(p['name'])}">
      <div class="thumbs">{thumbs}</div>
    </div>
    <div class="pinfo">
      <a class="back" href="../index.html">&larr; Shop</a>
      <h1>{html.escape(p['name'])}</h1>
      <div class="price">${p.get('price','')}</div>
      <div class="desc">{html.escape(p.get('desc') or '')}</div>
      <a class="buy" href="mailto:hello@studiomacon.co?subject={subj}">Buy Now</a>
      {notes_html}
    </div>
  </section>'''
    open(f"product/{slug}.html", "w").write(page(f"{p['name']} | Studio Maçon", body, "../", p.get("desc", "")))

# ---------- content pages ----------
story = '''  <div class="content">
    <h1>Our Story</h1>
    <h3>Our Practice</h3>
    <p class="lead">Each piece begins as a sketch on paper. Next, the object is carved by hand &mdash; first in wax, then fine-tuned in metal. We work closely with a local foundry to cast the wax carvings in bronze, silver or gold. Each piece is then refined and polished in our studio.</p>
    <p>If its path is to become a collection piece, a rubber mold is made so that we can make the children of that original and share them with you. If it's a custom piece, it is one of a kind.</p>
    <div class="steps">
      <figure><img src="images/content/draw.png" alt="Concept &amp; sketch"><figcaption>Concept &amp; Sketch</figcaption></figure>
      <figure><img src="images/content/cast.png" alt="Carve &amp; cast"><figcaption>Carve &amp; Cast</figcaption></figure>
      <figure><img src="images/content/polish.png" alt="Polish &amp; patina"><figcaption>Polish &amp; Patina</figcaption></figure>
    </div>
    <h3>Our History</h3>
    <p>Maçon is based in southern California, but Alex and Hannah met at RISD in 2008. They had figure drawing class together freshman year and quickly became close friends.</p>
    <p>After graduating college, their resilient love for each other &mdash; despite gaps in distance and time &mdash; never waned. Eventually they found their way back to each other and married in 2023. Both Maçon and their union were born out of their desire to live and create as one.</p>
    <div class="twoup"><img src="images/content/hannah.png" alt="Hannah as a child"><img src="images/content/alex.png" alt="Alex as a child"></div>
    <p class="lead">We discover by holding.</p>
    <p>Maçon was founded by two creative and life partners, Alex and Hannah. Their work is inspired by ancient artifacts and the intimate and personal objects they cared for when they were children.</p>
    <img src="images/content/hand-milo.png" alt="Hand holding Milo">
  </div>'''
open("story.html", "w").write(page("Studio Maçon ⚚ Our Story", story, "",
    "The story of Studio Maçon — Alex and Hannah, sculptural jewelry cast by hand in California."))

custom = '''  <div class="content">
    <h1>Custom Heirlooms</h1>
    <p class="lead">Let's make something real together.</p>
    <p>It's a rare privilege to create custom heirlooms to honor a special moment. If you're interested in commissioning a piece for yourself or someone you love, <a href="contact.html">reach out to us here</a>.</p>
    <img src="images/content/lorenz.jpg" alt="Lorenz Ring, 2023">
    <p style="text-align:center;color:var(--olive);font-size:13px;letter-spacing:.06em">Lorenz Ring, 2023</p>
    <div class="twoup"><img src="images/content/custom-2.jpg" alt="Custom work"><img src="images/content/custom-3.jpg" alt="Custom work"></div>
  </div>'''
open("custom.html", "w").write(page("Maçon ⚚ Custom Heirlooms", custom, "",
    "Commission a custom heirloom from Studio Maçon."))

ship = '''  <div class="content">
    <h1>Shipping &amp; Returns</h1>
    <h3>Shipping</h3>
    <p>Each piece is individually made to order; please allow up to 10 business days for us to create your piece before it heads out to you.</p>
    <p>Standard shipping takes 3&ndash;7 business days for delivery, while international shipping generally takes 5&ndash;10 business days depending on shipping destination.</p>
    <h3>Returns</h3>
    <p>We will accept pieces (excluding custom work) in their original condition for store credit towards your next purchase. For pieces that don't fit properly, we will gladly work with you to find the right size. Returns and exchanges must be initiated within 14 days of the delivery date.</p>
    <p><a href="mailto:hello@studiomacon.co?subject=Hi!%20I%27d%20like%20to%20start%20a%20return.">Contact us</a> to initiate a return. Include your order number and please let us know the reason for your return. After your return has been successfully processed, you will receive store credit and a confirmation email.</p>
    <img src="images/content/olive-branch.png" alt="Olive branch" style="max-width:340px">
  </div>'''
open("shipping.html", "w").write(page("Maçon ⚚ Shipping & Returns", ship, "",
    "Shipping and returns policy for Studio Maçon."))

contact = '''  <div class="content contact">
    <img class="leaves" src="images/content/leaves.png" alt="">
    <h1>Contact</h1>
    <p style="text-align:center"><a href="https://www.instagram.com/studiomacon/">@studiomacon</a> &nbsp;&middot;&nbsp; <a href="mailto:hello@studiomacon.co?subject=Hi%20there!">hello@studiomacon.co</a></p>
    <form id="cform" class="cform">
      <div class="row2"><input name="first" placeholder="First Name" required><input name="last" placeholder="Last Name"></div>
      <input name="email" type="email" placeholder="Email" required>
      <textarea name="message" rows="5" placeholder="Message" required></textarea>
      <button type="submit">Send</button>
    </form>
  </div>'''
open("contact.html", "w").write(page("Maçon ⚚ Contact", contact, "",
    "Get in touch with Studio Maçon."))

print("built: index + %d products + story/custom/shipping/contact" % len([p for p in prods if man.get(p['slug'])]))
