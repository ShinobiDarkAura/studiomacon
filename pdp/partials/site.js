<script>
  // Accordions: the height eases through a grid-row transition, so nothing is
  // measured in script and a panel of any length opens at the same pace.
  document.querySelectorAll('.acc-head').forEach(function (b) {
    b.addEventListener('click', function () {
      var item = b.parentElement, open = !item.classList.contains('open');
      item.classList.toggle('open', open);
      b.setAttribute('aria-expanded', open);
    });
  });

  // Nav tone: each part of the nav (links, logotype, bag) looks at what is
  // actually beneath it. Over an image it reads the pixels there; over anything
  // else, the background colour. Only very light ground keeps the nav black.
  (function () {
    var LIGHT = 0.82;                      // "super light": white, pale grey, paper
    var parts = [].slice.call(document.querySelectorAll('.head .left, .head .logotype, .head .right'));
    var maps = new WeakMap();

    function lumaOf(r, g, b) { return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255; }

    function map(img) {                    // a small luminance copy of each image, made once
      if (maps.has(img)) return maps.get(img);
      if (!img.complete || !img.naturalWidth) return null;
      var w = 64, h = Math.max(1, Math.round(64 * img.naturalHeight / img.naturalWidth));
      var c = document.createElement('canvas'); c.width = w; c.height = h;
      var x = c.getContext('2d', {willReadFrequently: true});
      try { x.drawImage(img, 0, 0, w, h); var d = x.getImageData(0, 0, w, h).data; } catch (e) { return null; }
      var m = {w: w, h: h, d: d}; maps.set(img, m); return m;
    }

    function bgLuma(el) {                  // first painted background up the tree, else the white page
      for (; el && el !== document.documentElement; el = el.parentElement) {
        var c = getComputedStyle(el).backgroundColor.match(/[\d.]+/g);
        if (c && (c.length < 4 || +c[3] > 0.5)) return lumaOf(+c[0], +c[1], +c[2]);
      }
      return 1;
    }

    function lumaAt(px, py) {
      var stack = document.elementsFromPoint(px, py);
      for (var i = 0; i < stack.length; i++) {
        var el = stack[i];
        if (el.closest('.head')) continue;
        if (el.tagName === 'IMG') {
          var m = map(el); if (!m) return bgLuma(el);
          var r = el.getBoundingClientRect(), fit = getComputedStyle(el).objectFit;
          var sx = r.width / el.naturalWidth, sy = r.height / el.naturalHeight;
          if (fit === 'cover') sx = sy = Math.max(sx, sy);
          else if (fit === 'contain') sx = sy = Math.min(sx, sy);
          var ox = (r.width - el.naturalWidth * sx) / 2, oy = (r.height - el.naturalHeight * sy) / 2;
          var u = (px - r.left - ox) / (el.naturalWidth * sx), v = (py - r.top - oy) / (el.naturalHeight * sy);
          if (u < 0 || u > 1 || v < 0 || v > 1) return bgLuma(el);
          var tx = Math.min(m.w - 1, Math.floor(u * m.w)), ty = Math.min(m.h - 1, Math.floor(v * m.h));
          var sum = 0, n = 0, alpha = 0;
          for (var dy = -1; dy <= 1; dy++) for (var dx = -2; dx <= 2; dx++) {
            var X = Math.max(0, Math.min(m.w - 1, tx + dx)), Y = Math.max(0, Math.min(m.h - 1, ty + dy)), k = (Y * m.w + X) * 4;
            sum += lumaOf(m.d[k], m.d[k + 1], m.d[k + 2]) * m.d[k + 3] / 255; alpha += m.d[k + 3] / 255; n++;
          }
          // transparent pixels show whatever is behind the picture
          var under = bgLuma(el.parentElement);
          return (sum + under * (n - alpha)) / n;
        }
        // a gap between pictures in an image grid: hold the current colour until the grid is left
        if (el.closest('.wall, .examples, .gallery')) return null;
        return bgLuma(el);
      }
      return 1;
    }

    var queued = false, held = null, head = document.querySelector('.head');
    function tone() {
      queued = false;
      // the whole nav is one unit: read under each part, then colour every part the same
      var r0 = head.getBoundingClientRect(), mid = r0.top + r0.height / 2;
      var grid = null;
      document.elementsFromPoint(innerWidth / 2, mid).some(function (el) {
        if (el.closest('.head')) return false;
        grid = el.closest('.wall, .examples, .gallery'); return true;
      });
      if (grid && held === grid) return;          // over an image grid: keep the colour until the grid has passed
      held = grid;
      var dark = 0, counted = 0;
      parts.forEach(function (p) {
        var r = p.getBoundingClientRect(); if (!r.width) return;
        var y = r.top + r.height / 2, l = 1, seen = false;
        [0.15, 0.5, 0.85].forEach(function (f) {
          var v = lumaAt(r.left + r.width * f, y);
          if (v === null) return;
          seen = true; l = Math.min(l, v);
        });
        if (!seen) return;
        counted++; if (l < LIGHT) dark++;
      });
      if (!counted) return;
      var onDark = dark * 2 > counted;              // most of the nav sits over something dark
      parts.forEach(function (p) { p.classList.toggle('on-dark', onDark); });
    }
    function soon() { if (!queued) { queued = true; requestAnimationFrame(tone); } }
    addEventListener('scroll', soon, {passive: true}); addEventListener('resize', soon);
    document.querySelectorAll('img').forEach(function (i) { if (!i.complete) i.addEventListener('load', function () { held = null; soon(); }); });
    addEventListener('load', function () { held = null; soon(); });
    tone();
  })();

  // Emerge: every image and text block starts hidden and settles into place the
  // first time about 16% of it is on screen. It never fades back out (toggling
  // flickered), and anything added later is picked up too.
  (function () {
    var BLOCKS = '.opening .hand, .ship .branch, .gallery figure, .info > *, .acc-item, .closing > *, .intro > *, .panel, .prose > *, ' +
                 '.steps figure, .childhood figure, .split .pics figure, .split .copy > *, ' +
                 '.policies, .ways > *, .form > *, footer > *, .wall figure, .wall-head, .order > *';
    // side-by-side groups cascade instead of arriving at once
    var GROUPS = ['.order', '.steps', '.childhood', '.history .intro', '.info', '.intro', '.split .copy', '.acc', '.ways', '.form', 'footer'];
    var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var io = still ? null : new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('is-seen');
        io.unobserve(e.target);
      });
    }, {threshold: 0.16, rootMargin: '0px 0px -6% 0px'});
    // the footer sits against the page's bottom edge, where the main trigger line
    // can never be crossed, so it reveals as soon as any of it is on screen
    var edge = still ? null : new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('is-seen');
        edge.unobserve(e.target);
      });
    }, {threshold: 0, rootMargin: '0px 0px 120px 0px'});          // allow for the 66px drop of the hidden state

    function arm(root) {
      (root.matches && root.matches(BLOCKS) ? [root] : []).concat([].slice.call(root.querySelectorAll ? root.querySelectorAll(BLOCKS) : []))
        .forEach(function (el) {
          if (el.classList.contains('dr-emerge')) return;
          // hide instantly: the transition is for arriving, not for going away
          el.style.transition = 'none';
          el.classList.add('dr-emerge');
          // the inspiration wall is already in place wherever it fills the first
          // screen; only pieces further down slide in as you scroll
          void el.offsetWidth;
          el.style.transition = '';
          if (still) { el.classList.add('is-seen'); return; }
          // the inspiration wall's first screen plays in full on load, even the
          // pieces only partly in view, so no part of the screen is left empty
          if (el.closest('.wall, .wall-head') && el.getBoundingClientRect().top < innerHeight) {
            requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add('is-seen'); }); });
            return;
          }
          // let the hidden state paint first, or blocks already on screen at load
          // would jump straight to their resting place without animating
          // (and wait for the stylesheet: until the hidden state has actually taken
          // effect there is nothing to animate from)
          var tries = 0;
          (function ready() {
            if (getComputedStyle(el).opacity !== '0' && tries++ < 120) return requestAnimationFrame(ready);
            requestAnimationFrame(function () { (el.closest('footer') ? edge : io).observe(el); });
          })();
        });
    }
    // wall pieces cascade by their position in the row, so each row settles left to right
    // pieces already on screen at load arrive top to bottom, the rest by column
    document.querySelectorAll('.wall figure').forEach(function (f) {
      var r = f.getBoundingClientRect();
      var d = r.top < innerHeight ? Math.max(0, r.top) / innerHeight * 700 + r.left / innerWidth * 120
                                  : Math.round(r.left / innerWidth * 4) * 80;
      f.style.setProperty('--stagger', Math.round(d) + 'ms');
    });
    document.querySelectorAll('.wall-head').forEach(function (h) { h.style.setProperty('--stagger', '0ms'); });
    GROUPS.forEach(function (g) {
      document.querySelectorAll(g).forEach(function (group) {
        [].slice.call(group.children).forEach(function (el, i) { el.style.setProperty('--stagger', Math.min(i, 6) * 90 + 'ms'); });
      });
    });
    arm(document);
    // Blocks in the last few pixels of the page can't rise past the trigger
    // line, so reveal whatever is on screen once the bottom is reached.
    function atBottom() {
      if (still || innerHeight + scrollY < document.documentElement.scrollHeight - 2) return;
      document.querySelectorAll('.dr-emerge:not(.is-seen)').forEach(function (el) {
        if (el.getBoundingClientRect().top < innerHeight) { el.classList.add('is-seen'); io.unobserve(el); }
      });
    }
    addEventListener('scroll', atBottom, {passive: true});
    // a reload lands back at the old scroll position without necessarily scrolling,
    // so check once everything has loaded and been armed as well
    addEventListener('load', function () { setTimeout(atBottom, 80); setTimeout(atBottom, 400); });
    new MutationObserver(function (muts) {
      muts.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) arm(n); }); });
    }).observe(document.body, {childList: true, subtree: true});
  })();
</script>
