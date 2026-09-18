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
        edits = {products: c.products || {}, pages: c.pages || {}, stamp: c.stamp || {}};
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
    var n = Object.keys(edits.pages).length + Object.keys(edits.stamp).length;
    Object.keys(edits.products).forEach(function (k) { n += Object.keys(edits.products[k]).length; });
    return n;
  }

  // ── remembering one change ────────────────────────────────────────────
  function record(el, value) {
    var key = el.dataset.edit, dflt = el.dataset.editDefault;
    if (key.indexOf('page:') === 0) {
      var k = key.slice(5);
      if (value === dflt) delete edits.pages[k]; else edits.pages[k] = value;
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
  }

  // ── photographs ───────────────────────────────────────────────────────
  function photos(show) {
    document.querySelectorAll('.gallery figure').forEach(function (fig, i) {
      var tag = fig.querySelector('.ed-photo');
      if (!show) { if (tag) tag.remove(); fig.classList.remove('ed-fig'); return; }
      fig.classList.add('ed-fig');
      if (tag) return;
      var img = fig.querySelector('img, video'); if (!img) return;
      var src = (img.getAttribute('src') || '').replace(/^\//, '').replace(/\.webp$/, '.jpg');
      var box = document.createElement('div');
      box.className = 'ed-photo';
      box.innerHTML = (i === 0 ? '<b>Main photograph</b>' : '<button data-a="hero">Make main</button>') +
                      '<button data-a="hide">Hide</button>' +
                      (i > 1 ? '<button data-a="up">←</button>' : '') +
                      '<button data-a="down">→</button>';
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
      .map(function (n) { return (n.getAttribute('src') || '').replace(/^\//, '').replace(/\.webp$/, '.jpg'); });
  }

  function photoAction(a, src) {
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
    edits = {products: {}, pages: {}, stamp: {}};
    setDirty(true);
    save(true);
  }

  // ── the bar along the bottom ──────────────────────────────────────────
  function build() {
    var css = document.createElement('style');
    css.textContent = [
      '.ed-bar{position:fixed;left:0;right:0;bottom:0;z-index:99999;display:flex;align-items:center;gap:12px;',
      ' padding:9px 16px;background:#111;color:#fff;font:13px/1.4 ui-sans-serif,-apple-system,sans-serif}',
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
      '.ed-fig{position:relative}',
      '.ed-photo{position:absolute;left:10px;bottom:10px;display:flex;gap:5px;align-items:center;',
      ' background:rgba(17,17,17,.88);border-radius:7px;padding:5px 7px;z-index:5}',
      '.ed-photo b{color:#fff;font:500 11px ui-sans-serif,sans-serif;padding:0 4px}',
      '.ed-photo button{font:11px ui-sans-serif,sans-serif;border:1px solid #555;background:#222;color:#fff;',
      ' border-radius:5px;padding:3px 7px;cursor:pointer}',
      '.ed-photo button:hover{border-color:#aaa}'
    ].join('');
    document.head.appendChild(css);

    bar = document.createElement('div');
    bar.className = 'ed-bar';
    bar.innerHTML = '<button class="ed-toggle">Edit this page</button>' +
      '<span class="ed-count">No changes</span><span class="grow"></span>' +
      '<span class="ed-msg"></span>' +
      '<button class="ed-revert">Undo everything</button>' +
      '<button class="ed-save" disabled>Save &amp; rebuild</button>';
    document.body.appendChild(bar);
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
    };
    addEventListener('beforeunload', function (e) { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
  }

  load().then(function () {
    build();
    var want = /[?&]edit/.test(location.search);
    try { want = want || sessionStorage.getItem('macon-edit') === '1'; } catch (e) {}
    if (want) bar.querySelector('.ed-toggle').click();
    setDirty(changeCount() > 0 && false);
  });
})();
