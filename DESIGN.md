# Studio Maçon — design system (extracted from live studiomacon.co)

Read off the live DOM's computed styles, not guessed. This is the STORE's language,
which is close to but distinct from the `macon-archive` CRM palette.

## Palette
| Token | Value | Use |
|---|---|---|
| `--cream` | `#FFFBF0` | page background (warmer/lighter than archive's paper) |
| `--ink` | `#282523` | primary text |
| `--terra` | `#B56B2F` | primary accent — active nav, tagline, prices |
| `--terra-deep` | `#9F551B` | deeper burnt orange |
| `--terra-alt` | `#BA573A` | terracotta illustration tone |
| `--olive` | `#43493E` | inactive nav, secondary text |
| `--tan` | `#CFA886` | muted tan / rules |

## Type (the studio's own uploaded fonts — self-hosted in assets/fonts/)
- **Index** (`index.woff2`) — workhorse: body, product names, hero tagline. The mono-ish face.
- **Louize** (`louize.woff2`) — serif display: nav (Shop/Story/Custom), headings.
- **DM Mono** (`dmmono.woff2`) — minor: the "Menu" label only.

NOTE (licensing): Index and Louize are commercial fonts the studio licensed for Wix.
Self-hosting the woff2 on GitHub Pages is a *separate* use — confirm the license permits
self-hosting, or buy a webfont license, before going public. (Flagged to Alex/Hannah.)

## Signature assets (images, not fonts — reused from the real site)
- `assets/hero.jpg` — botanical + MAÇON wordmark hero composition
- `assets/goat-logo.png` — center-nav ram/goat mark
- (todo) urn icon (top-left), "Maçon Bureau of Provenance" olive crest (bottom-left)

## Homepage structure
1. Top bar: urn icon · goat logo (center) · Menu/hamburger
2. Hero image + terracotta Index tagline with em-dash marks
3. Maçon Bureau crest overlapping bottom-left
4. Shop grid: product image · name (Index) · price (Index)
5. Footer: email hello@studiomacon.co · Story · Custom · Shipping & Returns
