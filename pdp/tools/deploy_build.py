#!/usr/bin/env python3
"""Assemble the folder that goes to Cloudflare Pages.

Only what a visitor loads, plus the JPEGs Shopify fetches for product images.
The editor, the photographs as shot, the builder and the page sources stay home.
"""
import csv, glob, os, re, shutil, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(HERE), "dist")

KEEP_FILES = (".html", ".css", ".xml", ".txt", ".ico", ".webmanifest", ".csv")
KEEP_DIRS = ("img", "video", "fonts")
SKIP_DIRS = {"_editor", "_originals", "_picker", "tools", "partials", "pages", "shopify", "_source"}


def used_media():
    """Only the video and posters the built pages actually ask for.

    film.mp4 is the 42MB source the process cut was made from; it has no place
    on a web server.
    """
    out = set()
    for f in glob.glob(os.path.join(HERE, "*.html")):
        doc = open(f, encoding="utf-8").read()
        for m in re.findall(r'(?:src|poster)="(video/[^"]+)"', doc):
            out.add(os.path.normpath(m))
    return out


def wanted_jpgs():
    """The product pictures Shopify pulls in on import."""
    out = set()
    csv_path = os.path.join(HERE, "shopify", "product-images.csv")
    if os.path.exists(csv_path):
        for row in csv.DictReader(open(csv_path)):
            out.add(row["Image Src"].split("studiomacon.co/", 1)[-1])
    return out


def referenced():
    """Every picture any page or stylesheet names, however it names it: <img>, CSS url(), or script.
    The logotype letters, for one, are drawn from CSS and never appear as an <img>."""
    out = set()
    for f in os.listdir(HERE):
        if f.endswith((".html", ".css", ".csv", ".xml")) and f != "template.html":          # the product feeds name photos too
            with open(os.path.join(HERE, f), encoding="utf-8") as fh:
                # the whole name, double extensions included (hero.jpg.webp is not hero.jpg)
                out.update(re.findall(r'(img/[^"\'()\s,]+\.(?:png|jpe?g|webp|svg|gif))(?![\w.])', fh.read()))
    return {os.path.normpath(x) for x in out}


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    keep_jpg = wanted_jpgs()
    used = used_media()
    named = referenced()
    n = 0
    for root, dirs, files in os.walk(HERE):
        rel_root = os.path.relpath(root, HERE)
        parts = rel_root.split(os.sep)
        if parts[0] in SKIP_DIRS:
            dirs[:] = []
            continue
        for f in files:
            rel = os.path.normpath(os.path.join(rel_root, f))
            top = rel.split(os.sep)[0]
            take = False
            if os.sep not in rel and f.endswith(KEEP_FILES) and f != "template.html":
                take = True
            elif top == "video":
                take = rel in used
            elif top in KEEP_DIRS:
                take = f.endswith((".webp", ".mp4", ".woff2", ".jpg" if rel in keep_jpg else ".webp"))
                if f.endswith(".jpg"):
                    take = rel in keep_jpg
                elif f.endswith((".png",)):
                    take = not os.path.exists(os.path.join(root, f + ".webp"))
            elif f in ("_redirects", "_headers"):
                take = True
            if rel in named:                               # named somewhere: always ship it
                take = True
            if not take:
                continue
            dst = os.path.join(OUT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)
            n += 1
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs)
    print(f"{n} files, {size/1048576:.0f} MB -> {OUT}")


if __name__ == "__main__":
    main()
