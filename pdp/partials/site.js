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

  // Nav items are white while they sit over photography (anything marked
  // data-under-nav) and black everywhere else. Bag (0) stays black.
  (function () {
    var head = document.querySelector('.head'), art = document.querySelector('[data-under-nav]');
    function tone() {
      var over = art && art.getBoundingClientRect().bottom >= head.offsetHeight * 0.6;
      head.classList.toggle('ink', !over);
    }
    addEventListener('scroll', tone, {passive: true}); addEventListener('resize', tone); tone();
  })();

  // Emerge: every image and text block starts hidden and settles into place the
  // first time about 16% of it is on screen. It never fades back out (toggling
  // flickered), and anything added later is picked up too.
  (function () {
    var BLOCKS = '.gallery figure, .info > *, .closing > *, .intro > *, .panel, .prose > *, ' +
                 '.steps figure, .childhood figure, .split .pics figure, .split .copy > *, .policies';
    // side-by-side groups cascade instead of arriving at once
    var GROUPS = ['.steps', '.childhood', '.info', '.intro', '.split .copy'];
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
    new MutationObserver(function (muts) {
      muts.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) arm(n); }); });
    }).observe(document.body, {childList: true, subtree: true});
  })();
</script>
