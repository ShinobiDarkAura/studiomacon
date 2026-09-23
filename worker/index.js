// The site is static files. This only steps in for video: phones (iPhones above all) stream
// a video by asking for it in byte ranges, and will not play one from a server that answers
// every range with the whole file. Cloudflare's static serving does exactly that, so here
// each range request is answered with just the bytes asked for (206 Partial Content).
// On the real domain it also sends www.studiomacon.co to studiomacon.co (one permanent hop, path and
// query kept), so old links and anything bookmarked from the Wix days still land.
// Meta's Conversions API: the same three events the browser sends, sent again from here.
// A browser event is lost to blockers, ITP and every locked-down phone; a server one is not.
// Both carry the same event_id, so Meta counts the pair once. Purchase and InitiateCheckout
// are deliberately absent: Shopify's own app already sends those, and sending ours would
// recreate the double count that fbq InitiateCheckout was removed to fix.
const CAPI_EVENTS = new Set(['PageView', 'ViewContent', 'AddToCart', 'Contact']);

function cookie(header, name) {
  const m = (header || '').match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}

async function relay(request, env, ctx) {
  if (request.method !== 'POST') return new Response(null, {status: 405});
  // the endpoint is public, so only our own pages may speak to it, and only in these words
  const origin = request.headers.get('origin') || '';
  if (!/^https:\/\/(www\.)?studiomacon\.co$/.test(origin) && !origin.endsWith('.workers.dev')) {
    return new Response(null, {status: 204});
  }
  if (!env.META_CAPI_TOKEN) return new Response(null, {status: 204});          // nothing to send with yet

  let body;
  try { body = await request.json(); } catch (e) { return new Response(null, {status: 204}); }
  if (!body || !CAPI_EVENTS.has(body.ev) || typeof body.id !== 'string') return new Response(null, {status: 204});

  const ck = request.headers.get('cookie');
  const user = {
    client_ip_address: request.headers.get('cf-connecting-ip') || undefined,
    client_user_agent: request.headers.get('user-agent') || undefined,
    fbp: cookie(ck, '_fbp') || undefined,
    fbc: cookie(ck, '_fbc') || undefined,
  };
  // already SHA-256 in the browser; anything else is dropped rather than guessed at
  if (typeof body.em === 'string' && /^[0-9a-f]{64}$/.test(body.em)) user.em = body.em;

  const payload = {
    data: [{
      event_name: body.ev,
      event_time: Math.floor(Date.now() / 1000),
      event_id: body.id,
      event_source_url: typeof body.url === 'string' ? body.url.slice(0, 500) : undefined,
      action_source: 'website',
      user_data: user,
      custom_data: (body.custom && typeof body.custom === 'object') ? body.custom : {},
    }],
    access_token: env.META_CAPI_TOKEN,
  };
  if (env.META_TEST_CODE) payload.test_event_code = env.META_TEST_CODE;

  // the visitor never waits on Meta, and never sees it fail
  ctx.waitUntil(
    fetch(`https://graph.facebook.com/v21.0/${env.META_PIXEL_ID || '501136812574699'}/events`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(2500),
    }).catch(() => {})
  );
  return new Response(null, {status: 204});
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/_e') return relay(request, env, ctx);
    // Which country the visitor is in, so the pages can show the international note to them only.
    if (url.pathname === '/_geo') {
      return new Response(JSON.stringify({country: request.cf && request.cf.country || ''}),
                          {headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
    }
    // One permanent hop for anything that needs tidying: www to the bare domain, and old links shared as
    // /Product-Page/Pip/ or /story/ (Wix ignored case and a closing slash). Real files keep their case.
    const to = new URL(url);
    if (to.hostname.startsWith('www.')) to.hostname = to.hostname.slice(4);
    if (to.pathname.length > 1) to.pathname = to.pathname.replace(/\/+$/, '');
    if (!/\.[a-z0-9]+$/i.test(to.pathname)) to.pathname = to.pathname.toLowerCase();
    if (to.href !== url.href) return Response.redirect(to.toString(), 301);
    let res = await env.ASSETS.fetch(request);
    // the preview address stays up after launch; keep it out of search results so only studiomacon.co is found
    if (url.hostname.endsWith('.workers.dev')) {
      res = new Response(res.body, res);
      res.headers.set('X-Robots-Tag', 'noindex');
    }
    const range = request.headers.get('range');
    if (!range || res.status !== 200) return res;

    const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
    if (!m || (m[1] === '' && m[2] === '')) return res;

    const body = await res.arrayBuffer();
    const size = body.byteLength;
    let start, end;
    if (m[1] === '') {                        // "bytes=-500": the last 500 bytes
      start = Math.max(0, size - Number(m[2]));
      end = size - 1;
    } else {
      start = Number(m[1]);
      end = m[2] === '' ? size - 1 : Math.min(Number(m[2]), size - 1);
    }
    if (start >= size || start > end) {
      return new Response(null, { status: 416, headers: { 'content-range': `bytes */${size}` } });
    }

    const headers = new Headers(res.headers);
    headers.set('content-range', `bytes ${start}-${end}/${size}`);
    headers.set('content-length', String(end - start + 1));
    headers.set('accept-ranges', 'bytes');
    return new Response(body.slice(start, end + 1), { status: 206, headers });
  },
};
