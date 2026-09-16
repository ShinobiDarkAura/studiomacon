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
        return bgLuma(el);
      }
      return 1;
    }

    var queued = false;
    function tone() {
      queued = false;
      parts.forEach(function (p) {
        var r = p.getBoundingClientRect(); if (!r.width) return;
        // sample a few points across the part and go by the darkest reading
        var y = r.top + r.height / 2, l = 1;
        [0.15, 0.5, 0.85].forEach(function (f) { l = Math.min(l, lumaAt(r.left + r.width * f, y)); });
        p.classList.toggle('on-dark', l < LIGHT);
      });
    }
    function soon() { if (!queued) { queued = true; requestAnimationFrame(tone); } }
    addEventListener('scroll', soon, {passive: true}); addEventListener('resize', soon);
    document.querySelectorAll('img').forEach(function (i) { if (!i.complete) i.addEventListener('load', soon); });
    tone();
  })();

  // Emerge: every image and text block starts hidden and settles into place the
  // first time about 16% of it is on screen. It never fades back out (toggling
  // flickered), and anything added later is picked up too.
  (function () {
    var BLOCKS = '.opening .hand, .gallery figure, .info > *, .acc-item, .closing > *, .intro > *, .panel, .prose > *, ' +
                 '.steps figure, .childhood figure, .split .pics figure, .split .copy > *, ' +
                 '.policies, .ways > *, .form > *, footer > *';
    // side-by-side groups cascade instead of arriving at once
    var GROUPS = ['.steps', '.childhood', '.info', '.intro', '.split .copy', '.acc', '.ways', '.form', 'footer'];
    var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var io = still ? null : new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('is-seen');
        io.unobserve(e.target);
      });
    }, {threshold: 0.16, rootMargin: '0px 0px -6% 0px'});

    function arm(root) {
      (root.matches && root.matches(BLOCKS) ? [root] : []).concat([].slice.call(root.querySelectorAll ? root.querySelectorAll(BLOCKS) : []))
        .forEach(function (el) {
          if (el.classList.contains('dr-emerge')) return;
          el.classList.add('dr-emerge');
          if (still) { el.classList.add('is-seen'); return; }
          io.observe(el);
        });
    }
    GROUPS.forEach(function (g) {
      document.querySelectorAll(g).forEach(function (group) {
        [].slice.call(group.children).forEach(function (el, i) { el.style.setProperty('--stagger', Math.min(i, 6) * 90 + 'ms'); });
      });
    });
    arm(document);
    // Blocks in the last few pixels of the page can't rise past the trigger
    // line, so reveal whatever is on screen once the bottom is reached.
    addEventListener('scroll', function () {
      if (still || innerHeight + scrollY < document.documentElement.scrollHeight - 2) return;
      document.querySelectorAll('.dr-emerge:not(.is-seen)').forEach(function (el) {
        if (el.getBoundingClientRect().top < innerHeight) { el.classList.add('is-seen'); io.unobserve(el); }
      });
    }, {passive: true});
    new MutationObserver(function (muts) {
      muts.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) arm(n); }); });
    }).observe(document.body, {childList: true, subtree: true});
  })();
</script>
