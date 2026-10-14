#!/usr/bin/env python3
"""A rail of thumbnails beside the product photo stack, desktop only (local preview; lives in _variant-story).

    python3 pdp/_variant-story/pdp/make_rail.py        (after build_pdp.py and make_collage.py)

Thumbnails on the photograph itself, the glass 32px in from the left edge, centred on the screen, square with 16px corners and drop shadows.
The thumbnails are 2.8vw wide, stacked at the left, centred in the screen; they travel with the page and stop where the stack ends.
Clicking one scrolls to that photograph; the one in view is marked.
"""
import glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ON = False          # parked for now: False takes the rail off every page, True puts it back

BLOCK = r"""
<!-- thumbnail rail (local preview) -->
<style>
  .rail{display:none}
  @media (min-width:1024px){
    .gallery{position:relative}
    .rail{display:flex;flex-direction:column;justify-content:flex-start;position:absolute;left:0;right:0;top:0;bottom:0;align-items:flex-start;z-index:2;pointer-events:none}          /* under the header and menu */
    .rail .in{position:sticky;top:50vh;transform:translateY(-50%);display:flex;flex-direction:column;gap:10.5px;margin-left:32px;padding:10.5px;pointer-events:auto;
      width:fit-content;border-radius:12px;background:rgba(255,255,255,.22);-webkit-backdrop-filter:blur(18px) saturate(1.5);backdrop-filter:blur(18px) saturate(1.5);
      box-shadow:0 2px 6px rgba(0,0,0,.06),0 14px 34px -12px rgba(0,0,0,.28)}          /* a light frosted glass behind the thumbnails */
    .rail button{display:block;width:2.82vw;aspect-ratio:1/1;padding:0;border:0;border-radius:8px;background:#E5E3DF;overflow:hidden;cursor:pointer;
      outline:none}
    .rail button:focus,.rail button:focus-visible{outline:none}
    .rail img{display:block;width:100%;height:100%;object-fit:cover;border-radius:8px}
  }
</style>
<script>
(function () {
  function go() {
    var g = document.querySelector('.gallery'); if (!g || g.querySelector('.rail')) return;
    var figs = [].filter.call(g.children, function (f) { return f.tagName === 'FIGURE'; });
    if (figs.length < 2) return;
    var rail = document.createElement('div'), inner = document.createElement('div'); rail.className = 'rail'; inner.className = 'in'; rail.appendChild(inner);
    figs.forEach(function (f, i) {
      var im = f.querySelector('img'), vid = f.querySelector('video');
      var src = im ? (im.getAttribute('data-th') || im.currentSrc || im.src) : (vid && vid.getAttribute('poster'));
      if (!src) return;
      var b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-label', 'Picture ' + (i + 1));
      var t = document.createElement('img'); t.src = src; t.alt = ''; b.appendChild(t);
      b.addEventListener('click', function () { f.scrollIntoView({behavior: 'smooth', block: 'start'}); });
      inner.appendChild(b); f._railBtn = b;
    });
    g.appendChild(rail);
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting && e.target._railBtn) { inner.querySelectorAll('.on').forEach(function (x) { x.classList.remove('on'); }); e.target._railBtn.classList.add('on'); } });
    }, {rootMargin: '-45% 0px -45% 0px'});
    figs.forEach(function (f) { io.observe(f); });
  }
  if (document.readyState !== 'loading') go(); else document.addEventListener('DOMContentLoaded', go);
})();
</script>
<!-- /thumbnail rail -->"""

n = 0
for p in sorted(glob.glob(os.path.join(HERE, "*.html"))):
    d = open(p).read()
    if 'class="gallery"' not in d or 'class="product' not in d:
        continue
    d = re.sub(r"\n<!-- thumbnail rail \(local preview\) -->.*?<!-- /thumbnail rail -->", "", d, flags=re.S)
    if ON:
        d = d.replace("</body>", BLOCK + "\n</body>", 1)
    open(p, "w").write(d); n += 1
print(n, "product pages", "given the rail" if ON else "with the rail taken off")
