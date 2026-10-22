# Retired previews

Each `.patch` here is one of the old local previews (`pdp/_variant-<name>/`), saved as the difference between
its source files and the live `pdp` at the commit named on its first line. Photos and the built pages are not
in them: `build_pdp.py` makes the pages, and the photos are the site's own.

| Patch | What the preview was |
|---|---|
| `cards.patch` | Home grid cards made like the "For Someone You Know" cards (rounded, gaps, sentence-case names) |
| `collection.patch` | A collection page (`collection.html`, `pages/collection.html`) |
| `editorial.patch` | An editorial pass on the product pages and copy |
| `jewelry.patch` | An optional left anchor in `tools/grey_backdrop.py` |
| `local.patch` | A local layout test of the product pages and home grid |
| `story.patch` | The Story page collage and moodboard tools (`collages.html`, `make_collage.py`, `make_moodboard.py` ...) |

The golden preview held only comparison images (Chrysalis hero, logo deboss options), not source, so it has no patch.

Some previews are older than later work on the live site, so a shared file (say `build_pdp.py`) can show older
lines as changes. Read a patch for the idea and lift the parts you want, rather than applying it whole.

## Bringing one back as a preview

```bash
cd ~/Documents/git/studiomacon/pdp
mkdir -p _variant-story/pdp && for e in $(ls -A | grep -v '^_variant\|^_before'); do cp -cR "$e" _variant-story/pdp/; done
ln -s ../../_source _variant-story/_source && ln -s ../../product _variant-story/product
cd _variant-story && patch -p1 --dry-run < ../tools/previews/story.patch
```

Drop `--dry-run` once it applies cleanly, then run `python3 build_pdp.py` inside `_variant-story/pdp`. Hunks that
no longer fit (because the live file has moved on) are left as `.rej` files to merge by hand.
