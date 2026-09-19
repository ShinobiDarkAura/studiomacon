// The site is static files. This only steps in for video: phones (iPhones above all) stream
// a video by asking for it in byte ranges, and will not play one from a server that answers
// every range with the whole file. Cloudflare's static serving does exactly that, so here
// each range request is answered with just the bytes asked for (206 Partial Content).
// On the real domain it also sends www.studiomacon.co to studiomacon.co (one permanent hop, path and
// query kept), so old links and anything bookmarked from the Wix days still land.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname.startsWith('www.')) {
      url.hostname = url.hostname.slice(4);
      return Response.redirect(url.toString(), 301);
    }
    const res = await env.ASSETS.fetch(request);
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
