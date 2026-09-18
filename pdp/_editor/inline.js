/* The studio's editor, laid over the real site.

   It is injected only by the local preview server (pdp/serve.py), so it can never
   reach the published shop. Turn it on with the button at the bottom left, or ?edit.  */
(function () {
  if (window.top !== window.self) return;
  var API = '/api/content';
  var edits = {products: {}, pages: {}, stamp: {}};
  var dirty = false, on = false, bar, msg, count;

  function load() {
    return fetch('/pdp/content.json?' + Date.now()).then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; })
      .then(function (c) {
        edits = {products: c.products || {}, pages: c.pages || {}, shared: c.shared || {}, stamp: c.stamp || {}};
      });
  }

  function slug() { return document.body.dataset.slug || ''; }

  function setDirty(v) {
    dirty = v;
    if (!bar) return;
    bar.classList.toggle('dirty', v);
    count.textContent = v ? changeCount() + ' unsaved' : 'No changes';
    bar.querySelector('.ed-save').disabled = !v;
  }

  function changeCount() {
    var n = Object.keys(edits.pages).length + Object.keys(edits.shared || {}).length + Object.keys(edits.stamp).length;
    Object.keys(edits.products).forEach(function (k) { n += Object.keys(edits.products[k]).length; });
    return n;
  }

  // ── remembering one change ────────────────────────────────────────────
  function record(el, value) {
    var key = el.dataset.edit, dflt = el.dataset.editDefault;
    if (key.indexOf('page:') === 0) {
      var k = key.slice(5);
      if (value === dflt) delete edits.pages[k]; else edits.pages[k] = value;
    } else if (key.indexOf('acc:') === 0) {          // wording shared by every piece of this kind
      var a = key.slice(4);
      if (value === dflt) delete edits.shared[a]; else edits.shared[a] = value;
    } else {
      var s = slug(); if (!s) return;
      var p = edits.products[s] || (edits.products[s] = {});
      var v = key === 'price' ? Number(String(value).replace(/[^0-9.]/g, '')) : value;
      var d = key === 'price' ? Number(String(dflt).replace(/[^0-9.]/g, '')) : dflt;
      if (v === d || v === '' || (key === 'price' && !(v > 0))) delete p[key]; else p[key] = v;
      if (!Object.keys(p).length) delete edits.products[s];
    }
    el.classList.toggle('ed-changed', !!changedHere(el));
    setDirty(changeCount() > 0);
  }

  function changedHere(el) {
    var key = el.dataset.edit;
    if (key.indexOf('page:') === 0) return key.slice(5) in edits.pages;
    if (key.indexOf('acc:') === 0) return key.slice(4) in edits.shared;
    return ((edits.products[slug()] || {})[key] !== undefined);
  }

  // ── turning the page into something you can type into ─────────────────
  function fields() { return [].slice.call(document.querySelectorAll('[data-edit]')); }

  function arm() {
    fields().forEach(function (el) {
      if (!('editDefault' in el.dataset)) el.dataset.editDefault = el.innerHTML.trim();
      el.contentEditable = on ? 'true' : 'false';
      el.spellcheck = true;
      el.classList.toggle('ed-field', on);
      el.classList.toggle('ed-changed', on && !!changedHere(el));
      if (!el.dataset.editBound) {
        el.dataset.editBound = '1';
        el.addEventListener('input', function () { record(el, el.innerHTML.trim()); });
        el.addEventListener('blur', function () { record(el, el.innerHTML.trim()); });
        el.addEventListener('keydown', function (e) {
          if (e.key === 'Escape') { el.innerHTML = el.dataset.editDefault; record(el, el.dataset.editDefault); el.blur(); }
          if (e.key === 'Enter' && el.tagName !== 'P') { e.preventDefault(); el.blur(); }
        });
        el.addEventListener('click', function (e) { if (on) e.stopPropagation(); }, true);
      }
    });
    photos(on);
    stamp(on);
    document.querySelectorAll('.acc-item').forEach(function (it) {
      it.classList.toggle('ed-open', on);          // panels stand open while editing
    });
  }

  // ── photographs ───────────────────────────────────────────────────────
  function photos(show) {
    document.querySelectorAll('.gallery figure').forEach(function (fig, i) {
      var tag = fig.querySelector('.ed-photo');
      if (!show) { if (tag) tag.remove(); fig.classList.remove('ed-fig'); return; }
      fig.classList.add('ed-fig');
      if (tag) return;
      var img = fig.querySelector('img, video'); if (!img) return;
      var src = (img.getAttribute('src') || '').replace(/^\//, '').replace(/\.webp$/, '');
      var box = document.createElement('div');
      box.className = 'ed-photo';
      box.innerHTML = (i === 0 ? '<b>Main photograph</b>' : '<button data-a="hero">Make main</button>') +
                      '<button data-a="out">&#8722;</button><span class="ed-frame-tip">100%</span><button data-a="in">+</button>' +
                      '<button data-a="fit">reset</button>' +
                      '<button data-a="replace">Replace…</button>' +
                      '<button data-a="hide">Hide</button>' +
                      (i > 1 ? '<button data-a="up">&#8592;</button>' : '') +
                      '<button data-a="down">&#8594;</button>';
      if (img.tagName === 'IMG') { armFraming(fig, img, src); paintFrame(img, frameOf(src)); }
      box.addEventListener('click', function (e) {
        var a = e.target.dataset && e.target.dataset.a; if (!a) return;
        e.preventDefault(); e.stopPropagation();
        photoAction(a, src);
      });
      fig.appendChild(box);
    });
  }

  function gallerySrcs() {
    return [].slice.call(document.querySelectorAll('.gallery figure img, .gallery figure video'))
      .map(function (n) { return (n.getAttribute('src') || '').replace(/^\//, '').replace(/\.webp$/, ''); });
  }

  // choosing a picture from the studio's own drive, in place of one on the page
  function choosePhoto(replacing) {
    var s = slug(); if (!s) return;
    var inp = document.createElement('input');
    inp.type = 'file'; inp.accept = 'image/*'; inp.style.display = 'none';
    document.body.appendChild(inp);
    inp.onchange = function () {
      var f = inp.files && inp.files[0];
      inp.remove();
      if (!f) return;
      if (f.size > 24 * 1024 * 1024) { msg.textContent = 'That photograph is over 24MB'; msg.className = 'ed-msg bad'; return; }
      msg.textContent = 'Adding ' + f.name + '…'; msg.className = 'ed-msg';
      fetch('/api/photo?slug=' + encodeURIComponent(s) + '&name=' + encodeURIComponent(f.name),
            {method: 'POST', body: f})
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j.error) throw new Error(j.error);
          var p = edits.products[s] || (edits.products[s] = {});
          var all = gallerySrcs();
          var hero = p.hero || all[0];
          var rest = (p.gallery || all.slice(1)).slice();
          if (replacing === hero) { p.hero = j.added; }
          else {
            var at = rest.indexOf(replacing);
            if (at > -1) rest.splice(at, 1, j.added); else rest.push(j.added);
          }
          p.gallery = rest;
          setDirty(true);
          save(true);
        })
        .catch(function (e) { msg.textContent = 'Could not add it: ' + e.message; msg.className = 'ed-msg bad'; });
    };
    inp.click();
  }

  // ── framing a picture inside its frame, by hand ──────────────────────
  function frameOf(src) {
    var p = edits.products[slug()] || {};
    return Object.assign({x: 50, y: 50, z: 1}, (p.frames || {})[src] || {});
  }

  function setFrame(src, f) {
    var s = slug(); if (!s) return;
    var p = edits.products[s] || (edits.products[s] = {});
    var frames = p.frames || (p.frames = {});
    if (Math.abs(f.x - 50) < 0.6 && Math.abs(f.y - 50) < 0.6 && Math.abs(f.z - 1) < 0.01) delete frames[src];
    else frames[src] = {x: Math.round(f.x * 10) / 10, y: Math.round(f.y * 10) / 10, z: Math.round(f.z * 100) / 100};
    if (!Object.keys(frames).length) delete p.frames;
    if (!Object.keys(p).length) delete edits.products[s];
    setDirty(true);
  }

  function paintFrame(img, f) {
    img.style.objectPosition = f.x + '% ' + f.y + '%';
    img.style.transform = 'scale(' + f.z + ')';
    var tip = img.parentNode.querySelector('.ed-frame-tip');
    if (tip) tip.textContent = Math.round(f.z * 100) + '%';
  }

  function armFraming(fig, img, src) {
    if (fig.dataset.edFrame) return;
    fig.dataset.edFrame = '1';
    var moving = false, sx, sy, start;

    img.addEventListener('pointerdown', function (e) {
      if (!on) return;
      e.preventDefault();
      moving = true; sx = e.clientX; sy = e.clientY; start = frameOf(src);
      img.setPointerCapture(e.pointerId); fig.classList.add('ed-framing');
    });
    img.addEventListener('pointermove', function (e) {
      if (!moving) return;
      var r = img.getBoundingClientRect();
      // how far the picture can travel inside the frame depends on how much of it is hidden
      var f = Object.assign({}, start);
      f.x = Math.max(0, Math.min(100, start.x - (e.clientX - sx) / r.width * 100));
      f.y = Math.max(0, Math.min(100, start.y - (e.clientY - sy) / r.height * 100));
      paintFrame(img, f); setFrame(src, f);
    });
    function end(e) {
      if (!moving) return;
      moving = false; fig.classList.remove('ed-framing');
      try { img.releasePointerCapture(e.pointerId); } catch (err) {}
    }
    img.addEventListener('pointerup', end);
    img.addEventListener('pointercancel', end);
    img.addEventListener('wheel', function (e) {
      if (!on) return;
      e.preventDefault();
      var f = frameOf(src);
      f.z = Math.max(1, Math.min(4, f.z * (e.deltaY < 0 ? 1.06 : 1 / 1.06)));
      paintFrame(img, f); setFrame(src, f);
    }, {passive: false});
  }

  function photoAction(a, src) {
    if (a === 'replace') return choosePhoto(src);
    if (a === 'in' || a === 'out' || a === 'fit') {
      var img = [].slice.call(document.querySelectorAll('.gallery figure img'))
        .filter(function (n) { return (n.getAttribute('src') || '').replace(/^\//, '').replace(/\.webp$/, '') === src; })[0];
      if (!img) return;
      var f = frameOf(src);
      if (a === 'fit') f = {x: 50, y: 50, z: 1};
      else f.z = Math.max(1, Math.min(4, f.z * (a === 'in' ? 1.12 : 1 / 1.12)));
      paintFrame(img, f); setFrame(src, f);
      return;
    }
    var s = slug(); if (!s) return;
    var p = edits.products[s] || (edits.products[s] = {});
    var all = gallerySrcs();
    var hero = p.hero || all[0];
    var rest = (p.gallery || all.slice(1)).slice();
    if (a === 'hero') { rest = rest.filter(function (f) { return f !== src; }); rest.unshift(hero); p.hero = src; }
    if (a === 'hide') rest = rest.filter(function (f) { return f !== src; });
    if (a === 'up' || a === 'down') {
      var j = rest.indexOf(src), to = j + (a === 'up' ? -1 : 1);
      if (j > -1 && to >= 0 && to < rest.length) { rest.splice(j, 1); rest.splice(to, 0, src); }
    }
    p.gallery = rest;
    setDirty(true);
    save(true);          // photographs need a rebuild to be seen, so save straight away
  }

  // ── the Bureau stamp: dragged and resized on the page itself ─────────
  var STAMP_DEFAULT = {w: 13, right: 11.4, drop: 98.3, tilt: -14};

  function stampNow() {
    var s = {};
    Object.keys(STAMP_DEFAULT).forEach(function (k) {
      s[k] = (edits.stamp && typeof edits.stamp[k] === 'number') ? edits.stamp[k] : STAMP_DEFAULT[k];
    });
    return s;
  }

  var round1 = function (n) { return Math.round(n * 10) / 10; };

  function stampPaint(el, s) {
    el.style.width = 'clamp(60px,' + s.w + 'vw,40vw)';
    el.style.right = s.right + 'vw';
    el.style.transform = 'translateY(' + s.drop + '%) rotate(' + s.tilt + 'deg)';
    var tip = document.querySelector('.ed-stamp-tip');
    if (tip) tip.textContent = round1(s.w) + 'vw wide · ' + round1(s.right) + ' from right · ' + Math.round(s.tilt) + '°';
    stampBox(el, s);
  }

  // the outline with a handle at each corner, laid exactly over the stamp
  function stampBox(el, s) {
    var box = document.querySelector('.ed-stamp-box');
    if (!box) return;
    box.style.width = el.offsetWidth + 'px';
    box.style.height = el.offsetHeight + 'px';
    box.style.right = s.right + 'vw';
    box.style.transform = 'translateY(' + s.drop + '%) rotate(' + s.tilt + 'deg)';
  }

  function stamp(show) {
    var el = document.querySelector('.stamp');
    if (!el) return;
    var tools = document.querySelector('.ed-stamp'), box = document.querySelector('.ed-stamp-box');
    if (!show) {
      if (tools) tools.remove();
      if (box) box.remove();
      el.classList.remove('ed-stamp-on'); el.style.cursor = '';
      return;
    }
    el.classList.add('ed-stamp-on', 'on');
    el.style.cursor = 'grab';

    if (!box) {
      box = document.createElement('div');
      box.className = 'ed-stamp-box';
      ['nw', 'ne', 'sw', 'se'].forEach(function (c) {
        var h = document.createElement('i'); h.className = 'h ' + c; h.dataset.corner = c; box.appendChild(h);
      });
      el.parentNode.appendChild(box);
      box.addEventListener('pointerdown', function (e) {
        if (!e.target.dataset.corner) return;
        e.preventDefault(); e.stopPropagation();
        var s0 = stampNow();
        var r = el.getBoundingClientRect();
        var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        var d0 = Math.hypot(e.clientX - cx, e.clientY - cy) || 1;
        var w0 = s0.w;
        box.setPointerCapture(e.pointerId);
        function move(ev) {
          var d = Math.hypot(ev.clientX - cx, ev.clientY - cy);
          var s = stampNow();
          s.w = round1(Math.max(3, Math.min(40, w0 * (d / d0))));
          edits.stamp = s; stampPaint(el, s); setDirty(true);
        }
        function up(ev) {
          box.releasePointerCapture(ev.pointerId);
          box.removeEventListener('pointermove', move); box.removeEventListener('pointerup', up);
        }
        box.addEventListener('pointermove', move); box.addEventListener('pointerup', up);
      });
    }

    if (!tools) {
      tools = document.createElement('div');
      tools.className = 'ed-stamp';
      tools.innerHTML = '<b>Stamp</b><button data-t="-2">tilt &#8634;</button><button data-t="2">tilt &#8635;</button>' +
                        '<button data-r="1">reset</button><span class="ed-stamp-tip"></span>';
      el.parentNode.appendChild(tools);
      tools.addEventListener('click', function (e) {
        var d = e.target.dataset || {}; var s = stampNow();
        if (d.t) s.tilt = Math.max(-45, Math.min(45, s.tilt + Number(d.t)));
        else if (d.r) s = Object.assign({}, STAMP_DEFAULT);
        else return;
        edits.stamp = s; stampPaint(el, s); setDirty(true);
      });
    }

    if (!el.dataset.edStampBound) {
      el.dataset.edStampBound = '1';
      el.addEventListener('pointerdown', function (e) {
        if (!on) return;
        e.preventDefault();
        var s0 = stampNow(), x0 = e.clientX, y0 = e.clientY, r0 = s0.right, d0 = s0.drop;
        el.setPointerCapture(e.pointerId); el.style.cursor = 'grabbing';
        function move(ev) {
          var s = stampNow();
          // it may travel anywhere down the page, over the writing below the film
          s.right = round1(Math.max(-5, Math.min(92, r0 - (ev.clientX - x0) / innerWidth * 100)));
          s.drop  = round1(Math.max(-60, Math.min(900, d0 + (ev.clientY - y0) / el.offsetHeight * 100)));
          edits.stamp = s; stampPaint(el, s); setDirty(true);
        }
        function up(ev) {
          el.releasePointerCapture(ev.pointerId); el.style.cursor = 'grab';
          el.removeEventListener('pointermove', move); el.removeEventListener('pointerup', up);
        }
        el.addEventListener('pointermove', move); el.addEventListener('pointerup', up);
      });
    }
    stampPaint(el, stampNow());
  }

  // ── saving ────────────────────────────────────────────────────────────
  function save(reload) {
    msg.textContent = 'Saving…'; msg.className = 'ed-msg';
    return fetch(API, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(edits)})
      .then(function (r) { return r.json().then(function (j) { return {ok: r.ok, j: j}; }); })
      .then(function (res) {
        if (res.j && res.j.saved) setDirty(false);
        if (!res.ok || (res.j && res.j.error)) throw new Error((res.j && res.j.error) || 'could not save');
        msg.textContent = 'Saved';
        if (reload) location.reload();
        else setTimeout(function () { msg.textContent = ''; }, 2500);
      })
      .catch(function (e) { msg.textContent = e.message; msg.className = 'ed-msg bad'; });
  }

  function revertAll() {
    if (!confirm('Put every word and photograph back the way it was?')) return;
    edits = {products: {}, pages: {}, shared: {}, stamp: {}};
    setDirty(true);
    save(true);
  }

  // ── the bar along the bottom ──────────────────────────────────────────
  function build() {
    var css = document.createElement('style');
    css.textContent = [
      '.ed-bar{position:fixed;left:0;right:0;bottom:0;z-index:99999;display:flex;align-items:center;gap:12px;',
      ' padding:9px 16px;background:#111;color:#fff;font:13px/1.4 ui-sans-serif,-apple-system,sans-serif;',
      ' transform:translateY(105%);transition:transform .3s cubic-bezier(.3,.8,.3,1)}',
      '.ed-bar.show{transform:none}',
      '.ed-peek{position:fixed;left:0;right:0;bottom:0;height:26px;z-index:99998}',
      '.ed-tab{position:fixed;right:16px;bottom:0;z-index:99998;background:#111;color:#fff;border:0;',
      ' border-radius:7px 7px 0 0;padding:4px 12px;font:12px ui-sans-serif,sans-serif;cursor:pointer;opacity:.5;',
      ' transition:opacity .25s ease}',
      '.ed-tab:hover{opacity:1}',
      'body.ed-barred .ed-tab{display:none}',
      '.ed-bar button{font:inherit;border:1px solid #444;background:#1b1b1b;color:#fff;border-radius:6px;padding:5px 11px;cursor:pointer}',
      '.ed-bar button:hover{border-color:#888}',
      '.ed-bar .ed-save{background:#fff;color:#111;border-color:#fff}',
      '.ed-bar .ed-save:disabled{opacity:.4;cursor:default}',
      '.ed-bar .grow{flex:1}.ed-msg{opacity:.75}.ed-msg.bad{color:#ff9b8a;opacity:1}',
      '.ed-count{opacity:.6}.ed-bar.dirty .ed-count{opacity:1;color:#ffd08a}',
      'body.ed-on [data-edit]{outline:1px dashed rgba(0,0,0,.25);outline-offset:3px;border-radius:2px;cursor:text}',
      'body.ed-on [data-edit]:hover{outline-color:rgba(0,0,0,.6);background:rgba(255,246,222,.5)}',
      'body.ed-on [data-edit]:focus{outline:2px solid #111;background:#fffdf6}',
      'body.ed-on .ed-changed{outline-color:#9a5b21;background:rgba(255,241,220,.6)}',
      'body.ed-on{padding-bottom:46px}',
      'body.ed-on .acc-item.ed-open .acc-panel{grid-template-rows:1fr!important;height:auto!important;',
      ' max-height:none!important;visibility:visible!important;opacity:1!important}',
      '.ed-fig{position:relative}',
      '.ed-photo{position:absolute;left:10px;bottom:10px;display:flex;gap:5px;align-items:center;',
      ' background:rgba(17,17,17,.88);border-radius:7px;padding:5px 7px;z-index:5}',
      '.ed-photo b{color:#fff;font:500 11px ui-sans-serif,sans-serif;padding:0 4px}',
      '.ed-photo button{font:11px ui-sans-serif,sans-serif;border:1px solid #555;background:#222;color:#fff;',
      ' border-radius:5px;padding:3px 7px;cursor:pointer}',
      '.ed-photo button:hover{border-color:#aaa}',
      '.ed-photo .ed-frame-tip{color:#bbb;font:11px ui-sans-serif,sans-serif;min-width:34px;text-align:center}',
      'body.ed-on .gallery figure{overflow:hidden}',
      'body.ed-on .gallery figure img{cursor:grab}',
      'body.ed-on .gallery figure.ed-framing img{cursor:grabbing}',
      'body.ed-on .gallery figure.ed-framing{outline:2px solid #111;outline-offset:-2px}',
      '.ed-stamp-on{pointer-events:auto!important;opacity:1!important;outline:1px dashed rgba(0,0,0,.35);outline-offset:6px}',
      '.ed-stamp{position:absolute;right:10px;bottom:8px;display:flex;gap:5px;align-items:center;z-index:6;',
      ' background:rgba(17,17,17,.88);border-radius:7px;padding:5px 7px}',
      '.ed-stamp b{color:#fff;font:500 11px ui-sans-serif,sans-serif;padding:0 4px}',
      '.ed-stamp span{color:#bbb;font:11px ui-sans-serif,sans-serif;padding:0 4px}',
      '.ed-stamp button{font:11px ui-sans-serif,sans-serif;border:1px solid #555;background:#222;color:#fff;',
      ' border-radius:5px;padding:3px 7px;cursor:pointer}',
      '.ed-stamp button:hover{border-color:#aaa}',
      '.ed-stamp-box{position:absolute;right:0;bottom:0;z-index:7;pointer-events:none;',
      ' outline:1px dashed rgba(17,17,17,.55);outline-offset:0}',
      '.ed-stamp-box .h{position:absolute;width:11px;height:11px;background:#fff;border:1px solid #111;',
      ' border-radius:2px;pointer-events:auto;cursor:nwse-resize}',
      '.ed-stamp-box .nw{left:-6px;top:-6px}.ed-stamp-box .ne{right:-6px;top:-6px;cursor:nesw-resize}',
      '.ed-stamp-box .sw{left:-6px;bottom:-6px;cursor:nesw-resize}.ed-stamp-box .se{right:-6px;bottom:-6px}'
    ].join('');
    document.head.appendChild(css);

    bar = document.createElement('div');
    bar.className = 'ed-bar';
    bar.innerHTML = '<button class="ed-toggle">Edit this page</button>' +
      '<span class="ed-count">No changes</span><span class="grow"></span>' +
      '<span class="ed-msg"></span>' +
      '<button class="ed-revert">Undo everything</button>' +
      '<button class="ed-save" disabled>Save &amp; rebuild</button>' +
      '<button class="ed-close" title="Hide this bar">&#10005;</button>';
    document.body.appendChild(bar);

    // it stays out of the way: reach for the bottom of the screen and it comes up
    var peek = document.createElement('div'); peek.className = 'ed-peek';
    var tab = document.createElement('button'); tab.className = 'ed-tab'; tab.textContent = 'Edit';
    document.body.appendChild(peek); document.body.appendChild(tab);
    var hideTimer, pinned = false;
    function showBar(keep) {
      clearTimeout(hideTimer);
      bar.classList.add('show'); document.body.classList.add('ed-barred');
      if (keep) pinned = true;
    }
    function hideBar(force) {
      if ((pinned || dirty || on) && !force) return;
      bar.classList.remove('show'); document.body.classList.remove('ed-barred');
    }
    function laterHide() { clearTimeout(hideTimer); hideTimer = setTimeout(hideBar, 1200); }
    peek.addEventListener('pointerenter', function () { showBar(false); });
    bar.addEventListener('pointerenter', function () { clearTimeout(hideTimer); });
    bar.addEventListener('pointerleave', laterHide);
    tab.addEventListener('click', function () { showBar(true); });
    window.MaconEditorBar = {show: showBar, hide: hideBar};
    msg = bar.querySelector('.ed-msg');
    count = bar.querySelector('.ed-count');
    bar.querySelector('.ed-save').onclick = function () { save(true); };
    bar.querySelector('.ed-revert').onclick = revertAll;
    bar.querySelector('.ed-toggle').onclick = function () {
      on = !on;
      document.body.classList.toggle('ed-on', on);
      this.textContent = on ? 'Done editing' : 'Edit this page';
      arm();
      try { sessionStorage.setItem('macon-edit', on ? '1' : '0'); } catch (e) {}
      if (on) showBar(true); else { pinned = false; hideBar(true); }
    };
    bar.querySelector('.ed-close').onclick = function () { pinned = false; hideBar(true); };
    addEventListener('beforeunload', function (e) { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
  }

  load().then(function () {
    build();
    var want = /[?&]edit/.test(location.search);
    try { want = want || sessionStorage.getItem('macon-edit') === '1'; } catch (e) {}
    if (want) { bar.querySelector('.ed-toggle').click(); }
    setDirty(changeCount() > 0 && false);
  });
})();
