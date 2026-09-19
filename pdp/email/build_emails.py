#!/usr/bin/env python3
"""The welcome series as email HTML, in the site's own type, colour and photography.

    python3 pdp/email/build_emails.py

Writes email/welcome-1.html, -2.html, -3.html (paste each into Klaviyo: Template → Edit →
HTML, or "Create template → Import HTML"), and email-sized JPEGs into img/email/ that the
site serves. Tables and inline styles only: that is what every mail client reads.
Klaviyo fills in {% unsubscribe_url %} and {{ organization.* }}.
"""
import os, re
from PIL import Image, ImageOps

PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = "https://studiomacon.studiomacon.workers.dev/img/email"   # becomes studiomacon.co/img/email after the switch
SITE = "https://studiomacon.co"                                  # links: work on Wix today and the new site after
CODE = "MACON10"

SERIF = "'Instrument Serif','Times New Roman',Georgia,serif"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"

# ── images, sized for email (2x for sharp screens) ──────────────────────────────────
def jpg(src, name, w=1200, ratio=None, centre=(0.5, 0.5)):
    im = ImageOps.exif_transpose(Image.open(os.path.join(PDP, src))).convert("RGB")
    if ratio:                                                      # cover-crop to a shape
        im = ImageOps.fit(im, (w, round(w / ratio)), Image.LANCZOS, centering=centre)
    else:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(PDP, "img/email", name), quality=82, optimize=True, progressive=True)
    return f"{IMG}/{name}"

def png(src, name, w):
    im = Image.open(os.path.join(PDP, src)).convert("RGBA")
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    bg = Image.new("RGB", im.size, "#ffffff"); bg.paste(im, mask=im.split()[3])   # flattened: no clients guessing at transparency
    bg.save(os.path.join(PDP, "img/email", name.replace(".png", ".jpg")), quality=90)
    return f"{IMG}/{name.replace('.png', '.jpg')}"

LOGO = png("img/logotype.png", "logotype.png", 300)

def eye(w=150):
    """The footer's blinking eye, for the top of the emails: flattened onto white, and started on its last
    frame (eye open), because some mail apps (Outlook) only ever show the first frame."""
    src = Image.open(os.path.join(PDP, "img/mark-loop.gif")); frames, times = [], []
    for i in range(src.n_frames):
        src.seek(i); f = src.convert("RGBA"); bg = Image.new("RGB", f.size, "#ffffff"); bg.paste(f, mask=f.split()[3])
        frames.append(bg.resize((w, round(f.height * w / f.width)), Image.LANCZOS)); times.append(src.info.get("duration", 120))
    frames = frames[-1:] + frames[:-1]; times = times[-1:] + times[:-1]
    frames[0].save(os.path.join(PDP, "img/email/eye.gif"), save_all=True, append_images=frames[1:], duration=times, loop=0, optimize=True)
    return f"{IMG}/eye.gif"
EYE = eye()
HERO1 = jpg("img/pip/hand-2.jpg", "welcome-hero.jpg", 1200, 3 / 2)
HAND = jpg("img/ren/hand-2.jpg", "in-hand.jpg", 1200, 3 / 2)
RENHAND = f"{IMG}/ren-hand.gif"          # from _originals/ren-hand.mov
PATINA = f"{IMG}/ren-patina.gif"          # from _originals/ren-patina.mov, the brushing sped up 4.4x
TURN = f"{IMG}/ring-turn.gif"          # made from a short video (_originals/ring-turn.mov); mail apps that do not animate show the first frame
INSITU = jpg("_originals/insitu-zuma.jpg", "insitu-zuma.jpg", 1200, 3 / 2, (0.5, 0.66))          # Zuma at home, on a stack of books
FILM = [jpg(f"_originals/still-{n}.jpg", f"still-{n}.jpg", 720, 1, (0.5, 0.3) if n == "cast" else (0.5, 0.5)) for n in ("drawn", "cast", "finished")]
POUR = jpg("_originals/still-cast.jpg", "pour-hero.jpg", 1200, 4 / 5)
STEPS = [png(f"img/pages/{n}.png", f"step-{n}.png", 260) for n in ("draw", "cast", "polish")]
# an email-sized picture of every piece, the one the shop grid shows (also used by the site's Klaviyo events)
import json as _json
_C = _json.load(open(os.path.join(PDP, "content.json")))["products"]
for _slug in os.listdir(os.path.join(PDP, "img")):
    _dir = os.path.join(PDP, "img", _slug)
    if not os.path.isdir(os.path.join(PDP, "_originals", _slug)): continue
    _still = (_C.get(_slug) or {}).get("tile_image") or f"img/{_slug}/{'plain-3.jpg' if _slug == 'wonderhorn-talisman' else 'hero.jpg'}"
    if os.path.exists(os.path.join(PDP, _still)):
        jpg(_still, f"tile-{_slug}.jpg", 520, 4 / 5); jpg(_still, f"wide-{_slug}.jpg", 960, 3 / 2)

_PRICE = {k: v["variants"][0]["price"] for k, v in _json.load(open(os.path.join(PDP, "shopify", "variants.json"))).items()}
def three(*pairs):
    return [(n, slug, f"{IMG}/tile-{slug}.jpg") for n, slug in pairs]
_IDS = _json.load(open(os.path.join(PDP, "shopify", "ids.json")))
TOTEM_IDS, JEWEL_IDS = [], []
EMAIL_HELD = {"ear-cuff": "img/ear-cuff/hires-3.jpg"}          # emails only: a different photo from the site's hover
for _slug, _vs in _IDS.items():
    _held = EMAIL_HELD.get(_slug) or (_C.get(_slug) or {}).get("tile_hover") or f"img/{_slug}/" + {"wonderhorn-talisman": "plain-2.jpg", "starshipkey-pendant": "plain-1.jpg"}.get(_slug, "hand-1.jpg")
    if not os.path.exists(os.path.join(PDP, _held)): continue
    jpg(_held, f"held-{_slug}.jpg", 960, 3 / 2); jpg(_held, f"held-{_vs[0]['product']}.jpg", 960, 3 / 2)
    (TOTEM_IDS if _slug in ("pip","rebi","ren","zuma","ori","yael","milo","eleph","ibi") else JEWEL_IDS).append(_vs[0]["product"])

PIECES = three(("Pip", "pip"), ("Rebi", "rebi"), ("Ori", "ori"))

# ── building blocks ─────────────────────────────────────────────────────────────────
def _versioned(html):
    """Each image address carries a short fingerprint of the file, so a changed picture is fetched fresh
    by Shopify, mail apps and the CDN instead of an old cached copy."""
    import hashlib, re
    def tag(m):
        path = os.path.join(PDP, "img", "email", m.group(1))
        if not os.path.exists(path): return m.group(0)
        return m.group(0) + "?v=" + hashlib.md5(open(path, "rb").read()).hexdigest()[:8]
    return re.sub(re.escape(IMG) + r"/([\w.-]+\.(?:jpg|gif|png))(?![?\w])", tag, html)

def page(preheader, body):
    return _versioned(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting"><title>Studio Maçon</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&display=swap" rel="stylesheet">
<style>
  body{{margin:0;padding:0;background:#ffffff}} a{{color:#000000}} img{{border:0;display:block}}
  @media (max-width:620px){{ .wrap{{width:100%!important}} .pad{{padding-left:24px!important;padding-right:24px!important}}
    .h1{{font-size:40px!important}} .col{{display:block!important;width:100%!important;padding:0 0 24px!important}}
    .trio{{padding:0 4px!important}} .trio-t{{font-size:18px!important;padding-top:16px!important}} .trio-d{{font-size:12px!important}}
    .duo{{display:inline-block!important;width:50%!important;box-sizing:border-box}} .gone{{display:none!important}} }}
</style></head>
<body style="margin:0;padding:0;background:#ffffff">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{preheader}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center">
<table role="presentation" class="wrap" width="100%" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px">
  <tr><td align="center" style="padding:53px 0 44px"><a href="{SITE}"><img src="{EYE}" width="54" alt="Studio Maçon" style="width:54px;height:auto"></a></td></tr>
{body}
  <tr><td class="pad" align="center" style="padding:56px 24px 48px;border-top:1px solid #e3e3e3;font:400 12px/1.7 {SANS};color:#8a8a8a">
    Every piece is made to order in the studio in California.<br>
    <a href="{SITE}/story" style="color:#8a8a8a">About</a> &nbsp;·&nbsp; <a href="https://www.instagram.com/studiomacon/" style="color:#8a8a8a">Instagram</a>
    &nbsp;·&nbsp; <a href="{{% unsubscribe_url %}}" style="color:#8a8a8a">Unsubscribe</a><br>
    {{{{ organization.name }}}} · {{{{ organization.full_address }}}}
  </td></tr>
</table></td></tr></table></body></html>""")

def eyebrow(t):
    return f'<tr><td class="pad" align="center" style="padding:0 24px 17px;font:400 14px/1.4 {SANS};color:#000000">{t}</td></tr>'

def h1(t, below=51):
    return (f'<tr><td class="pad h1" align="center" style="padding:0 24px {below}px;font:400 46px/1 {SERIF};'
            f'text-transform:uppercase;letter-spacing:-.005em;color:#000000">{t}</td></tr>')

def title(t):
    """Bag and browse emails: a larger title with 8px more above it and a short rule 24px beneath."""
    return (f'<tr><td class="pad h1" align="center" style="padding:8px 24px 24px;font:400 54px/1 {SERIF};'
            f'text-transform:uppercase;letter-spacing:-.005em;color:#000000">{t}</td></tr>'
            f'<tr><td align="center" style="padding:0 0 40px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="48" height="1" style="width:48px;height:1px;background:#000000;font-size:0;line-height:0">&nbsp;</td></tr></table></td></tr>')

def friends():
    return ('<tr><td class="pad" align="center" style="padding:8px 24px 22px;font:400 16px/1.35 ' + SANS + ';color:#000000">'
            "We'd like to introduce you<br>to a few friends</td></tr>")

def text(t, pad="0 111px 34px"):
    # the side margin becomes a max width, so a phone never has to shrink the email to fit it
    top, side, bottom = pad.split(); w = 600 - 2 * int(side[:-2])
    return (f'<tr><td class="pad" align="center" style="padding:{top} 24px {bottom};font:400 16px/1.6 {SANS};color:#000000">'
            f'<div style="max-width:{w}px;margin:0 auto">{t}</div></td></tr>')

def image(src, alt, link=SITE + "/shop?discount=" + CODE):
    return (f'<tr><td class="pad" align="center" style="padding:0 24px 63px"><a href="{link}"><img src="{src}" width="504" alt="{alt}" '
            f'style="width:100%;max-width:504px;height:auto;margin:0 auto;border-radius:16px;box-shadow:0 18px 28px -12px rgba(0,0,0,.45),0 4px 10px -4px rgba(0,0,0,.25)"></a></td></tr>')

def button(label, href):
    top = 16 if label == "Return to checkout" else 4          # a little more air above the checkout button
    return (f'<tr><td align="center" style="padding:{top}px 24px 53px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
            f'<td bgcolor="#000000" style="background:#000000"><a href="{href}" style="display:inline-block;padding:17px 44px;'
            f'font:500 12px/1 {SANS};letter-spacing:.14em;text-transform:uppercase;color:#ffffff;text-decoration:none">{label}</a>'
            f'</td></tr></table></td></tr>')

def code(note):
    return (f'<tr><td class="pad" align="center" style="padding:10px 24px 49px"><table role="presentation" cellpadding="0" cellspacing="0" '
            f'style="border:1px solid rgba(0,0,0,.12)"><tr><td align="center" style="padding:24px 34px">'
            f'<div style="font:400 11px/1 {SANS};letter-spacing:.14em;text-transform:uppercase;color:#6b6b6b;padding-bottom:10px">{note}</div>'
            f'<div style="font:400 30px/1 {SERIF};letter-spacing:.06em;color:#000000"><span style="padding:2px 8px 0;'
            f'background-color:#fbe84a;background-image:linear-gradient(176deg,#ffffff 0%,#ffffff 42%,'
            f'#fbe84a 44%,#f6df3c 90%,#ffffff 93%);border-radius:3px 6px 4px 7px">{CODE}</span></div></td></tr></table></td></tr>')

def trio(items):
    cells = "".join(
        f'<td class="{"duo" if i < 2 else "duo gone"}" width="33%" valign="top" style="padding:0 6px"><a href="{SITE}/product-page/{slug}" style="text-decoration:none;color:#000000">'
        f'<img src="{src}" width="160" alt="{name}" style="width:100%;height:auto;border-radius:16px">'
        f'<div style="font:400 22px/1 {SERIF};text-transform:uppercase;padding:12px 0 4px">{name}</div>'
        f'<div style="font:400 13px/1 {SANS};color:#6b6b6b">${_PRICE.get(slug, 220):.0f}</div></a></td>' for i, (name, slug, src) in enumerate(items))
    return (f'<tr><td class="pad" style="padding:0 24px 44px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr>{cells}</tr></table></td></tr>')

def film_steps():
    rows = [("Drawn", "Each piece begins as a pencil sketch on paper."),
            ("Cast", "Carved in wax, then cast in bronze or silver."),
            ("Finished", "Polished by hand, its patina built up slowly.")]
    cells = "".join(
        f'<td class="trio" width="33%" valign="top" align="center" style="padding:0 6px">'
        f'<img src="{src}" width="160" alt="" style="width:100%;height:auto;border-radius:16px;{SH}">'
        f'<div class="trio-t" style="font:400 22px/1 {SERIF};text-transform:uppercase;padding:24px 0 9px">{t}</div>'
        f'<div class="trio-d" style="font:400 14px/1.55 {SANS};color:#333333">{d}</div></td>' for src, (t, d) in zip(FILM, rows))
    return (f'<tr><td class="pad" style="padding:8px 24px 48px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr>{cells}</tr></table></td></tr>')

SH = "box-shadow:0 18px 28px -12px rgba(0,0,0,.45),0 4px 10px -4px rgba(0,0,0,.25)"

def steps():
    rows = [("Drawn", "Each piece begins as a pencil sketch on paper."),
            ("Cast", "Carved in wax, then cast in bronze or silver."),
            ("Finished", "Polished by hand, its patina built up slowly.")]
    cells = "".join(
        f'<td class="col" width="33%" valign="top" align="center" style="padding:0 8px">'
        f'<div style="height:150px;line-height:150px"><img src="{src}" width="130" alt="" style="width:130px;height:auto;max-height:150px;margin:0 auto;display:inline-block;vertical-align:bottom"></div>'
        f'<div style="font:400 22px/1 {SERIF};text-transform:uppercase;padding:22px 0 8px">{t}</div>'
        f'<div style="font:400 14px/1.55 {SANS};color:#333333">{d}</div></td>' for src, (t, d) in zip(STEPS, rows))
    return (f'<tr><td class="pad" style="padding:8px 40px 44px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr>{cells}</tr></table></td></tr>')

# ── the three emails ────────────────────────────────────────────────────────────────
EMAILS = {
 "welcome-1": dict(
    subject="Welcome to Maçon",
    preview="10% off a first piece, and a little about how they are made.",
    body=eyebrow("Studio Maçon") + h1("Welcome<br>to the studio") + image(HERO1, "Pip, held in the palm of a hand")
       + text("We're so glad you're here! Maçon is a small studio making even smaller things that bring us GREAT joy. "
              "Here's a little something to thank you:")
       + code("10% off your first purchase") + button("Browse artifacts", SITE + "/shop?discount=" + CODE)
       + friends() + trio(PIECES)),
 "welcome-2": dict(
    subject="How a Maçon piece is made",
    preview="Drawn on paper, carved in wax, cast in metal, finished by hand.",
    body=eyebrow("Studio Maçon") + h1("Carved by hand,<br>cast in metal") + image(PATINA, "Ren being brushed with patina, turning from silver to dark bronze")
       + text("We wanted to show you a little of how our pieces come to be. It's slow, hands-on work, "
              "and every step leaves its mark, so no two ever turn out quite the same.", "0 111px 50px")
       + film_steps() + code("10% off your first purchase") + button("Browse artifacts", SITE + "/shop?discount=" + CODE)
       + friends() + trio(three(("Ren", "ren"), ("Zuma", "zuma"), ("Yaël", "yael")))),
 "welcome-3": dict(
    subject="Your welcome code closes soon",
    preview="MACON10 is good for two more days.",
    body=eyebrow("Studio Maçon") + h1("Made to live<br>with you") + image(TURN, "A silver ring turned slowly between two fingers")
       + text("On a finger, in a pocket, or on a shelf by the bed, our pieces slowly pick up the marks of your days. "
              "Give it time, and yours won't look like anyone else's.", "0 131px 34px")          # narrower column
       + code("10% off, two days left") + button("Browse artifacts", SITE + "/shop?discount=" + CODE)
       + friends() + trio(three(("Milo", "milo"), ("Eleph", "eleph"), ("Ibi", "ibi")))),
}

# ── flows that show the shopper's own pieces (Klaviyo fills these in) ──────────────
def items(loop, title, image, price, link):
    """One row per piece, filled in by Klaviyo. For the preview, one sample row stands in."""
    row = (f'<tr><td align="center" style="padding:0 0 40px"><a href="{link}" style="text-decoration:none">'
           f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="width:100%;max-width:408px;border-radius:16px;'
           f'box-shadow:0 18px 28px -12px rgba(0,0,0,.45),0 4px 10px -4px rgba(0,0,0,.25)"><tr>'
           f'<td height="272" valign="bottom" background="{image}" bgcolor="#8a7a6a" '
           f'style="height:272px;border-radius:16px;background-image:url({image});background-size:cover;background-position:center">'
           f'<div style="padding:48px 22px 18px;border-radius:0 0 16px 16px;text-align:left;'
           f'background-image:linear-gradient(to top,rgba(0,0,0,.42),rgba(0,0,0,0))">'
           f'<div style="font:400 35px/1 {SERIF};text-transform:uppercase;color:#ffffff">{title}</div>'
           f'<div style="font:400 16px/1 {SANS};color:#ffffff;padding-top:7px">${price}</div></div>'
           f'</td></tr></table></a></td></tr>')
    # every further piece sits behind the first like a stacked deck: only its bottom 18% shows below
    peek = (f'<tr><td align="center" style="padding:0 16px"><a href="{link}" style="text-decoration:none">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="width:100%;max-width:376px;'
            f'border-radius:0 0 16px 16px;box-shadow:0 14px 22px -12px rgba(0,0,0,.4)"><tr>'
            f'<td height="49" background="{image}" bgcolor="#8a7a6a" style="height:49px;font-size:0;line-height:0;'
            f'border-radius:0 0 16px 16px;background-image:url({image});background-size:cover;background-position:center bottom">&nbsp;</td>'
            f'</tr></table></a></td></tr>')
    rows = (f'{{% for item in {loop} %}}{row}{{% endfor %}}' if loop else row)          # each piece its own full card
    return (f'<tr><td class="pad" style="padding:0 24px 13px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            + rows + '</table></td></tr>')

CART = items("event.extra.line_items", "{{ item.product.title }}", IMG + "/held-{{ item.product.id }}.jpg",
             "{{ item.line_price|floatformat:0 }}", "{{ event.extra.checkout_url }}")
VIEWED = items(None, "{{ event.ProductName }}", "{{ event.ImageURL|replace:'/wide-','/held-' }}", "{{ event.Price|floatformat:0 }}", "{{ event.URL }}")
ORDER = items("event.extra.line_items", "{{ item.product.title }}", "{{ item.product.images.0.src|missing_product_image }}&width=960&height=640&crop=center",
              "{{ item.line_price|floatformat:0 }}", SITE)
CHECKOUT = "{{ event.extra.checkout_url }}"
GRID = "<!--GRID-->"          # checkout 2 only: the bag laid out as a grid (Shopify version, see _grid)

def notes(rows):
    cells = "".join(f'<tr><td align="center" style="padding:0 0 42px"><div style="font:400 31px/1 {SERIF};text-transform:uppercase;padding-bottom:7px">{t}</div>'
                    f'<div style="font:400 15px/1.6 {SANS};color:#333333">{d}</div></td></tr>' for t, d in rows)
    return (f'<tr><td class="pad" style="padding:4px 24px 26px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:244px;margin:0 auto">'
            f'{cells}</table></td></tr>')

EMAILS.update({
 # Abandoned checkout (trigger: Checkout Started; exit if Placed Order). 1: after 4 hours. 2: after 2 days.
 "checkout-1": dict(
    subject="We saved it for you",
    preview="The piece is waiting where you left it.",
    body=eyebrow("Studio Maçon") + title("We saved it<br>for you") + CART
       + text("Every Maçon piece is made to order once it is chosen, so nothing is lost by taking a moment. "
              "The checkout is saved exactly as it was.", "0 153px 31px") + button("Return to checkout", CHECKOUT)),
 "checkout-2": dict(
    subject="Questions answered",
    preview="Solid metal, made to order, and what happens if it is not right.",
    body=eyebrow("Studio Maçon") + title("Questions<br>answered")
       + notes([("Is it solid?", "Every piece is cast solid in bronze, silver or gold. Nothing is plated, and it has real weight in the hand."),
                ("When does it ship?", "It is made by hand once it is chosen, and it leaves the studio in California within about ten business days.")])
       + GRID
       + notes([("Not quite right?", "Rings are made to size and remade if the fit is off. Any piece can be returned for store credit in 14 days."),
                ("Anything else?", "A reply to this email reaches the studio directly, not a help desk. Every note is read and answered in turn.")])
       + button("Return to checkout", CHECKOUT)),
 # Browse abandonment (trigger: Viewed Product; skip if they checked out or were emailed in the last day). After 1 day.
 "browse-1": dict(
    subject="{% if event.ProductID|slice:'11:25' in '" + ",".join(TOTEM_IDS) + "' %}{{ event.ProductName }} is thinking about you, too{% else %}{{ event.ProductName }}, still catching the light{% endif %}",
    preview="A second look at the piece you were studying.",
    body=eyebrow("Studio Maçon")
       + "{% if event.ProductID|slice:'11:25' in '" + ",".join(TOTEM_IDS) + "' %}"
       + title("They're thinking<br>about you, too") + VIEWED
       + text("Every totem is drawn, carved in wax and cast in bronze by hand, then finished in the studio in California. "
              "No two leave quite alike.", "0 153px 31px") + button("Browse artifacts", "{{ event.URL }}")
       + friends() + trio(three(("Pip", "pip"), ("Ori", "ori"), ("Milo", "milo")))
       + "{% else %}"
       + title("Still catching<br>the light") + VIEWED
       + text("Every piece is drawn, carved in wax and cast in silver or gold by hand, then finished in the studio in California. "
              "No two leave quite alike.", "0 153px 31px") + button("Browse artifacts", "{{ event.URL }}")
       + friends()
       + "{% if 'Eclipse' in event.ProductName %}" + trio(three(("Zuma Ring", "zuma-ring"), ("Lunar Canyon", "lunar-canyon-ring"), ("Caldera Arc", "ear-cuff")))
       + "{% else %}" + trio(three(("Eclipse Ring", "eclipse-ring"), ("Meridian Egg", "meridian-egg-ring"), ("Sietch Ring", "sietch-aperture"))) + "{% endif %}"
       + "{% endif %}"),
 # Post-purchase (trigger: Placed Order). 1: straight away. 2: after 21 days.
 "thanks-1": dict(
    subject="Your piece is being made",
    preview="What happens between now and its arrival.",
    body=eyebrow("Studio Maçon") + h1("Your piece<br>is being made") + ORDER
       + notes([("Made to order", "We start on your order as soon as it comes in. No two pieces come out alike."),
                ("On its way", "You can expect it to ship within about ten business days. We'll send you tracking as soon as possible."),
                ("Questions", "Just reply to this email! We respond to every message directly.")])),
 "thanks-2": dict(
    subject="How to care for your piece",
    preview="Bronze and silver, and how they change with handling.",
    body=eyebrow("Studio Maçon") + h1("Meant to<br>be handled") + image(HAND, "A small bronze totem held in the palm")
       + notes([("Bronze", "The patina darkens where the thumb rests and brightens where it rubs. "
                           "To keep it as it is, wipe with a soft dry cloth. Avoid polish; it takes the patina with it."),
                ("Silver", "Silver darkens slowly in the air. A polishing cloth brings it back; wearing it often does the same."),
                ("Share it", 'Photographs of Maçon pieces in their new homes are always welcome: '
                             '<a href="https://www.instagram.com/studiomacon/">@studiomacon</a>.')])
       + button("Browse artifacts", SITE + "/shop?discount=" + CODE)
       + friends() + trio(three(("Rebi", "rebi"), ("Zuma Ring", "zuma-ring"), ("Yaël", "yael")))),

 # Thank customers after they purchase: the email Shopify sends after a customer's second order
 "thanks-repeat": dict(
    subject="Look who's back",
    preview="Your second piece is underway. Thank you, truly.",
    body=eyebrow("Studio Maçon") + h1("Good to see<br>you again") + image(HAND, "Ren, held in the palm of a hand")
       + text("A second order means a lot to a studio our size. We've already started on it, and we'll send tracking "
              "as soon as it's on its way. Thank you for coming back!", "0 131px 34px")
       + button("Browse artifacts", SITE + "/shop")
       + friends() + trio(three(("Milo", "milo"), ("Eclipse Ring", "eclipse-ring"), ("Ibi", "ibi")))),
 # Win back customers: sent to customers who haven't ordered in 60 days
 "winback-1": dict(
    subject="We've been thinking of you",
    preview="A few new things from the studio, whenever you're ready.",
    body=eyebrow("Studio Maçon") + h1("It's been<br>a little while") + image(INSITU, "Zuma resting on a stack of books at home")
       + text("We hope your piece has found a good spot. Things have been busy here, with new pieces coming out of "
              "the wax and into the world. Come take a look whenever you like.", "0 131px 34px")
       + button("Browse artifacts", SITE + "/shop")
       + friends() + trio(three(("Rebi", "rebi"), ("Lunar Canyon", "lunar-canyon-ring"), ("Yaël", "yael")))),
})

os.makedirs(os.path.join(PDP, "email"), exist_ok=True)
for name, e in EMAILS.items():
    with open(os.path.join(PDP, "email", name + ".html"), "w", encoding="utf-8") as f:
        f.write(page(e["preview"], e["body"]))
    print(f"{name}.html   subject: {e['subject']}   preview: {e['preview']}")

# ── Shopify Email versions (Marketing → Shopify Email → "Code your own") ────────────────────
# Same design; Shopify's own placeholders. Browse abandonment is left out: Shopify Email cannot see
# visits to this custom site. For the bag emails Shopify gives each piece's title and photo but not
# its price, so the title picks our held/worn photograph and the price from the catalogue.
_TITLES = _json.load(open(os.path.join(PDP, "shopify", "titles.json")))
def _line_case():
    """Pick each piece's in-hand photo and price by its name. Written as a plain if/elsif chain:
    Shopify's email code checker rejects case/when."""
    items = [(h, t) for h, t in _TITLES.items() if h in _PRICE]
    chain = "".join(
        f'{{% {"if" if i == 0 else "elsif"} line.product_title == "{t}" %}}{{% assign held = "{IMG}/held-{h}.jpg" %}}'
        f'{{% assign cost = "{_PRICE.get(h, 0):.0f}" %}}{{% assign label = "{t}" %}}'
        for i, (h, t) in enumerate(items))
    return ('{% assign held = line.image_url %}{% assign cost = "" %}{% assign label = line.product_title %}'
            + chain + '{% endif %}')

def _per_piece(tpl):
    """Write tpl out once per known piece, chosen by product name, with Shopify's own photo and name as the
    fallback. Uses only for/if/elsif/else and plain values, no assign/case/filters: Shopify's email code
    checker rejects the rest. tpl holds @HELD@, @LABEL@ and @PRICE@."""
    fill = lambda h, l, p: tpl.replace("@HELD@", h).replace("@LABEL@", l).replace("@PRICE@", p)
    items = [(h, t) for h, t in _TITLES.items() if h in _PRICE]
    out = "".join(f'{{% {"if" if i == 0 else "elsif"} line.product_title == "{t}" %}}'
                  + fill(f"{IMG}/held-{h}.jpg", t.upper(), f"${_PRICE[h]:.0f}") for i, (h, t) in enumerate(items))
    return out + "{% else %}" + fill("{{ line.image_url }}", "{{ line.product_title }}", "") + "{% endif %}"

SITE_ASSETS = IMG.rsplit("/img", 1)[0]

def _grid(card):
    """One piece: the full card. Two: side by side. Three or more: rows of three, the last row left-aligned."""
    def cell(w):
        return (f'<td width="{w}%" valign="top" style="padding:0 6px"><a href="{{{{ abandoned_checkout.url }}}}" style="text-decoration:none;color:#000000">'
                f'<img src="@HELD@" width="160" alt="@LABEL@" style="width:100%;height:auto;border-radius:16px;{SH}">'
                f'<div style="font:400 22px/1 {SERIF};text-transform:uppercase;padding:16px 0 4px">@LABEL@</div>'
                f'<div style="font:400 13px/1 {SANS};color:#6b6b6b">@PRICE@</div></a></td>')
    blank = '<td width="33%" style="padding:0 6px">&nbsp;</td>'
    gap = '</tr><tr><td colspan="3" style="height:28px;font-size:0;line-height:0">&nbsp;</td></tr><tr>'
    n = "abandoned_checkout.line_items.size"
    wrap = lambda inner: ('<tr><td class="pad" style="padding:0 18px 53px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
                          + inner + '</table></td></tr>')
    return (f'{{% if {n} == 1 %}}' + card
            + f'{{% elsif {n} == 2 %}}' + wrap('<tr>{% for line in abandoned_checkout.line_items %}' + _per_piece(cell(50)) + '{% endfor %}</tr>')
            + '{% else %}' + wrap('<tr>{% for line in abandoned_checkout.line_items %}' + _per_piece(cell(33))
                                  + '{% if forloop.index == 3 %}' + gap + '{% endif %}{% endfor %}'
                                  + f'{{% if {n} == 4 %}}{blank}{blank}{{% endif %}}{{% if {n} == 5 %}}{blank}{{% endif %}}</tr>')
            + '{% endif %}')

def _caps(html):
    """Anything styled uppercase is also written in capitals, so it stays in caps in any mail app."""
    def up(m):
        inner = re.sub(r"(<[^>]*>|\{[{%].*?[}%]\}|&\w+;|@\w+@)|([^<{&@]+)", lambda t: t.group(1) or t.group(2).upper(), m.group(2))
        return m.group(1) + inner + m.group(3)
    return re.sub(r'(<(td|div|a)[^>]*text-transform:uppercase[^>]*>)(.*?)(</\2>)',
                  lambda m: up(type("M", (), {"group": lambda self, i: [None, m.group(1), m.group(3), m.group(4)][i]})()), html, flags=re.S)

def to_shopify_cart():
    """The full-width cards, one per piece, in Shopify's terms."""
    card = (items(None, "@LABEL@", "@HELD@", "@PRICE@", "{{ abandoned_checkout.url }}")
            .replace("$@PRICE@", "@PRICE@"))
    head, rest = card.split('<table role="presentation" width="100%" cellpadding="0" cellspacing="0">', 1)
    row, tail = rest.rsplit("</table></td></tr>", 1)
    return (head + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            + "{% for line in abandoned_checkout.line_items %}" + _per_piece(row) + "{% endfor %}</table></td></tr>")

def to_shopify(html, name):
    import re
    html = html.replace('<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&display=swap" rel="stylesheet">', "")
    html = html.replace("<style>", "<style>\n  @font-face{font-family:'Instrument Serif';font-style:normal;font-weight:400;"
                        f"src:url({SITE_ASSETS}/fonts/instrument-serif.woff2) format('woff2')}}", 1)
    html = html.replace("{% unsubscribe_url %}", "{{ unsubscribe_url }}")
    html = html.replace("{{ organization.name }} · {{ organization.full_address }}",
                        "{{ shop.name }} · {{ shop.address.city }}")
    html = html.replace("</body>", "{{ open_tracking_block }}\n</body>")
    if name.startswith("checkout"):
        html = html.replace(CART, to_shopify_cart()).replace("{{ event.extra.checkout_url }}", "{{ abandoned_checkout.url }}")
    if "<!--GRID-->" in html:
        card = to_shopify_cart()
        html = html.replace("<!--GRID-->", _grid(card))
    if name == "thanks-1":                                   # Shopify's order emails list the pieces already; this one shows the studio
        html = re.sub(r'{% for item in event\.extra\.line_items %}.*?{% endfor %}',
                      f'<tr><td align="center"><img src="{HERO1}" width="408" alt="A small bronze totem held in the palm" '
                      f'style="width:100%;max-width:408px;height:auto;border-radius:16px;margin:0 auto 40px;{SH}"></td></tr>', html, flags=re.S)
    left = re.findall(r'{{\s*(?:event|item|organization)\.[^}]*}}|{%[^%]*event\.[^%]*%}', html)
    assert not left, (name, left[:3])                          # nothing Klaviyo-only may remain
    return html

os.makedirs(os.path.join(PDP, "email", "shopify"), exist_ok=True)
for name, e in EMAILS.items():
    if name.startswith("browse"): continue
    with open(os.path.join(PDP, "email", "shopify", name + ".html"), "w", encoding="utf-8") as f:
        out = _caps(to_shopify(page(e["preview"], e["body"]), name))
        # accented letters as HTML codes (ç → &#231;), so a paste that loses UTF-8 cannot break them;
        # names inside Liquid tags stay as they are, since they must match Shopify's product titles
        out = re.sub(r"(\{%.*?%\})|([^\x00-\x7f])", lambda m: m.group(1) or f"&#{ord(m.group(2))};",
                     out, flags=re.S)
        f.write(out)
    print(f"shopify/{name}.html")
