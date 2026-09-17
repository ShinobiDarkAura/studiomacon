# Shopify hookup — status and what's left

## Done (by Claude)
- Store name Studio Maçon; store + sender email hello@; order alerts to alex@ and hannah@
- Checkout newsletter checkbox on, unticked everywhere
- Headless channel installed; public Storefront token in shopify/config.json
- 18 products imported (17 pieces + hidden Totem Commission); Caldera Arc Single/Pair
- Site hookup: sizes/styles/prices from Shopify (tools/shopify_sync.py → shopify/variants.json → build);
  bag stores Shopify variant ids; Checkout and Apple Pay create a Shopify cart and hand off to Shopify checkout
  (tested: redirects correctly; store currently shows its password page until launch)
- SEO: meta description, canonical, share tags on every page; Product structured data on product pages;
  sitemap.xml, robots.txt; noindex on bag/checkout/hidden pages
- Old Wix addresses → new pages: _redirects
- Policy drafts: shopify/policies/*.md

## Needs Alex / Hannah (logins, IDs, bank)
1. Payments: Settings → Payments → Shopify Payments (Private multi-member LLC, Macon Studio LLC, EIN, bank). Turn on Apple Pay + Shop Pay.
2. Plan: Settings → Plan → Basic (removes the store password so checkout opens).
3. California sales tax: Settings → Taxes and duties → United States → California "Set up tax collection" (needs seller's permit number).
4. Shipping: DONE by Claude — Domestic: live USPS (Ground Advantage, Priority, Priority Express); Rest of World (every country in Markets: Asia, Europe, Canada, Oceania): live USPS International. To ship to more countries, add them in Settings → Markets first. Still set your real box: Settings → Shipping and delivery → Packages.
5. Weigh pieces (grams) — current weights are estimates (totems 60 g, rings 12 g, pendants 20 g, cuff 10 g).
6. Klaviyo: Integrations → Shopify → connect w3nidi-ny.myshopify.com (keep Wix connected until switch day).
7. Policies: paste the drafts from shopify/policies into Settings → Policies (edit first).
8. Sietch Ring: Products → Sietch Ring → Type: change "Ear Cuff" to "Ring".

## Next for Claude (after the above)
- Klaviyo footer signup (needs the Klaviyo public key + list id)
- Contact + commission forms: site side DONE (posts to the Bureau). Bureau side coded on branch `website-forms` in a worktree at git/macon-archive-web-forms — NOT deployed. To go live: merge, set secrets RESEND_API_KEY, ENQUIRY_FROM="Studio Maçon <hello@studiomacon.co>", ENQUIRY_NOTIFY="hello@studiomacon.co,alex@studiomacon.co,hannah@studiomacon.co", ENQUIRY_ORIGINS="https://studiomacon.co,https://www.studiomacon.co", then `supabase functions deploy enquiry`. Verify studiomacon.co as a sending domain in Resend.
- Newsletter footer: Shopify signup (per Alex) — to wire once the store password is removed
- Hosting (Cloudflare Pages), domain records at switch day, Search Console + Google & YouTube app
