# Studio Maçon — build plan

Rebuild of studiomacon.co off Wix. Static site + Supabase-backed editor ("Maçon Studio").

## Decisions made

| Decision | Choice | Why |
|---|---|---|
| Hosting | Static HTML on GitHub Pages | Free, fastest, best SEO, zero runtime deps |
| Content architecture | **Static + Publish button**, with a **live sold-out flag** exception | Republish (~1 min) is fine for content; drops need instant stock |
| Overselling protection | **Stripe inventory limits** (qty=1 for one-of-a-kind) | Server-side + atomic; a live badge alone can be raced |
| Supabase project | Reuse macon-archive's (`berdrzxjoejirbhdgjer`) | One login covers CRM + store editor |
| Auth | Magic link, locked to alex@ / hannah@studiomacon.co | No passwords; same pattern as macon-archive |
| Collections | **Two stacked sections, ephemeral first** — NOT a toggle | Toggles hide inventory; stacking keeps both visible and frames the price difference |
| Editable by Hannah | Product fields, page content, homepage hero/tagline | (Not full drag-drop layout — that's Wix's bloat) |

## Collections model

- **Ephemeral** — one-of-a-kind, higher price, sells out permanently. Top of page, 2-up larger cards,
  crest as the marker, "ONE OF ONE" overline in Swim Club Wide. Sold pieces are **archived visibly**
  (desaturated + crest stamp), not deleted — builds mythology and proves scarcity.
- **Perennial** — made-to-order collection, always available. Below, calm 3-up grid (current design).
- Dedicated pages `/ephemeral` and `/perennial` for drop marketing ("link in bio") and SEO.

## Schema (Supabase)

- `products` — slug, name, price, description, notes, collection(perennial|ephemeral),
  status(draft|scheduled|live|sold_out|archived), release_at, quantity, sort_order
- `product_images` — product_id, path, alt, sort_order
- `pages` — key(story|custom|shipping|contact), title, body, images
- `settings` — hero image, tagline
- Storage bucket for uploads. RLS: public read of live items; keepers-only write.

## Build phases

1. Supabase schema + migrate current 18 products & pages in
2. `build.py` reads Supabase instead of `_source/*.json`
3. GitHub Actions publish pipeline (+ scheduled publish for drops)
4. Admin `/admin`: auth + product editor + image manager  ← the big one
5. Admin: page + homepage editors
6. Stripe: products/prices synced on publish; inventory limits; webhook → macon-archive CRM

## Open items

- **Font licensing** — Index, Louize, Swim Club Wide are commercial fonts licensed for Wix.
  Self-hosting on GitHub Pages is a separate use. CONFIRM LICENSE OR BUY WEBFONT LICENSE before public launch.
- Contact form backend (currently opens mail client) — Formspree or Supabase function
- `hello@studiomacon.co` mailbox: confirm it isn't hosted *through* Wix before cancelling
- Sales tax / shipping rules (Wix computes these today)
- DNS: repoint studiomacon.co at GoDaddy when ready; keep Wix live until verified
