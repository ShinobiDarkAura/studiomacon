#!/usr/bin/env python3
"""Generate seed-pages.sql — the current page copy expressed as editor blocks.

Without this, opening a page in the admin would show an empty editor and the
first save would wipe the built-in copy. Seeding means editing starts from
exactly what is on the site today.
"""
import json, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PAGES = {
    "story": {
        "title": "Our Story",
        "body": [
            {"type": "h3", "text": "Our Practice"},
            {"type": "lead", "text": "Each piece begins as a sketch on paper. Next, the object is carved by hand — first in wax, then fine-tuned in metal. We work closely with a local foundry to cast the wax carvings in bronze, silver or gold. Each piece is then refined and polished in our studio."},
            {"type": "p", "text": "If its path is to become a collection piece, a rubber mold is made so that we can make the children of that original and share them with you. If it's a custom piece, it is one of a kind."},
            {"type": "steps", "items": [
                {"src": "images/content/draw.png", "caption": "Concept & Sketch"},
                {"src": "images/content/cast.png", "caption": "Carve & Cast"},
                {"src": "images/content/polish.png", "caption": "Polish & Patina"},
            ]},
            {"type": "h3", "text": "Our History"},
            {"type": "p", "text": "Maçon is based in southern California, but Alex and Hannah met at RISD in 2008. They had figure drawing class together freshman year and quickly became close friends."},
            {"type": "p", "text": "After graduating college, their resilient love for each other — despite gaps in distance and time — never waned. Eventually they found their way back to each other and married in 2023. Both Maçon and their union were born out of their desire to live and create as one."},
            {"type": "twoup", "src1": "images/content/hannah.png", "alt1": "Hannah as a child",
             "src2": "images/content/alex.png", "alt2": "Alex as a child"},
            {"type": "lead", "text": "We discover by holding."},
            {"type": "p", "text": "Maçon was founded by two creative and life partners, Alex and Hannah. Their work is inspired by ancient artifacts and the intimate and personal objects they cared for when they were children."},
            {"type": "img", "src": "images/content/hand-milo.png", "alt": "Hand holding Milo"},
        ],
    },
    "custom": {
        "title": "Custom Heirlooms",
        "body": [
            {"type": "lead", "text": "Let's make something real together."},
            {"type": "html", "html": "It's a rare privilege to create custom heirlooms to honor a special moment. If you're interested in commissioning a piece for yourself or someone you love, <a href=\"contact.html\">reach out to us here</a>."},
            {"type": "img", "src": "images/content/lorenz.jpg", "alt": "Lorenz Ring, 2023"},
            {"type": "caption", "text": "Lorenz Ring, 2023"},
            {"type": "twoup", "src1": "images/content/custom-2.jpg", "alt1": "Custom work",
             "src2": "images/content/custom-3.jpg", "alt2": "Custom work"},
        ],
    },
    "shipping": {
        "title": "Shipping & Returns",
        "body": [
            {"type": "h3", "text": "Shipping"},
            {"type": "p", "text": "Each piece is individually made to order; please allow up to 10 business days for us to create your piece before it heads out to you."},
            {"type": "p", "text": "Standard shipping takes 3–7 business days for delivery, while international shipping generally takes 5–10 business days depending on shipping destination."},
            {"type": "h3", "text": "Returns"},
            {"type": "p", "text": "We will accept pieces (excluding custom work) in their original condition for store credit towards your next purchase. For pieces that don't fit properly, we will gladly work with you to find the right size. Returns and exchanges must be initiated within 14 days of the delivery date."},
            {"type": "html", "html": "<a href=\"mailto:hello@studiomacon.co?subject=Hi!%20I%27d%20like%20to%20start%20a%20return.\">Contact us</a> to initiate a return. Include your order number and please let us know the reason for your return. After your return has been successfully processed, you will receive store credit and a confirmation email."},
            {"type": "img", "src": "images/content/olive-branch.png", "alt": "Olive branch", "style": "max-width:340px"},
        ],
    },
    "contact": {
        "title": "Contact",
        "body": [
            {"type": "html", "html": "<a href=\"https://www.instagram.com/studiomacon/\">@studiomacon</a> &nbsp;&middot;&nbsp; <a href=\"mailto:hello@studiomacon.co?subject=Hi%20there!\">hello@studiomacon.co</a>"},
        ],
    },
}

def q(s):
    return "'" + str(s).replace("'", "''") + "'"

out = ["-- Studio Maçon — seed page bodies as editor blocks (generated; safe to re-run)",
       "begin;", ""]
for key, p in PAGES.items():
    body = json.dumps(p["body"], ensure_ascii=False)
    out.append(f"insert into public.store_pages (key,title,body) values "
               f"({q(key)},{q(p['title'])},{q(body)}::jsonb)\n"
               "on conflict (key) do update set title=excluded.title, body=excluded.body;")
out += ["", "commit;"]
open("seed-pages.sql", "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"wrote seed-pages.sql — {len(PAGES)} pages, "
      f"{sum(len(p['body']) for p in PAGES.values())} blocks")
