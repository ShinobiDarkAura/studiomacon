#!/usr/bin/env python3
"""The welcome series as email HTML, in the site's own type, colour and photography.

    python3 pdp/email/build_emails.py

Writes email/welcome-1.html, -2.html, -3.html (paste each into Klaviyo: Template → Edit →
HTML, or "Create template → Import HTML"), and email-sized JPEGs into img/email/ that the
site serves. Tables and inline styles only: that is what every mail client reads.
Klaviyo fills in {% unsubscribe_url %} and {{ organization.* }}.
"""
import os
from PIL import Image, ImageOps

PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = "https://studiomacon.studiomacon.workers.dev/img/email"   # becomes studiomacon.co/img/email after the switch
SITE = "https://studiomacon.co"                                  # links: work on Wix today and the new site after
CODE = "MACON10"

SERIF = "'Instrument Serif','Times New Roman',Georgia,serif"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"

# ── images, sized for email (2x for sharp screens) ──────────────────────────────────
def jpg(src, name, w=1200, ratio=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(PDP, src))).convert("RGB")
    if ratio:                                                      # cover-crop to a shape
        im = ImageOps.fit(im, (w, round(w / ratio)), Image.LANCZOS)
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
HERO1 = jpg("img/eleph/hires-1.jpg", "welcome-hero.jpg", 1200, 4 / 5)
HAND = jpg("img/ren/hand-2.jpg", "in-hand.jpg", 1200, 4 / 5)
STEPS = [png(f"img/pages/{n}.png", f"step-{n}.png", 260) for n in ("draw", "cast", "polish")]
# an email-sized picture of every piece, the one the shop grid shows (also used by the site's Klaviyo events)
import json as _json
_C = _json.load(open(os.path.join(PDP, "content.json")))["products"]
for _slug in os.listdir(os.path.join(PDP, "img")):
    _dir = os.path.join(PDP, "img", _slug)
    if not os.path.isdir(os.path.join(PDP, "_originals", _slug)): continue
    _still = (_C.get(_slug) or {}).get("tile_image") or f"img/{_slug}/{'plain-3.jpg' if _slug == 'wonderhorn-talisman' else 'hero.jpg'}"
    if os.path.exists(os.path.join(PDP, _still)): jpg(_still, f"tile-{_slug}.jpg", 520, 4 / 5)

PIECES = [(n, slug, jpg(img, f"tile-{slug}.jpg", 520, 4 / 5)) for n, slug, img in [
    ("Pip", "pip", "img/pip/hero.jpg"), ("Rebi", "rebi", "img/rebi/hero.jpg"), ("Ori", "ori", "img/ori/plain-1.jpg")]]

# ── building blocks ─────────────────────────────────────────────────────────────────
def page(preheader, body):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting"><title>Studio Maçon</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&display=swap" rel="stylesheet">
<style>
  body{{margin:0;padding:0;background:#ffffff}} a{{color:#000000}} img{{border:0;display:block}}
  @media (max-width:620px){{ .wrap{{width:100%!important}} .pad{{padding-left:24px!important;padding-right:24px!important}}
    .h1{{font-size:40px!important}} .col{{display:block!important;width:100%!important;padding:0 0 24px!important}} }}
</style></head>
<body style="margin:0;padding:0;background:#ffffff">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{preheader}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff"><tr><td align="center">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px">
  <tr><td align="center" style="padding:44px 0 36px"><a href="{SITE}"><img src="{EYE}" width="75" alt="Studio Maçon" style="width:75px;height:auto"></a></td></tr>
{body}
  <tr><td class="pad" align="center" style="padding:56px 48px 48px;border-top:1px solid #e3e3e3;font:400 12px/1.7 {SANS};color:#8a8a8a">
    Every piece is made to order in the studio in California.<br>
    <a href="{SITE}/story" style="color:#8a8a8a">About</a> &nbsp;·&nbsp; <a href="https://www.instagram.com/studiomacon/" style="color:#8a8a8a">Instagram</a>
    &nbsp;·&nbsp; <a href="{{% unsubscribe_url %}}" style="color:#8a8a8a">Unsubscribe</a><br>
    {{{{ organization.name }}}} · {{{{ organization.full_address }}}}
  </td></tr>
</table></td></tr></table></body></html>"""

def eyebrow(t):
    return f'<tr><td class="pad" align="center" style="padding:0 48px 14px;font:400 14px/1.4 {SANS};color:#000000">{t}</td></tr>'

def h1(t):
    return (f'<tr><td class="pad h1" align="center" style="padding:0 48px 26px;font:400 46px/1 {SERIF};'
            f'text-transform:uppercase;letter-spacing:-.005em;color:#000000">{t}</td></tr>')

def text(t, pad="0 64px 28px"):
    return f'<tr><td class="pad" align="center" style="padding:{pad};font:400 16px/1.6 {SANS};color:#000000">{t}</td></tr>'

def image(src, alt, link=SITE + "/shop"):
    return (f'<tr><td class="pad" style="padding:0 48px 36px"><a href="{link}"><img src="{src}" width="504" alt="{alt}" '
            f'style="width:100%;max-width:504px;height:auto;border-radius:6px"></a></td></tr>')

def button(label, href):
    return (f'<tr><td align="center" style="padding:4px 48px 44px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
            f'<td bgcolor="#000000" style="background:#000000"><a href="{href}" style="display:inline-block;padding:17px 44px;'
            f'font:500 12px/1 {SANS};letter-spacing:.14em;text-transform:uppercase;color:#ffffff;text-decoration:none">{label}</a>'
            f'</td></tr></table></td></tr>')

def code(note):
    return (f'<tr><td class="pad" align="center" style="padding:0 48px 30px"><table role="presentation" cellpadding="0" cellspacing="0" '
            f'style="border:1px solid #000000"><tr><td align="center" style="padding:18px 34px">'
            f'<div style="font:400 11px/1 {SANS};letter-spacing:.14em;text-transform:uppercase;color:#6b6b6b;padding-bottom:10px">{note}</div>'
            f'<div style="font:400 30px/1 {SERIF};letter-spacing:.06em;color:#000000"><span style="padding:2px 8px 0;'
            f'background-color:#fbe84a;background-image:linear-gradient(176deg,#ffffff 0%,#ffffff 42%,'
            f'#fbe84a 44%,#f6df3c 90%,#ffffff 93%);border-radius:3px 6px 4px 7px">{CODE}</span></div></td></tr></table></td></tr>')

def trio(items):
    cells = "".join(
        f'<td class="col" width="33%" valign="top" style="padding:0 6px"><a href="{SITE}/product-page/{slug}" style="text-decoration:none;color:#000000">'
        f'<img src="{src}" width="160" alt="{name}" style="width:100%;height:auto;border-radius:6px">'
        f'<div style="font:400 22px/1 {SERIF};text-transform:uppercase;padding:12px 0 4px">{name}</div>'
        f'<div style="font:400 13px/1 {SANS};color:#6b6b6b">$220</div></a></td>' for name, slug, src in items)
    return (f'<tr><td class="pad" style="padding:0 42px 40px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr>{cells}</tr></table></td></tr>')

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
    body=eyebrow("Studio Maçon") + h1("Small things,<br>kept close") + image(HERO1, "Eleph, a small bronze totem")
       + text("Maçon makes artifacts and jewelry to be carried, worn and handed down. Each piece is drawn on paper, "
              "carved by hand in wax and cast in bronze, silver or gold, then finished by hand in the studio.")
       + code("10% off a first piece") + button("See the pieces", SITE + "/shop")
       + text("A few to start with", "8px 48px 18px") + trio(PIECES)),
 "welcome-2": dict(
    subject="How a Maçon piece is made",
    preview="Drawn on paper, carved in wax, cast in metal, finished by hand.",
    body=eyebrow("Field notes") + h1("Carved by hand,<br>born of fire")
       + text("No two pieces leave the studio quite alike. The patina is built up by hand, and it keeps changing: "
              "it darkens where the thumb rests and brightens where it rubs, recording how it is held.")
       + steps() + code("Still yours for a first piece") + button("Choose a piece", SITE + "/shop")),
 "welcome-3": dict(
    subject="Your welcome code closes soon",
    preview="MACON10 is good for two more days.",
    body=eyebrow("A last note") + h1("Meant to<br>be held") + image(HAND, "Ren, held in the palm of a hand")
       + text("Every piece is made to order, so it is made for whoever asks for it. "
              "The welcome code is good for two more days.")
       + code("10% off, two days left") + button("Choose a piece", SITE + "/shop")),
}

# ── flows that show the shopper's own pieces (Klaviyo fills these in) ──────────────
def items(loop, title, image, price, link):
    """One row per piece, filled in by Klaviyo. For the preview, one sample row stands in."""
    row = (f'<tr><td style="padding:0 0 16px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
           f'<td width="120" valign="top"><a href="{link}"><img src="{image}" width="120" alt="" style="width:120px;height:auto;border-radius:6px"></a></td>'
           f'<td valign="middle" style="padding-left:20px"><div style="font:400 26px/1 {SERIF};text-transform:uppercase;color:#000000">{title}</div>'
           f'<div style="font:400 14px/1 {SANS};color:#6b6b6b;padding-top:8px">${price}</div></td></tr></table></td></tr>')
    return (f'<tr><td class="pad" style="padding:0 72px 20px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            + (f'{{% for item in {loop} %}}{row}{{% endfor %}}' if loop else row) + '</table></td></tr>')

CART = items("event.extra.line_items", "{{ item.product.title }}", "{{ item.product.images.0.src|missing_product_image }}",
             "{{ item.line_price|floatformat:0 }}", "{{ event.extra.checkout_url }}")
VIEWED = items(None, "{{ event.ProductName }}", "{{ event.ImageURL }}", "{{ event.Price|floatformat:0 }}", "{{ event.URL }}")
ORDER = items("event.extra.line_items", "{{ item.product.title }}", "{{ item.product.images.0.src|missing_product_image }}",
              "{{ item.line_price|floatformat:0 }}", SITE)
CHECKOUT = "{{ event.extra.checkout_url }}"

def notes(rows):
    cells = "".join(f'<tr><td style="padding:0 0 18px"><div style="font:400 22px/1 {SERIF};text-transform:uppercase;padding-bottom:6px">{t}</div>'
                    f'<div style="font:400 15px/1.6 {SANS};color:#333333">{d}</div></td></tr>' for t, d in rows)
    return (f'<tr><td class="pad" style="padding:4px 72px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'{cells}</table></td></tr>')

EMAILS.update({
 # Abandoned checkout (trigger: Checkout Started; exit if Placed Order). 1: after 4 hours. 2: after 2 days.
 "checkout-1": dict(
    subject="Left on the bench",
    preview="The piece is waiting where you left it.",
    body=eyebrow("Your bag") + h1("Left on<br>the bench") + CART
       + text("Every Maçon piece is made to order once it is chosen, so nothing is lost by taking a moment. "
              "The checkout is saved exactly as it was.") + button("Return to checkout", CHECKOUT)),
 "checkout-2": dict(
    subject="A question about your piece?",
    preview="Sizing, patina, timing: the studio answers every note.",
    body=eyebrow("Your bag") + h1("Still<br>deciding?") + CART
       + notes([("Sizing", "Rings can be made in any size. If the fit is not right, the studio will make it right."),
                ("Timing", "Each piece is made to order and leaves the studio within about ten business days."),
                ("Questions", 'A reply to this email reaches the studio directly, at <a href="mailto:hello@studiomacon.co">hello@studiomacon.co</a>.')])
       + button("Return to checkout", CHECKOUT)),
 # Browse abandonment (trigger: Viewed Product; skip if they checked out or were emailed in the last day). After 1 day.
 "browse-1": dict(
    subject="{{ event.ProductName }}, still on your mind?",
    preview="A second look at the piece you were studying.",
    body=eyebrow("A second look") + h1("Still<br>on your mind") + VIEWED
       + text("Every piece is drawn, carved in wax and cast by hand, then finished in the studio in California. "
              "No two leave quite alike.") + button("Take another look", "{{ event.URL }}")),
 # Post-purchase (trigger: Placed Order). 1: straight away. 2: after 21 days.
 "thanks-1": dict(
    subject="Your piece is being made",
    preview="What happens between now and its arrival.",
    body=eyebrow("Thank you") + h1("Your piece<br>is being made") + ORDER
       + notes([("Made to order", "The piece is being made for you now, in the studio in California."),
                ("On its way", "It leaves the studio within about ten business days. A tracking link follows when it ships."),
                ("Questions", 'A reply to this email reaches the studio directly, at <a href="mailto:hello@studiomacon.co">hello@studiomacon.co</a>.')])),
 "thanks-2": dict(
    subject="How to care for your piece",
    preview="Bronze and silver, and how they change with handling.",
    body=eyebrow("Care notes") + h1("Meant to<br>be handled") + image(HAND, "A small bronze totem held in the palm")
       + notes([("Bronze", "The patina darkens where the thumb rests and brightens where it rubs. "
                           "To keep it as it is, wipe with a soft dry cloth. Avoid polish; it takes the patina with it."),
                ("Silver", "Silver darkens slowly in the air. A polishing cloth brings it back; wearing it often does the same."),
                ("Share it", 'Photographs of Maçon pieces in their new homes are always welcome: '
                             '<a href="https://www.instagram.com/studiomacon/">@studiomacon</a>.')])
       + button("See the other pieces", SITE + "/shop")),
})

os.makedirs(os.path.join(PDP, "email"), exist_ok=True)
for name, e in EMAILS.items():
    with open(os.path.join(PDP, "email", name + ".html"), "w", encoding="utf-8") as f:
        f.write(page(e["preview"], e["body"]))
    print(f"{name}.html   subject: {e['subject']}   preview: {e['preview']}")
