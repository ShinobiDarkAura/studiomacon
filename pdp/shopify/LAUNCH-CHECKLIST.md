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
- Contact + commission forms DONE end to end: enquiry function deployed, Resend verified, both paths
  tested. Studio copy reaches hello@/alex@/hannah@ with Reply-To set to the sender; auto-reply goes out.
  Checked in Gmail: SPF, DKIM and DMARC all pass, inbox not spam.
- DNS moved to Cloudflare (2026-09-17): zone rebuilt from live records in pdp/dns/studiomacon.co.zone,
  nameservers at GoDaddy now kobe/rachel.ns.cloudflare.com. Fixed on the way: all five Google MX records
  (only alt3 existed) and an SPF record (none existed).

## Needs Alex / Hannah (logins, IDs, bank)
1. Payments: DONE — Shopify Payments live, out of test mode.
2. Plan: DONE — Basic; storefront password removed, checkout verified working end to end.
3. California sales tax: DONE — permit 247-073440 (MACON STUDIO LLC).
   Open item: CDTFA had 11 unread notices, and the old ADACUS account 102-658559 may need formally closing.
4. Shipping: DONE by Claude — Domestic: live USPS (Ground Advantage, Priority, Priority Express); Rest of World (every country in Markets: Asia, Europe, Canada, Oceania): live USPS International. To ship to more countries, add them in Settings → Markets first. Still set your real box: Settings → Shipping and delivery → Packages.
5. Weigh pieces (grams) — current weights are estimates (totems 60 g, rings 12 g, pendants 20 g, cuff 10 g).
6. Klaviyo: installed. Still needed from Alex: Klaviyo public key + list id for the footer signup.
7. Policies: DONE — pasted.
8. Sietch Ring: DONE — typed Ring.

## Next for Claude (after the above)
- Klaviyo footer signup (needs the Klaviyo public key + list id)
- Branch `website-forms` at git/macon-archive-web-forms still needs merging to main (deployed from the branch).
- Test data to clear before launch: 4 test enquiries in the `inquiries` table (Wiring/Second/Third/Fourth Test).
- Newsletter footer: Shopify signup (per Alex) — to wire once the store password is removed
- Hosting (Cloudflare Pages), domain records at switch day, Search Console + Google & YouTube app
- Product photographs in Shopify: the 17 products have none, so the checkout, receipts and
  Klaviyo emails show a grey placeholder. shopify/product-images.csv maps all 68 pictures to
  their studiomacon.co addresses; import it (Products -> Import, "Overwrite existing products")
  the moment the site is live. Shopify fetches each URL itself, so it only works once the
  domain serves the site. No admin token needed.
