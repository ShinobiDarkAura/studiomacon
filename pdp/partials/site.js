<script>
  (function (m) { if (m) document.documentElement.classList.add('logo-' + m[1]); })(location.search.match(/[?&]logo=(artifacts|objects)\b/));
  // A refresh always starts at the top of the page; Back and Forward still return to where you were
  (function () {
    var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    if (nav && nav.type === 'reload') {
      history.scrollRestoration = 'manual';
      scrollTo(0, 0);
      addEventListener('load', function () { scrollTo(0, 0); });
    }
    addEventListener('beforeunload', function () { history.scrollRestoration = 'auto'; });
  })();

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

    var lumas = new WeakMap();
    function bgLuma(el) {                  // first painted background up the tree, else the white page
      if (el && lumas.has(el)) return lumas.get(el);
      var v = paintedLuma(el); if (el) lumas.set(el, v); return v;
    }
    function paintedLuma(el) {
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
        if (el.tagName === 'VIDEO') return 0;
        if (/^(IMG|VIDEO)$/.test(el.tagName) && el.closest('.product .gallery')) return 0;          // product photos: the nav is always white over them
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
        if (el.closest('.wall, .examples')) return null;
        return bgLuma(el);
      }
      return 1;
    }

    var queued = false, held = null, head = document.querySelector('.head'), lastY = -99;
    function tone(force) {
      queued = false;
      if (force !== true && Math.abs(scrollY - lastY) < 8) return;          // nothing under the nav has moved enough to matter
      lastY = scrollY;
      // the whole nav is one unit: read under each part, then colour every part the same
      var r0 = head.getBoundingClientRect(), mid = r0.top + r0.height / 2;
      var grid = null;
      document.elementsFromPoint(innerWidth / 2, mid).some(function (el) {
        if (el.closest('.head')) return false;
        grid = el.closest('.wall, .examples'); return true;
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
    addEventListener('scroll', soon, {passive: true}); addEventListener('resize', function () { lastY = -99; soon(); });
    function fresh() { held = null; lastY = -99; soon(); }
    document.querySelectorAll('img').forEach(function (i) { if (!i.complete) i.addEventListener('load', fresh); });
    addEventListener('load', fresh);
    tone(true);
  })();

  // Emerge: every image and text block starts hidden and settles into place the
  // first time about 16% of it is on screen. It never fades back out (toggling
  // flickered), and anything added later is picked up too.
  (function () {
    var BLOCKS = '.opening .hand, .ship .branch, .gallery figure, .info > *, .acc-item, .closing > *, .intro > *, .panel, .prose > *, ' +
                 '.steps figure, .childhood figure, .split .pics figure, .split .copy > *, ' +
                 '.policies, .ways > *, .form > *, footer > *, .wall figure, .wall-head, .order > *, .related > :not(.rel-grid), .rel-piece';
    // side-by-side groups cascade instead of arriving at once
    var GROUPS = ['.related', '.rel-grid', '.order', '.steps', '.childhood', '.history .intro', '.info', '.intro', '.split .copy', '.acc', '.ways', '.form', 'footer'];
    // coming back (Back button or history) the page simply reappears as it was, with no entrance
    var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    var still = matchMedia('(prefers-reduced-motion: reduce)').matches || !!(nav && nav.type === 'back_forward');
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
      (root.matches && root.matches(BLOCKS) ? [root] : []).concat([].slice.call(root.querySelectorAll(BLOCKS)))
        .forEach(function (el) {
          if (el.classList.contains('dr-emerge') || el.hasAttribute('data-no-emerge')) return;
          // hide instantly: the transition is for arriving, not for going away
          el.style.transition = 'none';
          el.classList.add('dr-emerge');
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
    // Anything on the first screen at load plays its entrance even if it sits in the bottom
    // strip the scroll trigger ignores (it would otherwise wait for a scroll that never comes).
    if (!still) setTimeout(function () {
      document.querySelectorAll('.dr-emerge:not(.is-seen)').forEach(function (el) {
        if (el.getBoundingClientRect().top - 70 < innerHeight) { el.classList.add('is-seen'); io.unobserve(el); }
      });
    }, 400);
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

  // Checkout: the bag becomes a Shopify cart, then Shopify's own checkout takes over (cards, Apple Pay, Shop Pay, tax, shipping)
  window.MaconCheckout = function (items, button) {
    var cfg = window.MACON_SHOP || {};
    var lines = items.filter(function (i) { return i.variant; }).map(function (i) { return {merchandiseId: i.variant, quantity: i.qty || 1}; });
    if (!lines.length) return Promise.reject(new Error('Nothing to check out'));
    if (button) { button.setAttribute('aria-busy', 'true'); button.dataset.label = button.textContent; button.textContent = 'One moment…'; }
    return fetch('https://' + cfg.shop + '/api/' + cfg.api + '/graphql.json', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-Shopify-Storefront-Access-Token': cfg.token},
      body: JSON.stringify({query: 'mutation($lines:[CartLineInput!]){cartCreate(input:{lines:$lines}){cart{checkoutUrl} userErrors{message}}}', variables: {lines: lines}})
    }).then(function (r) { return r.json(); }).then(function (d) {
      var res = d && d.data && d.data.cartCreate;
      if (!res || !res.cart) throw new Error((res && res.userErrors[0] && res.userErrors[0].message) || 'Checkout is unavailable right now');
      // the bag is left alone here: a shopper who backs out of Shopify's checkout
      // must find their pieces still waiting. It is emptied on the thank-you page.
      location.href = res.cart.checkoutUrl;
    }).catch(function (e) {
      if (button) { button.removeAttribute('aria-busy'); button.textContent = button.dataset.label; }
      alert('Sorry, checkout could not start: ' + e.message + '. Please try again, or write to hello@studiomacon.co.');
      throw e;
    });
  };

  // Enquiries (contact + commission forms) go to the Bureau of Provenance, which emails the studio and replies to the sender
  window.MaconEnquiry = function (payload) {
    var url = (window.MACON_SHOP || {}).enquiry;
    if (!url) return Promise.reject(new Error('no enquiry address'));
    return fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)})
      .then(function (r) { if (!r.ok) throw new Error('enquiry failed (' + r.status + ')'); return r.json(); });
  };

  // Newsletter (footer): subscribes straight to the Klaviyo list the studio sends from
  document.querySelectorAll('form[data-newsletter]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var cfg = window.MACON_SHOP || {}, input = f.querySelector('input[type=email]'), email = input.value, btn = f.querySelector('button');
      if (!cfg.klaviyo || !cfg.klaviyoList) return;
      btn.textContent = '…';
      var body = new URLSearchParams();                                     // Klaviyo's own subscribe endpoint, the one its embedded forms use
      body.append('g', cfg.klaviyoList); body.append('email', email); body.append('$fields', '$source');
      body.append('$source', 'Website footer');
      fetch('https://manage.kmail-lists.com/ajax/subscriptions/subscribe?company_id=' + cfg.klaviyo,
            {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: body})
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res && res.success === false) throw new Error((res.errors || [])[0] || 'refused');
          btn.textContent = "You're on the list"; input.value = '';
        })
        .catch(function () { btn.textContent = 'Try again'; });
    });
  });

  // Bag: the pieces live in localStorage so the bag, checkout and every page agree
  window.MaconBag = (function () {
    var KEY = 'macon-bag-items';
    function read() { try { var v = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(v) ? v.map(clean).filter(function (it) { return it.slug; }) : []; } catch (e) { return []; } }
    function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }
    function clean(it) { return {variant: /^gid:\/\/shopify\/ProductVariant\/\d+$/.test(it.variant) ? it.variant : '', slug: /^[a-z0-9-]+$/.test(it.slug) ? it.slug : '', name: esc(it.name), img: /^img\/[\w\/.-]+$/.test(it.img) ? it.img : '',
      size: esc(it.size || ''), price: Math.max(0, +it.price || 0), qty: Math.max(1, Math.floor(+it.qty) || 1)}; }
    function write(items) { try { localStorage.setItem(KEY, JSON.stringify(items)); } catch (e) {} document.dispatchEvent(new CustomEvent('bag:change')); }
    function count() { return read().reduce(function (n, i) { return n + (i.qty || 1); }, 0); }
    function add(item) {
      var items = read();
      var same = items.filter(function (i) { return i.slug === item.slug && (i.size || '') === (item.size || ''); })[0];
      if (same) same.qty = (same.qty || 1) + 1; else { item.qty = 1; items.push(item); }
      write(items);
    }
    return {read: read, write: write, count: count, add: add};
  })();

  (function () {
    var bag = document.querySelector('.head .right a'); if (!bag) return;
    bag.setAttribute('href', 'bag.html');
    function paint() { bag.textContent = 'Bag (' + MaconBag.count() + ')'; }
    paint(); document.addEventListener('bag:change', paint);
    addEventListener('storage', paint);
    var toast = document.createElement('div');
    toast.className = 'bag-toast'; toast.setAttribute('role', 'status'); toast.setAttribute('aria-live', 'polite');
    document.querySelector('.head .right').appendChild(toast);
    var timer = null;
    document.querySelectorAll('.cta, .dock').forEach(function (b) {
      if (!/add to bag/i.test(b.textContent)) return;
      b.addEventListener('click', function (e) {
        var title = document.querySelector('.info h1'), hero = document.querySelector('.gallery .hero img'), price = document.querySelector('.info .price');
        var sizeBox = document.querySelector('[data-size]'), size = sizeBox && sizeBox.classList.contains('picked') ? sizeBox.querySelector('.size-value').textContent : '';
        if (sizeBox && !size) {                       // rings need a size before they go in the bag
          e.stopPropagation();                        // or the picker's click-outside handler shuts it again
          sizeBox.classList.add('open', 'need'); sizeBox.querySelector('.size-toggle').setAttribute('aria-expanded', true);
          sizeBox.scrollIntoView({block: 'center', behavior: 'smooth'});
          setTimeout(function () { sizeBox.classList.remove('need'); }, 1600);
          return;
        }
        MaconBag.add({
          slug: location.pathname.split('/').pop().replace('.html', ''),
          name: title ? title.textContent : '', price: price ? parseFloat(price.textContent.replace(/[^0-9.]/g, '')) || 0 : 0,
          img: hero ? hero.getAttribute('src') : '', size: size,
          variant: sizeBox ? (sizeBox.dataset.variant || '') : ((document.getElementById('bag') || {}).dataset || {}).variant || ''
        });
        toast.textContent = '';
        if (hero) { var ti = document.createElement('img'); ti.src = hero.getAttribute('src'); ti.alt = ''; toast.appendChild(ti); }
        var tx = document.createElement('span'), tb = document.createElement('b'); tb.textContent = 'Added to bag';
        tx.appendChild(tb); tx.appendChild(document.createTextNode((title ? title.textContent : '') + (size ? ' · Size ' + size : '')));
        if (price) { var tp = document.createElement('span'); tp.className = 'price-note'; tp.textContent = price.textContent; tx.appendChild(tp); }
        toast.appendChild(tx);
        bag.classList.remove('bump'); void bag.offsetWidth; bag.classList.add('bump');
        toast.classList.add('on'); clearTimeout(timer);
        timer = setTimeout(function () { toast.classList.remove('on'); }, 2600);
      });
    });
  })();

  addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    document.querySelectorAll('.dr-emerge').forEach(function (el) { el.style.transition = 'none'; el.classList.add('is-seen'); });
    // a shopper who backs out of Shopify's checkout returns to a cached page:
    // put any button that was mid-handoff back the way they found it
    document.querySelectorAll('[aria-busy="true"]').forEach(function (b) {
      b.removeAttribute('aria-busy');
      if (b.dataset.label) b.textContent = b.dataset.label;
      b.disabled = false;
    });
  });

  // Back to Shop: on wide screens it sits in the nav row, over the left edge of the right-hand column
  (function () {
    var link = document.querySelector('.back'), head = document.querySelector('.head'); if (!link || !head) return;
    var home = link.parentElement, next = link.nextSibling, wide = matchMedia('(min-width:768px)');
    function place() {
      if (wide.matches) {
        if (link.parentElement !== head) head.appendChild(link);
        var x = 0; for (var el = home; el; el = el.offsetParent) x += el.offsetLeft;
        link.style.left = x + 'px';
      } else if (link.parentElement !== home) { home.insertBefore(link, next); link.style.left = ''; }
    }
    place(); addEventListener('resize', place); addEventListener('load', place);
  })();

  // Apple Pay (product pages): this piece alone, straight to Shopify checkout where Apple Pay is offered
  document.querySelectorAll('.buy .apple-pay').forEach(function (b) {
    b.addEventListener('click', function (e) {
      var sizeBox = document.querySelector('[data-size]');
      if (sizeBox && !sizeBox.classList.contains('picked')) {
        e.stopPropagation(); sizeBox.classList.add('open', 'need');
        setTimeout(function () { sizeBox.classList.remove('need'); }, 1600); return;
      }
      var variant = sizeBox ? sizeBox.dataset.variant : document.getElementById('bag').dataset.variant;
      MaconCheckout([{variant: variant, qty: 1}], b).catch(function () {});
    });
  });

  // Mobile menu
  (function () {
    var btn = document.querySelector('.head .mob'); if (!btn) return;
    var menu = document.createElement('nav');
    menu.className = 'menu-sheet'; menu.setAttribute('aria-label', 'Menu'); menu.inert = true;
    menu.innerHTML = '<button class="menu-close" type="button" aria-label="Close menu">Close</button>' +
      '<a href="index.html#pieces">Shop</a><a href="custom.html">Custom</a><a href="inspiration.html">Inspiration</a>' +
      '<a href="story.html">About</a><a href="shipping.html">Shipping &amp; Returns</a><a href="contact.html">Contact</a><a href="bag.html">Bag</a>';
    [].forEach.call(menu.querySelectorAll('a'), function (a, i) { a.style.setProperty('--i', i); });
    document.body.appendChild(menu);
    btn.setAttribute('role', 'button'); btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('href', '#menu');
    var keyboard = false;
    function set(on) {
      if (on) {          // Close sits exactly where Menu was
        var r = btn.getBoundingClientRect(), c = menu.querySelector('.menu-close');
        c.style.left = r.left + 'px'; c.style.top = r.top + 'px'; c.style.height = r.height + 'px';
      }
      menu.classList.toggle('open', on); menu.inert = !on; open = on;
      document.documentElement.classList.toggle('menu-open', on);
      [].forEach.call(document.body.children, function (c) { if (c !== menu && c.tagName !== 'SCRIPT') c.inert = on; });
      btn.setAttribute('aria-expanded', on); document.documentElement.style.overflow = on ? 'hidden' : '';
      if (on && keyboard) menu.querySelector('a').focus();
    }
    var open = false;
    // tapping the pushed-over page closes the menu
    document.addEventListener('click', function (e) { if (open && !menu.contains(e.target) && e.target !== btn) set(false); });
    btn.addEventListener('click', function (e) { e.preventDefault(); keyboard = e.detail === 0; set(true); });          // focus the first link only for keyboard users, so a tap shows no outline
    menu.querySelector('.menu-close').addEventListener('click', function () { set(false); btn.focus(); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) { set(false); btn.focus(); } });
  })();
</script>
