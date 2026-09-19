# Switch day: studiomacon.co from Wix to the new site

Prepared 2026-09-19. Everything below was checked against the live records that night.

## Where things stand
- **DNS is already on Cloudflare** (account alex@studiomacon.co, zone studiomacon.co). GoDaddy only holds the registration (renews 2026-11-20).
- Today `studiomacon.co` and `www` are Cloudflare records pointing at Wix. Only those two records change on switch day.
- **Email is not touched.** The five Google MX records, SPF, DMARC and the Google/Klaviyo verification TXT records stay exactly as they are. hello@, alex@ and hannah@ keep working the whole time.
- The new site is built and tested. `wrangler.live.jsonc` attaches it to both addresses, and www forwards to studiomacon.co (tested: path and query kept).
- The preview (studiomacon.studiomacon.workers.dev) stays up after the switch. Anything still pointing at it, such as email images, keeps working.
- The contact form and footer sign-up already accept studiomacon.co and www (tested). They don't work on the preview; that's expected.
- Tracking (Meta pixel, GA4, Google Ads, Klaviyo onsite) switches on by itself the moment the site loads on studiomacon.co.

## Decide before switching
- **Prices:** seven totems cost different amounts on Wix than on the new site and Shopify. Ren is $240 on Wix and $220 new; Rebi, Eleph and Zuma are $200 → $220; Milo, Ibi and Yaël are $180 → $220. The custom page says "silver from $1,200" on Wix and "$1,600+" new. Confirm these are intended; the ad catalogs will switch to the new prices.
- **Privacy / terms links:** the site links to no privacy policy. Meta, Google Merchant and the newsletter sign-up expect one. Shopify already hosts them at `w3nidi-ny.myshopify.com/policies/privacy-policy`, `/terms-of-service` and `/refund-policy`; add small footer links to them.
- **Tracking IDs:** before cancelling Wix, open Wix → Marketing Integrations and confirm the Meta Pixel, GA4 and Google Ads IDs match the ones in `pdp/build_pdp.py` (TRACKING).

## Do now (any time, safe, fixes something already broken)
Cloudflare → studiomacon.co → DNS → Records. These CNAMEs are **proxied (orange cloud)**, which breaks email signing: Klaviyo's DKIM (`kl`, `kl2`) currently fails, so Klaviyo mail is more likely to reach spam. Click each one, set **Proxy status → DNS only (grey)**, and save:
- `kl._domainkey`, `kl2._domainkey`, `hello` (Klaviyo/SendGrid)
- `newsletter` (Klaviyo pages)
- `googledc01f90bfceb785d` (Google verification)
- `s1._domainkey`, `s2._domainkey`, `sel1._domainkey`, `sg` (old Wix mail, harmless either way)

Then: DNS → Records → **Import and Export → Export**, and keep the file as a backup.

## Switch (about 15 minutes, with Alex and Claude)
1. Pick a quiet hour. Tell Hannah.
2. In Cloudflare DNS, **delete only these**:
   - `A studiomacon.co` (Wix, all of them)
   - `CNAME www → cdn3.wixdns.net`
   Leave every MX, TXT and other CNAME alone. The site is offline for a minute or two from here.
3. Claude runs `npx wrangler deploy -c wrangler.live.jsonc` from the repo root. Cloudflare creates the new records and certificates for both addresses.
4. Check (Claude):
   - `https://studiomacon.co` → 200, the new home page
   - `https://www.studiomacon.co/pip.html` → 301 to `https://studiomacon.co/pip.html`
   - old Wix paths: `/product-page/pip` → `/pip.html`, `/shop`, `/cart-page`, `/shipping-and-returns` all redirect
   - `/video/film-process.mp4` with a byte range → 206 (iPhone video)
   - send an email to hello@ from a personal address and confirm it arrives
   - on a phone: home, a product, add to bag, Checkout reaches Shopify

## Right after (30–45 minutes)
5. **Shopify → Products → Import** `pdp/shopify/product-images.csv`, with **Overwrite existing products** ticked. This gives checkout, receipts and emails real photos. It only works once the site is live, because Shopify fetches each image from studiomacon.co.
6. **Meta Commerce Manager** → catalog → data sources: add a scheduled feed `https://studiomacon.co/meta-catalog.csv`, daily. Retire the Wix catalog source.
7. **Google Merchant Center** → feeds: `https://studiomacon.co/google-products.xml`, daily.
8. **Meta Events Manager** → Maçon's FGP Pixel → Test events: open studiomacon.co and confirm PageView and ViewContent.
9. **Google Search Console**: submit `https://studiomacon.co/sitemap.xml`. Verification is by DNS and is kept.
10. **Emails**: run `MACON_LIVE=1 python3 pdp/email/build_emails.py` and re-paste the templates in Shopify when convenient. This isn't urgent, because the preview host keeps serving the images.

## Later
- **Shopify Messaging sending:** once "test emails are temporarily unavailable" clears, turn off Klaviyo's welcome and abandoned-checkout flows, export the Klaviyo list, and import it into Shopify Customers.
- **Shopify sender domain:** Settings → Notifications → Sender email → authenticate studiomacon.co. Add the CNAMEs Shopify gives you in Cloudflare as **DNS only**.
- **Footer sign-up into Shopify:** create the custom app (`write_customers`), then add Supabase secrets `SHOPIFY_SHOP=w3nidi-ny.myshopify.com` and `SHOPIFY_ADMIN_TOKEN`.
- **Wix:** keep the plan for a week of clean orders, then cancel. The domain connection in Wix no longer matters, since DNS lives in Cloudflare.

## Roll back (if anything is badly wrong)
1. Cloudflare → Workers & Pages → studiomacon → Settings → Domains & Routes: remove `studiomacon.co` and `www.studiomacon.co`.
2. DNS → add back:
   - `A studiomacon.co 185.230.63.107`
   - `A studiomacon.co 185.230.63.186`
   - `A studiomacon.co 185.230.63.171`
   - `CNAME www cdn3.wixdns.net`
   All proxied, as they are today. Wix serves the old site again within minutes.
