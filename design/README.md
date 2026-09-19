# Studio Maçon — Design System

The canonical reference for anything designed in the Maçon brand. It was **extracted** from what the site and the emails actually do (`pdp/site.css`, `pdp/template.html`, `pdp/pages/*.html`, the CSS injected by `pdp/build_pdp.py`, `pdp/email/build_emails.py`) and checked against computed styles on the live preview at 390 × 844 and 1440 × 900. Nothing here was invented. Where the site clusters, a scale is named; where it does not, the outlier is kept and flagged.

The source under `pdp/` remains canonical. This folder describes it and does not change it.

## What is in the folder

| File | What it is |
|---|---|
| `index.html` | The design canon: principles, type specimen, colour with contrast ratios, spacing, radii, shadows, rules, motion, every component rendered live, email, voice, inconsistencies. Opens straight from disk. |
| `tokens.css` | Every token as a CSS custom property, with a comment saying where it is used. Also carries the `@font-face` rules (paths relative to this file). |
| `tokens.json` | The same tokens, machine-readable, `{"color":{"ink":{"value":"#000","use":"…"}}}` style, generated from `tokens.css`. |
| `components/` | One self-contained HTML page per component: anatomy, live variants and states, spec table, responsive notes, do/don't, source references. `_shell.css` is the shared page chrome. |
| `README.md` | This file. |

### Component pages

Site: `nav-header` · `menu-drawer` · `footer` · `type-hierarchy` · `eyebrow-label` · `prose` · `buttons` · `forms` · `product-tile` · `product-gallery` · `price-size` · `accordion` · `bag-line` · `bag-toast` · `stamp` · `scroll-cue` · `page-transitions` · `page-404`

Email: `email-eyebrow-title` · `email-image-card` · `email-code-box` · `email-button` · `email-friends-trio` · `email-notes-list` · `email-footer`

## How to use it

1. **Start from `index.html`.** Open it from disk. Everything links from there.
2. **Take values from `tokens.css`.** In new site work, `@import` or copy the variables; use `var(--r-photo)` rather than typing `6px`. In email, read the value out of the token (emails cannot use variables) and paste the inline style shown on the email component page.
3. **Copy components, do not redraw them.** Each component page has the site's exact CSS and markup. Copy it, then change copy and images only.
4. **When the site changes, change the tokens.** If a value in `pdp/` moves, update `tokens.css`, regenerate `tokens.json`, and fix the component page. This folder is only useful while it is true.
5. **Fonts.** `tokens.css` loads Instrument Serif (roman + italic) and Henry italic from `../pdp/fonts/`. Component pages get them by linking `../tokens.css`. The sans is system Helvetica Neue → Helvetica → Arial; never load a webfont for it.

## Principles observed

These are not aspirations; they are what the site already does everywhere.

- **Black on white, nothing else.** Every grey is black at an opacity (`rgba(0,0,0,.x)`), never a mixed hex. The only accent is `#c8321e` for a missed ring size and a required asterisk; the only yellow is the code highlighter in email.
- **The nav never has a background.** Menu / links, logotype and Bag float over whatever is beneath and read its luminance (`site.js`, threshold 0.82). Under 0.82 the whole row goes white (`.on-dark`). Product and Custom pages keep Bag black over their white right column on desktop (`body.white-right`).
- **Serif titles are always uppercase**, weight 400, line-height 1, tracked −.005em. Instrument Serif is never bold. Two italic exceptions: Story step names (17pt) and the film tagline in Henry (15pt).
- **Helvetica Neue does everything else.** Body 17/1.5; prose 17/1.55; overlines 13px uppercase .14em at 50%; buttons 15.33px uppercase .08em; nav 14.67px. Weight 500 appears only on a picked size, a summary total, the toast label and the email button.
- **Photographs sit in 6px frames on a `#f7f7f7` field.** Tiles, related cards, the phone hero, bag thumbnails, masonry. Full-bleed photographs have no radius. Emails use **16px** and the soft lift shadow (`0 18px 28px -12px rgba(0,0,0,.45), 0 4px 10px -4px rgba(0,0,0,.25)`), which on the site appears only under the bag line thumbnail.
- **Buttons are square and full width in their column.** 55px, black, arrow slides out to the right of the words on hover. Product page: 47px, type and arrow 15% smaller. Empty bag: outline. Custom steps: disabled at 10% opacity. There is no grey button and no rounded button.
- **Rules are hairlines.** 1px `#e3e3e3`, darkening to black on hover. Form fields are underlines only (.5px), never boxes. The size picker is the one bordered box.
- **One gutter on phones.** 16px from the screen edge for text, buttons and grids; Menu/Bag/Close a further 12px in (28px); the product hero and shop grid 8px in with 8px gaps. Every title centred on phones.
- **Space is generous and centred.** Page starts `head + 36px` down; sections 96px apart on phones, 140px on desktop; prose no wider than 620px; shop grid inset a further 7.5vw "so the pieces read smaller and calmer".
- **Things drift in.** `.dr-emerge`: from 66px below through a 16px blur over 1.1s on `cubic-bezier(.16,1,.3,1)`, staggered. Hover is unhurried: underlines .45s, tile zoom 1.2s, accordion .5s. `prefers-reduced-motion` switches all of it off.
- **Pieces are shown in the hand.** The tile hover image, the email hero, the bag thumbnail: held, worn, or resting at home.
- **The logotype is a mask, never an image.** `img/logotype.png` used as a CSS mask on `currentColor`, so it takes the nav's colour. 88px base, 108 on phones, 147 on desktop, aspect 888/331.

## Voice

- **Site copy is third-person field notes.** "Maçon makes…", "Each piece is…", "Bronze is meant to be handled." Present tense, no "we" or "I", no exclamation marks, no selling ("shop now", "limited", "buy").
- **Customer emails say "we".** "We're so glad you're here", "We saved it for you." Warm, still plain.
- **Never** "talisman" or "heirloom".
- **Pieces are artifacts**, not products or stock. Words that are Maçon: piece, artifact, totem, carried / worn / handed down, made to order, cast solid, patina, in the hand, the studio in California, Kindred, Field Notes, Also Worth Keeping.

## Token scales settled on

- **Colour:** `--ink` `--paper` `--field` `--rule` `--film` `--alert` + ink at opacity `--ink-08 … --ink-65` (14 steps in use; the clusters are rules .2–.25, faint .35–.45, muted text .5–.55) + placeholders/fields + email-only flat hex.
- **Serif type:** 22 · 26 · 30 · 30.4 · 31 · 34 · 35 · 38 · 38.83 · 42 · 46 · 53 · 54 · 57.5 · 60 · 66.25 · 75 (px). The genuine scale is **22 · 26 · 34 · 38 · 42 · 46 · 53 · 60 · 66 · 75**; the rest are near-duplicates listed below.
- **Sans type:** 11 · 12 · 13 · 14 · 15 · 16 · 17 · 19 (px), plus pt-derived fractions (11.67, 13.03, 14.33, 14.67, 15.33) that sit beside them.
- **Spacing:** 2 4 6 8 10 12 14 16 18 20 22 24 28 32 36 40 44 48 52 56 64 72 96 120 140 (px), then one-off section tops 180 / 204 / 236. The commonest gaps are 8 (phones) and 12 (desktop). Frame: `--pad` 24/40, edge = pad + 24 (48/64), `--head` 84/110, gutter 16, nav inset 28, photo inset 8.
- **Radii:** 6 (site photos) · 16 (email) · 4 (thumbnails) · 8 (toast) · 11 / 13 (pills) · 50% · 0 (everything else).
- **Shadows:** lift · peek · toast · panel.
- **Motion:** `--ease` (.22,.7,.2,1) house · `--ease-emerge` (.16,1,.3,1) arrival · `--ease-drawer` (.65,0,.25,1) · plus single-use gestures (settle, zoom, stamp, cedilla, fall, cue, info, wipe, fade in/out). Durations .2 / .25 / .3 / .35 / .45 / .5 / .6 / .7 / .9 / 1.1 / 1.2 s.
- **Z-index:** 1 · 2 · 3 · 15 (dock) · 20 (nav) · 50 (tool) · 59 · 60 (drawer) · 2147482000 (veil) · 2147483000 (wipe).
- **Breakpoints:** 767/768 (everything), 600 and 900 (shop grid columns; bag/checkout at 900), 1200 (h1 60, wall heads 75), 1600 (masonry 5), 620 (email).

## Inconsistencies and outliers found (not changed)

Each should be normalised in `pdp/`, then this folder updated.

1. **Eyebrow renders at 17px inside `.prose`.** `site.css` `.prose p{font-size:17px}` outranks `.eyebrow{font-size:15px}` (and its 10px margin), so the home welcome block and Story "Our Practice" eyebrow are 17px where every other eyebrow is 15/16. — `pdp/site.css` (.prose p, .eyebrow), `pdp/pages/shop.html`, `pdp/pages/story.html`. Fix: `.prose p:not(.eyebrow)` or give `.eyebrow` higher specificity.
2. **Three h2 scales.** Base h2 34/42 (`site.css`), Also Worth Keeping 42/53 (`template.html` `.related h2`), wall heads 57.5/66.25/75 (`pages/shop.html` `.wall-head h2`, `pages/inspiration.html`, `pages/custom.html` `.past-head h2`). The wall steps are not on the h1 scale (46/53/60).
3. **Two desktop tile-name sizes 0.83px apart.** Shop overlay `calc(49.5px - 8pt)` = 38.83px, lh .95, ls .01em (`pages/shop.html` `.piece .name`, `pages/custom.html` `.examples .over .name`); labels-under `calc(var(--tile-name) + 12pt)` = 38px, lh 1, ls 0 (`template.html` `.rel-name`, `pages/shop.html` labels-under). Pick one.
4. **Four field rules and three placeholder colours.** Default `.field` 1.5px rgba(0,0,0,.25) with `#777` placeholder (`site.css`, used unmodified nowhere); footer .5px rgba(0,0,0,.2) with .35 placeholder (`site.css` footer .field); contact and checkout .5px `#000` with .35 (`pages/contact.html`, `pages/checkout.html`); Custom `.line` .5px rgba(0,0,0,.2) with .22 (`pages/custom.html`); editor inputs 1px rgba(0,0,0,.25) (`pages/custom.html` `.ed`). Fix: make the default the hairline and drop the rest.
5. **Button type differs between site and email.** Site `.cta` 400 / 15.33px / .08em / 55px full-width; email `button()` 500 / 12px / .14em / 17px 44px padding, inline. — `site.css`, `email/build_emails.py`.
6. **Photo radius 6 vs 16.** Site photographs 6px, email 16px. Also the desktop overlay tile has no radius while the same tile with labels-under has 6px. — `site.css`/`template.html` vs `build_emails.py`; `pages/shop.html`.
7. **Overline sizes drift.** `.label` 13px .14em 50% (`site.css`); product Field Notes on phones 11.67px .08em black (`template.html` max-width 767); Custom step titles and `.terms dt` 11.67px .14em (`pages/custom.html`); Custom `.q .label` 13px black. Fix: one overline (13px .14em), colour by context only.
8. **pt-derived fractional sizes.** 14.33 (17px − 2pt), 14.67 (16px − 1pt), 15.33 (18px − 2pt), 13.03 (cta × .85), 11.67 (17px − 4pt), 30.4 (footer fine), 57.5 / 66.25 (wall heads). Round to 14 / 15 / 15 / 13 / 12 / 30 / 58 / 66 with no visible change. — `site.css`, `template.html`, `pages/shop.html`.
9. **Grey opacities used once.** .22 (Custom placeholder), .28 (dashed tile), .3 (locked step), .62 and .65 (locked step / number on hover). Neighbours .2 / .25 / .35 / .55 / .5 exist. — `pages/custom.html`, `site.css` `.acc-head .n`.
10. **Scrim .45 on the site, .42 in email.** `pages/shop.html` `.piece .over`; `build_emails.py` `items()`. Email h1 is a fixed 46 (40 on phones) while the site steps 46/53/60; email title 54 sits between the site's 53 and 60.
11. **Grid breakpoints off the main one.** Shop grid breaks at 600 and 900, bag/checkout at 900, everything else at 768. — `pages/shop.html` `.wall`, `pages/bag.html`, `pages/checkout.html`.
12. **Masonry gap 10 vs grid gap 8 on phones.** `pages/inspiration.html` and `pages/custom.html` `.examples` use 10px; `pages/shop.html` `.wall` uses 8px. Desktop both 12.
13. **Apple Pay button two sizes.** 47px / 16.6px on product (`template.html`), 55px / 23px on Custom (`pages/custom.html`).
14. **Voice: "we" on the site.** Story ("We work closely with a local foundry", "we can make the children of that original"), Contact ("We'd love to hear from you", "Bored at work?"), Shipping ("We accept pieces…", "we will gladly work with you"), product Shipping & Returns accordion ("we'll gladly help") and Custom ("Let's Make Something Real", "Notes for Us", "We never share your email") all break the third-person rule. — `pages/story.html`, `pages/contact.html`, `pages/shipping.html`, `pages/custom.html`, `build_pdp.py` `accordions()`.
15. **"talisman" survives in a slug.** `pdp/wonderhorn-talisman.html`, `pdp/img/wonderhorn-talisman/`, and the slug in `build_pdp.py` / `build_emails.py` / `content.json`. Not in visible copy, but in the URL.
16. **Related price colour.** Site `.rel-cost` rgba(0,0,0,.55) (≈ `#737373`); email trio price `#6b6b6b`; email body-secondary `#333` where the site uses black. — `template.html`, `build_emails.py`.
17. **Toast and drawer use their own radii and gaps.** Toast 8px radius (only 8px on the site); drawer link gap 24.8px (only fractional gap). — `site.css`.
18. **Section tops are one-offs.** 128 / 204 (closing), 236 (Story history), 180 + 10vh (related), 120 + 10vh (set spacer), 25vh (wall heads). Only 96 / 140 repeat. — `template.html`, `pages/story.html`, `pages/shop.html`.
19. **`.field` default input size 18px is never seen.** Every use overrides it to 14.33 or 16. — `site.css`.
20. **Custom `.lead` frame background `#e9e1cf`** is the only warm hex on the site (one use). — `pages/custom.html`.

## Regenerating tokens.json

`tokens.json` is derived from `tokens.css`. After editing the CSS, rebuild it with the small script used to make it (a Python parse of the `--name:value; /* use: … */` lines into the design-tokens shape). Keep the `use` comments in `tokens.css`; they are the documentation.
