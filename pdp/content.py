"""The studio's own copy and photograph choices, kept apart from the builder.

content.json holds only what Alex and Hannah have changed by hand in the editor
(pdp/_editor). Everything absent from it falls back to the defaults in
build_pdp.py, so the file stays small and readable, and deleting an entry
restores the original wording.
"""
import json, os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.json")


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            c = json.load(f)
    except (FileNotFoundError, ValueError):
        return {"products": {}, "pages": {}}
    c.setdefault("products", {})
    c.setdefault("pages", {})
    c.setdefault("shared", {})          # wording used by every piece of a kind
    return c


def save(c):
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1, ensure_ascii=False)
    os.replace(tmp, PATH)


CONTENT = load()


def product(slug, field, default):
    """One edited field for a piece, or the builder's own value."""
    v = CONTENT["products"].get(slug, {}).get(field)
    return default if v in (None, "") else v


def shared(key, default):
    """Copy that several pages have in common: care notes for a kind of piece, the
    shipping paragraphs. Editing it on one page changes it everywhere it appears."""
    v = CONTENT["shared"].get(key)
    return default if v in (None, "") else v


def page(key, default):
    v = CONTENT["pages"].get(key)
    return default if v in (None, "") else v
