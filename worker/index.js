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

// The newsletter maker (newsletter.html): its shared drafts and uploaded photos, kept in KV (binding NEWSLETTER).
// Drafts need the studio's shared password (secret NEWSLETTER_KEY); photos are public, since emails load them.
async function newsletter(request, env, url) {
  const kv = env.NEWSLETTER;
  const json = (o, status = 200) => new Response(JSON.stringify(o), {status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
  let m = url.pathname.match(/^\/_nl\/img\/([a-z0-9-]{8,64})\.(jpg|gif)$/);
  if (m) {
    if (!kv || request.method !== 'GET') return new Response(null, {status: 404});
    const pic = await kv.get('img:' + m[1], 'arrayBuffer');
    if (!pic) return new Response(null, {status: 404});
    return new Response(pic, {headers: {'content-type': m[2] === 'gif' ? 'image/gif' : 'image/jpeg', 'cache-control': 'public, max-age=31536000, immutable'}});
  }
  if (!kv || !env.NEWSLETTER_KEY) return json({error: 'not set up'}, 503);
  if (request.headers.get('x-macon-key') !== env.NEWSLETTER_KEY) return json({error: 'wrong password'}, 401);
  if (url.pathname === '/_nl/check') return json({ok: true});
  if (url.pathname === '/_nl/img' && request.method === 'POST') {
    const pic = await request.arrayBuffer();
    if (!pic.byteLength || pic.byteLength > 5e6) return json({error: 'photo too large'}, 413);
    const id = crypto.randomUUID(), ext = /gif/.test(request.headers.get('content-type') || '') ? 'gif' : 'jpg';          // moving GIFs are kept as they are
    const kind = /^(orig|crop)$/.test(request.headers.get('x-kind') || '') ? request.headers.get('x-kind') : 'orig';
    await kv.put('img:' + id, pic, {metadata: {at: Date.now(), kind, ext}});          // the library shows the originals, newest first
    return json({url: `https://studiomacon.co/_nl/img/${id}.${ext}`});
  }
  if (url.pathname === '/_nl/drafts' && request.method === 'GET') {
    const keys = [];
    let cursor;
    do { const page = await kv.list({prefix: 'draft:', cursor}); keys.push(...page.keys); cursor = page.list_complete ? null : page.cursor; } while (cursor);
    return json(keys.map(k => Object.assign({id: k.name.slice(6)}, k.metadata || {})));
  }
  m = url.pathname.match(/^\/_nl\/drafts\/([a-z0-9-]{8,64})$/);
  if (m) {
    const key = 'draft:' + m[1];
    if (request.method === 'GET') {
      const v = await kv.get(key);
      return v ? new Response(v, {headers: {'content-type': 'application/json', 'cache-control': 'no-store'}}) : json({error: 'not found'}, 404);
    }
    if (request.method === 'PUT') {
      const text = await request.text();
      if (text.length > 1e6) return json({error: 'too large'}, 413);
      let d; try { d = JSON.parse(text); } catch (e) { return json({error: 'not a draft'}, 400); }
      // two people on one draft: a save made from an older copy is refused, and the newer one sent back
      const cur = await kv.getWithMetadata(key);
      const baseUpdated = Number(request.headers.get('x-base-updated') || 0);
      if (cur.value && cur.metadata && cur.metadata.updated > baseUpdated) return new Response(cur.value, {status: 409, headers: {'content-type': 'application/json'}});
      // an earlier version is kept: every 15 minutes of editing, and whenever someone else saves over it
      const by = String(d.by || '').slice(0, 40);
      if (cur.value && cur.metadata && (request.headers.get('x-keep-version') === '1' || (cur.metadata.by || '') !== by)) {
        await kv.put('ver:' + m[1] + ':' + cur.metadata.updated, cur.value,
          {metadata: {by: cur.metadata.by || '', updated: cur.metadata.updated}, expirationTtl: 60 * 60 * 24 * 120});
        const vs = (await kv.list({prefix: 'ver:' + m[1] + ':'})).keys.sort((a, b) => (b.metadata?.updated || 0) - (a.metadata?.updated || 0));
        for (const k of vs.slice(40)) await kv.delete(k.name);          // the newest forty
      }
      const updated = Date.now();
      d.updated = updated;
      await kv.put(key, JSON.stringify(d), {metadata: {title: String(d.title || '').slice(0, 120), by: String(d.by || '').slice(0, 40), updated}});
      return json({ok: true, updated});
    }
    if (request.method === 'DELETE') { await kv.delete(key); return json({ok: true}); }
  }
  // the photo library: every original uploaded, newest first (crops of them are left out)
  if (url.pathname === '/_nl/library' && request.method === 'GET') {
    const keys = []; let cursor;
    do { const page = await kv.list({prefix: 'img:', cursor}); keys.push(...page.keys); cursor = page.list_complete ? null : page.cursor; } while (cursor && keys.length < 3000);
    return json(keys.filter(k => !k.metadata || k.metadata.kind !== 'crop')
      .map(k => ({url: `https://studiomacon.co/_nl/img/${k.name.slice(4)}.${(k.metadata && k.metadata.ext) || 'jpg'}`, at: (k.metadata && k.metadata.at) || 0}))
      .sort((a, b) => b.at - a.at));
  }
  // earlier versions of a draft
  m = url.pathname.match(/^\/_nl\/versions\/([a-z0-9-]{8,64})(?:\/(\d{10,16}))?$/);
  if (m && request.method === 'GET') {
    if (m[2]) { const v = await kv.get('ver:' + m[1] + ':' + m[2]); return v ? new Response(v, {headers: {'content-type': 'application/json', 'cache-control': 'no-store'}}) : json({error: 'not found'}, 404); }
    const ks = (await kv.list({prefix: 'ver:' + m[1] + ':'})).keys;
    return json(ks.map(k => k.metadata || {updated: Number(k.name.split(':').pop())}));
  }
  // saved sections, shared by everyone with the password
  if (url.pathname === '/_nl/sections' && request.method === 'GET') {
    const ks = (await kv.list({prefix: 'section:'})).keys;
    return json(ks.map(k => Object.assign({id: k.name.slice(8)}, k.metadata || {})));
  }
  m = url.pathname.match(/^\/_nl\/sections\/([a-z0-9-]{8,64})$/);
  if (m) {
    const key = 'section:' + m[1];
    if (request.method === 'GET') { const v = await kv.get(key); return v ? new Response(v, {headers: {'content-type': 'application/json', 'cache-control': 'no-store'}}) : json({error: 'not found'}, 404); }
    if (request.method === 'PUT') {
      const text = await request.text(); if (text.length > 2e5) return json({error: 'too large'}, 413);
      let s; try { s = JSON.parse(text); } catch (e) { return json({error: 'not a section'}, 400); }
      await kv.put(key, text, {metadata: {name: String(s.name || '').slice(0, 80), n: (s.blocks || []).length, by: String(s.by || '').slice(0, 40)}});
      return json({ok: true});
    }
    if (request.method === 'DELETE') { await kv.delete(key); return json({ok: true}); }
  }
  return json({error: 'not found'}, 404);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/_e') return relay(request, env, ctx);
    if (url.pathname.startsWith('/_nl/')) return newsletter(request, env, url);
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
