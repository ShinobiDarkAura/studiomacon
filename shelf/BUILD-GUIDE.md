# Maçon — Shelf Concept, build guide

### v3 — re-derived for the self-hosted stack (August 2026)

An alternate visual treatment of the existing store: same 18 pieces, same copy, same
Supabase content, presented as photographic shelf environments with the objects as set
dressing rather than as a card grid.

This supersedes `macon-wix-studio-build-guide.md` (v2, June 2026), which was written for
Wix Studio. The site has since moved to the static build in this repo, so roughly a third
of v2 is workarounds for constraints that no longer apply. The art direction in v2 is
sound and is kept almost intact; the architecture is replaced.

**This is an experiment that runs alongside the live design. It never modifies it** — see
§10 for the isolation rules, which are load-bearing, not politeness.

---

## 1. What the move off Wix changes

v2's architecture exists because of one constraint, stated plainly in its §1: Wix's
repeater produces a regular grid, and there is no way to bind a CMS collection to freely
positioned, overlapping elements. That forced a split into a dynamic commerce layer and a
hand-composed "stage layer," with every object placed by hand in an editor and every link
re-audited after each duplication.

None of that holds here. `build.py` is a generator: it reads content and writes HTML.
Emitting a product at an arbitrary coordinate is a formatted string.

| v2 constraint (Wix) | Here |
|---|---|
| Layout can't be CMS-driven → hand-place each object | Positions come from data; the page is generated |
| Image source can't vary per breakpoint → focal-point crop | `<picture>` with `media` — a real mobile plate |
| Elements hidden per breakpoint still download | Only the matching `<source>` is fetched |
| No hover source swap → stack a 2nd image at 0% opacity | Same stacking idea, already shipping as `.ci-lead`/`.ci-alt` |
| Each animated target needs its own interaction entry | CSS |
| Links inside reused sections reset | Not a concept that exists here |
| Custom cursor per element, per breakpoint | `cursor: url(...)`, same capability |

What survives from v2, and should be treated as settled: the locked light direction, baked
contact shadows, the refusal of handwriting fonts, the typographic ceiling, no parallax,
and the Index section as the real mobile shopping path. Those are art-direction calls, not
platform accommodations.

**One v2 instinct to drop deliberately.** Its §1 argues hand-curation is "the right call,
not a compromise — museum vitrines are curated by hand," and caps the homepage at 8–15
hero objects. That was making peace with a limitation. Curation stays a human decision,
but it is expressed as data (which piece, which shelf, which coordinate) rather than as
manual placement, so a seasonal re-dress is an edit to one JSON file instead of an
afternoon in an editor.

---

## 2. Architecture

One generator, `shelf/build_shelf.py`, writing to `shelf/_site/`.

It reuses `build.py`'s helpers rather than reimplementing them. The repo already
establishes this idiom in `make_register_mockup.py`: read `build.py`, split off everything
before `if __name__ == "__main__":`, and `exec` that into a namespace.

```python
src = open("build.py", encoding="utf-8").read().split('if __name__ == "__main__":')[0]
B = {"__file__": os.path.abspath("build.py")}
sys.argv = ["build.py", "--offline"]
exec(compile(src, "build.py", "exec"), B)
```

One difference from `make_register_mockup.py`: it does `os.chdir` to its own directory
because it sits at the repo root. `build_shelf.py` lives one level down, so it must chdir
to the **repo root** so that `build.py`'s relative paths (`_source/`, `images/`) resolve.

What gets reused as-is:

- `derive(src, width)` — writes a webp derivative and returns its path. `SIZES` is
  `(200, 800, 1800)`, but arbitrary widths work; the in-flight edition seal already calls
  it at 400.
- `srcset(src)`, `images_for(p)`, `pick_variant(imgs, want)`
- `is_public(p, now)`, `buyable(p)` — status and release-date gating
- `page(title, body, up, desc)` for the document shell

What is **not** reused: `nav()`, `footer()`, `card()`, and `assets/site.css`. The shelf
concept has its own chrome and its own stylesheet (`shelf/shelf.css`). Sharing the
stylesheet is what would eventually force an edit to the live design.

Content comes from `_source/content-cache.json` — currently 18 products, all
`collection: perennial`, all `status: live`, plus `pages` and `settings`
(`tagline`, `hero_image`). Run offline against the cache; there is no reason for this
experiment to hit Supabase at all.

---

## 3. The composition file — the thing v2 couldn't have

Positions live in `shelf/composition.json`, checked in, hand-edited. **Not in Supabase.**
The Supabase project is shared with macon-archive and with the live store; adding columns
for an experiment is exactly the kind of coupling this experiment is supposed to avoid.

Shape:

```json
{
  "scenes": [
    {
      "id": "threshold",
      "plate": "shelf/plates/plate-threshold.jpg",
      "plate_mobile": "shelf/plates/plate-threshold-9x16.jpg",
      "height": "96vh",
      "objects": [
        {
          "slug": "milo",
          "x": 0.34, "y": 0.62, "w": 0.13,
          "x_mobile": 0.5, "y_mobile": 0.55, "w_mobile": 0.46,
          "label": "shelf/labels/label-milo.webp",
          "label_dx": 0.02, "label_dy": 0.10, "rotate": -1.5
        }
      ]
    }
  ]
}
```

Coordinates are **fractions of the plate**, not pixels — the plate scales, so the objects
must scale with it. `x`/`y` are the object's anchor within the plate; `w` is its width as
a fraction of plate width. Height follows from the cutout's aspect ratio, so it is never
specified and the object can never be squashed.

Rules the generator enforces, rather than trusting the JSON:

- Every `slug` must exist in the content cache and pass `is_public` — a piece pulled from
  the store must not linger on a shelf. Unknown or non-public slugs fail the build loudly.
- Every piece in the catalogue appears in the Index (§4.5) whether or not it is on a
  shelf. The shelves are a selection; the Index is the record.
- Objects within a scene are emitted in `y` order, so nearer-the-front objects overlap
  correctly without hand-managed `z-index`.

---

## 4. Page structure

Homepage as stacked scenes, each 90–110vh. Not all exactly 100vh; uniform full-viewport
sections read as a slide deck.

**4.1 Threshold** — the quietest plate, nearly empty. One object, one label. Brand mark
small and letterspaced, top-left. No tagline, no CTA. This is the LCP element, so it is
the lightest plate on the page.

**4.2 Shelf I — Bronze** — 3–4 objects, window light from the locked direction.

**4.3 Interlude** — full-bleed detail photograph. No products, no links. The repo already
has usable material here: `images/content/` holds transparent PNGs of casting, polishing,
drawing, and hands.

**4.4 Shelf II — Rings & Silver** — different shelf depth, same light direction.

**4.5 Index** — text-only list of every piece: name, material, price, linked to the
product page. Set as a museum checklist. This is the accessibility and SEO floor and the
primary mobile path, so it is real markup that happens to be sparse — never a decorative
afterthought, never `display:none` at any breakpoint.

**4.6 Colophon** — studio line, contact, newsletter.

Each object's click target is one generous anchor wrapping cutout + label + price, with
descriptive text ("Milo — solid bronze, view piece"). No add-to-cart on the shelves; the
tone dies the moment a button appears in the scene. Cart lives on the product page.

Product pages themselves are **out of scope for v1** — shelf links point at the existing
`product/*.html`. Restyling those is a later decision, and keeping them shared means the
experiment can be judged on the homepage idea alone.

---

## 5. Asset pipeline

Still the bulk of the work, but the method changed once it was tested. v2 assumed the
shadow would be fabricated. It is now measured, because a generated relight produces a
physically correct one for free.

**Sprites — the round trip.** `shelf/tools/harvest.py`, one piece at a time:

```
real photo -> cutout (reference)
           -> generated lighting rig  (GPT Image 2, the cutout as reference)
           -> object + its baked shadow, lifted back out as one RGBA sprite
```

The generated image is a **lighting rig, not a set**: the piece on a plain seamless
ground, nothing else in frame. The room comes from the plate. Asking for the full
archival scene instead puts a shelf edge, uprights and boxes in frame, and the shadow
recovery (which measures how much darker a pixel is than the bare surface should be)
harvests all of it as shadow.

`rembg` returns only the object, so the shadow is recovered separately: a greyscale
morphological closing gives a shadow-free estimate of the ground, and the ratio between
the two is the darkening. It is stored as alpha over a warm dark so it multiplies
correctly onto any plate. The result is bounded to the object's own footprint,
asymmetrically — light is camera-left, so the cast falls right.

**Plates — by emptying the references, not describing them.** `shelf/tools/plates.py`
feeds each concept image back in and asks only for the objects to be removed. Writing a
plate from a description produced something cleaner and more architectural than the refs
— clean stone, grey steel, a room rather than a mood. Emptying preserves the ivory grade,
the bleached timber, the straight-on camera and the window shadows on the plaster. It also
makes the plate's light *the same light* the sprites were rendered under, so the two agree
by construction.

**Scale comes from the catalogue, off the longest dimension.** The `notes` field carries
millimetres, but the axis order is inconsistent — Milo's `36 x 26 x 11` is width-first,
Rebi's `42 x 16 x 16` must be height-first or a sitting rabbit would be three times wider
than tall. Taking the largest number and mapping it to the object's longest pixel axis is
ordering-agnostic and correct for all of them. Not every piece has dimensions recorded;
those need measuring or a per-piece override.

**Source photos need curating.** The batch cannot take image #1 — `pip`, `ori` and `yael`
all lead with in-hand shots, which are unusable as references. An explicit
slug -> plain-photo map is required.

**Labels.** Written physically in grease pencil on warm paper and scanned, or generated
with a consistent plaster treatment. Not a handwriting font — every handwriting font reads
as a font. Slight rotation, inconsistent baselines, small.

Naming: `shelf/plates/plate-<scene>.png`, `shelf/scenes/scene-<piece>.png`,
`shelf/sprites/<piece>.png` + `.json`, `shelf/cutouts/obj-<piece>.png`.

---

## 6. Typography

- **Inventory/utility:** EB Garamond or Cormorant Garamond, 13–15px, ~0.02em tracking.
  Prices set here.
- **Brand mark / eyebrows:** the same face in small caps, 0.12–0.18em, 11–13px.
- **Body:** Garamond 16–17px, 1.6 leading, ≤55ch.

Refuse display type above ~28px, bold weights, and any sans beyond tiny functional UI. The
handwritten labels are the display typography. Ink is a warm near-black (~#2B2722), never
pure black.

**This resolves an open blocker by side-stepping it.** `PLAN.md` flags that Index, Louize,
and Swim Club Wide are licensed for Wix and that self-hosting is a separate use requiring
confirmation or a new licence before public launch. Both Garamonds are freely
self-hostable, so this concept carries no font-licensing exposure and does not wait on
that question.

---

## 7. Interactions

All CSS. No panel bookkeeping, no per-target entries.

- **Hover:** crossfade the hover cutout over the normal one, ~500ms ease-out. The existing
  `.ci-lead`/`.ci-alt` pattern in `assets/site.css` is the working precedent — same idea,
  new class names local to `shelf.css`.
- **Cursor:** a small graphite mark on hotspots via `cursor: url(...)`, default everywhere
  else.
- **Scroll entrance:** gentle opacity fade on labels and prices only, completing early in
  the viewport. Plates and objects get no entrance — they should feel like they were
  always there.
- **No parallax.** Fastest way to read as a template.
- Nothing may *depend* on hover: touch devices never fire it, so the anchor carries the
  full interaction by itself.

Respect `prefers-reduced-motion` by disabling the entrance fades and the crossfade.

---

## 8. Performance and SEO

Wix's CDN did the image work automatically; here it is ours, and the tools are already in
the repo.

- `derive()` + `srcset()` already produce webp at multiple widths — reuse them for cutouts
  and plates rather than hand-exporting sizes.
- Plates are large. Everything below the fold gets `loading="lazy"`; the Threshold plate
  does not, and should be the lightest on the page.
- Use `<picture>` with `media` for the plate so a phone downloads only the 9:16 crop. This
  is the concrete win over v2, which had to pay for both.
- `PLAN.md` already lists image performance as open — a few transparent product shots are
  2–3MB. Transparent cutouts will make that worse before better; budget for it.
- SEO rests on the Index: real crawlable links and text for all 18 pieces. Alt text written
  by hand per object. H1 is the small brand mark.

---

## 9. Build order

1. ~~Go/no-go: does a catalogue-lit piece sit in window light?~~ **Done — yes.** See §11.
2. ~~Harvest pipeline, proven on three pieces.~~ **Done.**
3. ~~Bare plates.~~ **Done — three, emptied from the references.**
4. Curate the slug -> plain-photo map, then harvest the remaining 15 pieces. Every one is
   scored; anything flagged `REVIEW` or `CLIPPED` is re-rolled, not shipped.
5. `composition.json` + `build_shelf.py` emitting one scene, desktop and mobile. This
   replaces the ad-hoc compositing used for the previews.
6. That scene is the design system. Tune it until it holds, then add scenes.
7. Index, Threshold, Interlude, Colophon.
8. Test: real-phone tap targets (≥48px), a load waterfall on mobile, and the squint test —
   squinting, it should read as a photograph of a room, not a website.

---

## 10. Isolation rules

The live design must be unaffected at every point.

- All new files live under `shelf/`. Output goes to `shelf/_site/`, never `_site/`.
- `build.py`, `assets/site.css`, `assets/site.js`, `index.html`, and `product/*.html` are
  **read-only** to this experiment. `build_shelf.py` reads `build.py`; it never writes it.
  If something in `build.py` genuinely needs to change, that is a separate decision made
  on `main`, not a side effect here.
- No schema changes to Supabase. Composition data is local JSON. The experiment runs
  `--offline` against the content cache.
- Shared, and deliberately so: `_source/content-cache.json`, `images/` and its 201MB of
  derivatives, and the product pages the shelves link to. Sharing these is why this lives
  in a subdirectory instead of a separate repo — duplicating 201MB to prove a layout idea
  is not a real form of safety.
- Work stays on the `shelf-concept` branch.

There is uncommitted work on `main` from 4 August (a PDP redesign, edition seals, and a
rewritten copy pass). It is untouched and still uncommitted. Do not fold it into this
branch's commits.

---

## 11. What the tests established

Recorded because several of these contradict what was assumed going in.

**Identity survives the round trip.** The worry was that a generated relight would return a
plausible object rather than the actual merchandise. Measured as silhouette IoU against the
real photo: Milo 0.983, Ren 0.979, Rebi 0.985, Zuma Ring 0.965. The ring was expected to be
the hard case — thin section, a hole through it, specular highlights that *are* the product
— and it held. Texture comes back slightly regularised, invisible at shelf scale but a
reason to keep the real photographs on product pages.

**Every harvest is scored anyway.** Fidelity is checked per piece, not spot-checked, and
written into the sidecar with a verdict. Two distinct failures are separated:

- `REVIEW` — IoU below 0.95. Genuine drift.
- `CLIPPED` — the subject touches the frame edge. Different failure, and it makes the
  score *lie*: a truncated silhouette normalised to the same height reads as a fatter
  object, so drift is overstated. Rebi first scored 0.827 and looked like real drift;
  reframed on a portrait canvas it scored 0.985. Hence `frame_size()` matching the canvas
  to the piece's proportions.

**A stray pixel corrupts everything downstream.** The base anchor, the placement scale and
the fidelity score are all derived from the alpha bounding box. One detached speck in a
cutout put Rebi's measured IoU at 0.084 on images that were nearly identical. `clean_alpha()`
drops components below 2% of the largest; without it a batch fails silently.

**Model choice, not matting, cuts a ring.** `u2net` segments the outer silhouette only and
returns any ring as a solid disc. The obvious repair — key out backdrop-coloured pixels
enclosed by the silhouette — fails on exactly this case, because brushed silver and warm
linen sit at nearly the same tone, so it eats the band along with the hole.
`isnet-general-use` cuts the opening natively.

**Pin onnxruntime to CPU.** Left to itself it selects the CoreML provider and recompiles the
170MB model to an `.mlmodelc` on every run, in a system daemon — the Python process sits at
~0% CPU and looks hung, and the compile is cached per-process so it never amortises.
Pinning to `CPUExecutionProvider` took each cutout from minutes to seconds.

**rembg needs the network even when cached.** `BaseSession.__init__` resolves the model path
through `download_models()`, which calls `pooch.retrieve()` unconditionally. `offline_session()`
overrides that one classmethod and keeps rembg's own normalize/predict.
