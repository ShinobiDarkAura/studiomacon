/* editor.js: an in-place design editor for any web page. One file, no dependencies, for local development only.
 *
 * Nothing shows until the pointer finds something. Then that element's padding (green), margin (orange), gaps
 * (pink) and handles (blue) appear, and you drag them. Click something for a small chip of − / + steppers that
 * fit what it is (type, image, logo, box). Every change is a CSS override kept in one stylesheet, so it survives
 * re-renders and applies to every element like the one you touched. Copy puts a change list on the clipboard
 * for Claude to apply to the real source.
 *
 * On: add ?edit to the address, or press ⌥E (it stays on across pages until ⌥E again or ?edit=0).
 * A project that already uses ?edit sets window.EDITOR_CONFIG = {param: 'design'} before loading it.
 * API: window.__editor.on() / .off() / .copy() / .reset() / .report()
 */
(() => {
  'use strict';
  if (window.__editor) return;
  const D = document, W = window;
  const STORE = 'editor:' + location.host, ONKEY = 'editor:on';
  const PARAM = (W.EDITOR_CONFIG && W.EDITOR_CONFIG.param) || 'edit';          // the address word that turns it on, if a project already uses ?edit
  const COL = {el: '#2563EB', pad: '#16A34A', mar: '#EA580C', gap: '#DB2777', mea: '#9333EA'};

  /* ── changes, kept across reloads until Reset ─────────────────────────────── */
  // rules: [{sel, scope:'all'|'page'|'one', page, route, label, widths:[], props:{prop:{from, to, authored}}}]
  // texts: [{sel, page, from, to}]
  let S = {rules: [], texts: []};
  try { const j = JSON.parse(localStorage.getItem(STORE) || 'null'); if (j && Array.isArray(j.rules)) S = j; } catch (e) {}
  const save = () => { try { localStorage.setItem(STORE, JSON.stringify(S)); } catch (e) {} };
  let past = [], future = [];
  const mark = () => { past.push(JSON.stringify(S)); if (past.length > 300) past.shift(); future = []; };
  const undo = () => { if (!past.length) return; future.push(JSON.stringify(S)); S = JSON.parse(past.pop()); commit(true); };
  const redo = () => { if (!future.length) return; past.push(JSON.stringify(S)); S = JSON.parse(future.pop()); commit(true); };

  /* ── the one stylesheet every change lives in ─────────────────────────────── */
  const sheet = D.createElement('style'); sheet.id = 'editor-overrides';
  const mount = () => { if (!sheet.isConnected || sheet !== (D.head || D.documentElement).lastElementChild) (D.head || D.documentElement).appendChild(sheet); };
  const here = r => r.scope !== 'page' || r.page === location.pathname;
  function css() {
    mount();
    sheet.textContent = S.rules.filter(here).map(r =>
      r.sel + '{' + Object.keys(r.props).map(p => p + ':' + r.props[p].to + ' !important').join(';') + '}').join('\n');
  }
  const bare = (el, prop) => {          // the value the page itself gives, overrides set aside
    const s = sheet.sheet; if (s) s.disabled = true;
    const v = getComputedStyle(el).getPropertyValue(prop).trim();
    if (s) s.disabled = false; return v;
  };

  /* ── which elements a change applies to ───────────────────────────────────── */
  const esc = s => (W.CSS && CSS.escape) ? CSS.escape(s) : s.replace(/[^\w-]/g, '\\$&');
  // state classes come and go, and hashed ones change every build: neither may name a rule
  const STATE = /^(is|has)-|^(active|open|on|off|show|shown|hide|hidden|visible|invisible|selected|current|loaded|ready|seen|in-view|entered|entering|leaving|leave|enter|dark|light|hover|focus|disabled)$|(^|-)(active|open|visible|seen|in-view|hovered|focused|loaded)$/;
  const HASH = c => /^(css|sc|jsx|emotion|svelte|astro)-/.test(c) || (c.length >= 6 && /\d/.test(c) && /[A-Z]/.test(c) && /[a-z]/.test(c));
  const MOTION = /(^|-)(emerge|reveal|revealed|animate|animated|anim|fade|faded|appear|appeared|aos|wow|lazy|lazyloaded|inview|in-view|scrolled|sticky|stuck|pinned)(-|$)/;
  // a class a script adds after load is state, not design: learn the ones written in the page's own HTML
  let authoredClasses = null;
  function learnClasses() {
    fetch(location.href, {cache: 'no-store', credentials: 'same-origin'}).then(r => r.text()).then(t => {
      const set = new Set(); for (const m of t.matchAll(/class(?:Name)?=["']([^"']+)["']/g)) m[1].split(/\s+/).forEach(c => c && set.add(c));
      if (set.size > 15) { authoredClasses = set; soon(); }          // a page rendered in the browser has almost none: keep to the word lists
    }).catch(() => {});
  }
  const stable = c => !STATE.test(c) && !MOTION.test(c) && !HASH(c) && !/^editor-/.test(c) && (!authoredClasses || authoredClasses.has(c));
  function classSel(el) {
    const cl = [...el.classList].filter(stable); if (!cl.length) return '';
    const t = el.tagName.toLowerCase();
    return (/^(div|span|section|a|li)$/.test(t) ? '' : t) + cl.map(c => '.' + esc(c)).join('');
  }
  const matches = s => { try { return D.querySelectorAll(s).length; } catch (e) { return 0; } };
  function likeSel(el) {          // every element that shares this one's style
    const own = classSel(el); if (own) return own;
    const tag = el.tagName.toLowerCase();
    for (let a = el.parentElement; a && a !== D.documentElement; a = a.parentElement) {
      const s = classSel(a) || (a.id && !/\d{3,}/.test(a.id) ? '#' + esc(a.id) : '');
      if (s) return s + ' ' + tag;
    }
    return tag;
  }
  function oneSel(el) {          // this element and no other
    const parts = [];
    for (let n = el; n && n.nodeType === 1 && n !== D.documentElement; n = n.parentElement) {
      if (n.id && !/\d{3,}/.test(n.id)) { parts.unshift('#' + esc(n.id)); if (matches(parts.join(' > ')) === 1) break; continue; }
      let s = classSel(n) || n.tagName.toLowerCase();
      const p = n.parentElement;
      if (p && [...p.children].filter(x => { try { return x.matches(s); } catch (e) { return false; } }).length > 1)
        s += ':nth-child(' + ([...p.children].indexOf(n) + 1) + ')';
      parts.unshift(s);
      if (matches(parts.join(' > ')) === 1) break;
    }
    return parts.join(' > ');
  }
  let scope = 'all';          // all like it · this page only · just this one
  const SCOPES = ['all', 'page', 'one'];
  const selFor = (el, sc) => sc === 'one' ? oneSel(el) : likeSel(el);
  const label = el => {
    const t = (el.textContent || '').trim().replace(/\s+/g, ' ');
    return el.tagName.toLowerCase() + (t && t.length < 60 ? ' "' + t.slice(0, 40) + (t.length > 40 ? '…' : '') + '"' : '');
  };

  function ruleFor(el, sc) {
    const sel = selFor(el, sc), page = sc === 'page' ? location.pathname : null;
    let r = S.rules.find(x => x.sel === sel && x.scope === sc && (x.page || null) === page);
    if (!r) { r = {sel, scope: sc, page, route: location.pathname, label: label(el), widths: [], props: {}}; S.rules.push(r); }
    return r;
  }
  const same = (a, b) => String(a).trim() === String(b).trim() ||
    (/^-?[\d.]+(px)?$/.test(String(a).trim()) && /^-?[\d.]+(px)?$/.test(String(b).trim()) && Math.abs(parseFloat(a) - parseFloat(b)) < .01);
  function setProp(el, prop, value, sc = scope) {
    const r = ruleFor(el, sc);
    if (!r.props[prop]) r.props[prop] = {from: bare(el, prop), to: String(value), authored: authored(el, prop)};
    else r.props[prop].to = String(value);
    const w = Math.round(innerWidth); if (!r.widths.includes(w)) r.widths.push(w);
    if (same(r.props[prop].from, value)) delete r.props[prop];
    if (!Object.keys(r.props).length) S.rules.splice(S.rules.indexOf(r), 1);
    css();
  }
  function clearProps(el, props, sc = scope) {
    const sel = selFor(el, sc), page = sc === 'page' ? location.pathname : null;
    const r = S.rules.find(x => x.sel === sel && x.scope === sc && (x.page || null) === page); if (!r) return;
    props.forEach(p => delete r.props[p]);
    if (!Object.keys(r.props).length) S.rules.splice(S.rules.indexOf(r), 1);
    css();
  }

  /* ── how a value was written in the source (for the export) ───────────────── */
  function authored(el, prop) {
    let hit = '';
    const walk = list => {
      for (const r of list) {
        if (r.media && r.cssRules) { try { if (matchMedia(r.media.mediaText).matches) walk(r.cssRules); } catch (e) {} continue; }
        if (r.selectorText && r.style) {
          const v = r.style.getPropertyValue(prop);
          if (v) { try { if (el.matches(r.selectorText)) hit = v.trim(); } catch (e) {} }
        }
        if (r.cssRules && !r.media) walk(r.cssRules);          // @supports, @layer, nesting
      }
    };
    for (const s of D.styleSheets) { if (s.ownerNode === sheet) continue; try { walk(s.cssRules); } catch (e) {} }
    const inl = el.style && el.style.getPropertyValue(prop); if (inl) hit = inl.trim();
    return hit;
  }
  function tokenPx(el, name) {          // a custom property's value in px, measured where the element sits
    const host = /^(IMG|VIDEO|INPUT|BR|HR|SVG|CANVAS|PICTURE)$/i.test(el.tagName) ? el.parentElement : el;
    if (!host) return 0;
    const p = D.createElement('div'); p.style.cssText = 'position:absolute;visibility:hidden;height:0;pointer-events:none;width:var(' + name + ')';
    host.appendChild(p); const w = p.getBoundingClientRect().width; p.remove(); return w;
  }
  function inTokens(el, a, to) {          // the new value, written the way the source writes the old one
    const m = /var\((--[\w-]+)/.exec(a || ''), px = parseFloat(to);
    if (!m || !/px$/.test(String(to).trim()) || !isFinite(px)) return '';
    const t = tokenPx(el, m[1]); if (!t) return '';
    const k = +(px / t).toFixed(3);
    return k === 1 ? 'var(' + m[1] + ')' : 'calc(var(' + m[1] + ') * ' + k + ')';
  }

  /* ── what an element is ───────────────────────────────────────────────────── */
  const cs = el => getComputedStyle(el);
  const tagIs = (el, re) => re.test(el.tagName);
  const isMedia = el => tagIs(el, /^(IMG|VIDEO|CANVAS)$/i) || (cs(el).backgroundImage !== 'none' && !el.textContent.trim() && !el.children.length);
  const isSvg = el => el.tagName.toLowerCase() === 'svg';
  const isText = el => {
    if (isMedia(el) || isSvg(el) || !(el.textContent || '').trim()) return false;
    return [...el.children].every(c => c.tagName === 'BR' || /^inline/.test(cs(c).display));
  };
  const isBoxy = el => { const c = cs(el); return isMedia(el) || (c.backgroundColor !== 'rgba(0, 0, 0, 0)' && c.backgroundColor !== 'transparent') || parseFloat(c.borderTopWidth) > 0 || c.boxShadow !== 'none'; };
  const n = v => parseFloat(v) || 0;

  /* ── the overlay: its own shadow tree, so the page's CSS and ours never meet ── */
  const host = D.createElement('div'); host.id = 'editor-ui';
  host.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = '<style>' + `
    :host{all:initial}*{box-sizing:border-box}
    .layer{position:fixed;inset:0;pointer-events:none;font:500 11px/1.25 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#111;-webkit-font-smoothing:antialiased}
    .box{position:fixed;border:2px solid ${COL.el};border-radius:2px;pointer-events:none}
    .box.sel{border-width:2px;box-shadow:0 0 0 1px rgba(255,255,255,.9),0 0 0 5px rgba(37,99,235,.22)}
    .box.peer{border:1.5px dashed ${COL.el}}
    .band{position:fixed;pointer-events:auto;display:flex;align-items:center;justify-content:center}
    .band.pad{background:rgba(22,163,74,.26)}.band.mar{background:rgba(234,88,12,.24)}
    .band.gap{background:repeating-linear-gradient(45deg,rgba(219,39,119,.34) 0 5px,rgba(219,39,119,.14) 5px 10px)}
    .band.zero{background:none}
    .band:hover,.band.live{filter:saturate(1.8) brightness(1.05)}
    .band.pad:hover{background:rgba(22,163,74,.42)}.band.mar:hover{background:rgba(234,88,12,.4)}
    .band.ns{cursor:ns-resize}.band.ew{cursor:ew-resize}
    .grip{border-radius:4px;box-shadow:0 0 0 2px #fff,0 1px 3px rgba(0,0,0,.35);flex:none}
    .band.ns .grip{width:30px;height:6px}.band.ew .grip{width:6px;height:30px}
    .pad .grip{background:${COL.pad}}.mar .grip{background:${COL.mar}}.gap .grip{background:${COL.gap}}
    .handle{position:fixed;pointer-events:auto;background:${COL.el};box-shadow:0 0 0 2px #fff,0 1px 4px rgba(0,0,0,.4)}
    .handle.rad{width:14px;height:14px;border-radius:50%;cursor:nwse-resize}
    .handle.w{width:7px;height:34px;border-radius:4px;cursor:ew-resize}
    .handle.h{width:34px;height:7px;border-radius:4px;cursor:ns-resize}
    .handle:hover,.handle.live{transform:scale(1.25)}
    .cross{position:fixed;width:26px;height:26px;margin:-13px 0 0 -13px;border:2px solid #fff;border-radius:50%;box-shadow:0 0 0 2px ${COL.el},inset 0 0 0 2px ${COL.el};pointer-events:none}
    .name{position:fixed;background:${COL.el};color:#fff;padding:3px 7px;border-radius:5px;white-space:nowrap;font-weight:600}
    .name em{font-style:normal;opacity:.75;font-weight:500}
    .tag{position:fixed;background:#111;color:#fff;padding:5px 8px;border-radius:6px;white-space:nowrap;font:600 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;opacity:0;transition:opacity .15s}
    .tag.on{opacity:1}
    .ml{position:fixed;background:${COL.mea}}.mt{position:fixed;background:${COL.mea};color:#fff;padding:2px 5px;border-radius:4px;font:600 10px/1 ui-monospace,Menlo,monospace;transform:translate(-50%,-50%)}
    .chip{position:fixed;pointer-events:auto;display:flex;flex-wrap:wrap;gap:4px;align-items:center;background:#fff;border-radius:11px;padding:4px;box-shadow:0 0 0 1px rgba(0,0,0,.1),0 10px 28px -10px rgba(0,0,0,.4);max-width:calc(100vw - 16px)}
    .st{display:flex;align-items:center;border-radius:8px;background:#F4F4F5;height:28px}
    .st button{all:unset;width:22px;height:28px;display:grid;place-items:center;cursor:pointer;font-size:15px;color:#52525B;border-radius:8px}
    .st button:hover{color:#111;background:#E4E4E7}
    .st b{min-width:36px;text-align:center;font:600 11px/28px ui-monospace,SFMono-Regular,Menlo,monospace;cursor:ew-resize;user-select:none}
    .st i{font-style:normal;font-size:10px;color:#A1A1AA;margin:0 7px 0 1px}
    .st input{all:unset;width:44px;text-align:center;font:600 11px ui-monospace,Menlo,monospace;background:#fff;border-radius:5px;height:22px}
    .tog{all:unset;height:28px;padding:0 9px;border-radius:8px;background:#F4F4F5;cursor:pointer;display:flex;align-items:center;gap:5px}
    .tog:hover{background:#E4E4E7}.tog i{font-style:normal;font-size:10px;color:#A1A1AA}
    .sw{width:28px;height:28px;border-radius:8px;position:relative;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15);cursor:pointer}
    .sw input{position:absolute;inset:-6px;width:40px;height:40px;opacity:0;cursor:pointer}
    .scope{display:flex;background:#F4F4F5;border-radius:8px;height:28px;padding:2px}
    .scope button{all:unset;padding:0 8px;border-radius:6px;cursor:pointer;color:#71717A;display:flex;align-items:center}
    .scope button.on{background:#111;color:#fff}
    .pill{position:fixed;right:14px;bottom:14px;pointer-events:auto;display:flex;align-items:center;gap:2px;background:#111;color:#fff;border-radius:999px;padding:4px 4px 4px 12px;font-size:12px;box-shadow:0 8px 24px -8px rgba(0,0,0,.5)}
    .pill .dot{width:7px;height:7px;border-radius:50%;background:#22C55E;margin-right:8px}
    .pill span{color:#A1A1AA;margin-right:6px}
    .pill button{all:unset;padding:6px 10px;border-radius:999px;cursor:pointer;color:#D4D4D8}
    .pill button:hover{background:#27272A;color:#fff}.pill button.k{background:${COL.el};color:#fff}
    .help,.note{position:fixed;right:14px;bottom:62px;width:330px;pointer-events:auto;background:#fff;border-radius:14px;padding:14px 16px;font-size:12px;line-height:1.55;color:#27272A;box-shadow:0 0 0 1px rgba(0,0,0,.08),0 18px 40px -16px rgba(0,0,0,.35);display:none}
    .help.on,.note.on{display:block}.help b{font-weight:650;color:#111}
    .help .k{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
    .note textarea{width:100%;height:180px;font:11px ui-monospace,Menlo,monospace;border:1px solid #E4E4E7;border-radius:8px;padding:8px}
    .hint{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:#111;color:#fff;padding:8px 12px;border-radius:999px;font-size:12px;opacity:0;transition:opacity .3s}
    .hint.on{opacity:1}
  ` + '</style><div class="layer"><div class="dyn"></div><div class="fix"></div></div>';
  const dyn = root.querySelector('.dyn'), fix = root.querySelector('.fix');
  const mk = (cls, parent = dyn, html) => { const d = D.createElement('div'); d.className = cls; if (html != null) d.innerHTML = html; parent.appendChild(d); return d; };
  const at = (d, x, y, w, h) => { d.style.left = x + 'px'; d.style.top = y + 'px'; if (w != null) d.style.width = Math.max(0, w) + 'px'; if (h != null) d.style.height = Math.max(0, h) + 'px'; return d; };
  const tag = mk('tag', fix), pill = mk('pill', fix), help = mk('help', fix), note = mk('note', fix), hint = mk('hint', fix);
  let chip = null;
  let tagTimer;
  const say = (t, x, y) => { tag.textContent = t; at(tag, Math.min(x + 16, innerWidth - 220), Math.min(y + 18, innerHeight - 30)); tag.classList.add('on'); clearTimeout(tagTimer); tagTimer = setTimeout(() => tag.classList.remove('on'), 1200); };
  const flash = t => { hint.textContent = t; hint.classList.add('on'); clearTimeout(flash.t); flash.t = setTimeout(() => hint.classList.remove('on'), 2600); };

  help.innerHTML = `
    <b>Hover</b> anything: its <span class="k" style="background:${COL.pad}"></span>padding, <span class="k" style="background:${COL.mar}"></span>margin,
    <span class="k" style="background:${COL.gap}"></span>gaps and <span class="k" style="background:${COL.el}"></span>corner, width and height handles show. Drag them.<br>
    <b>⇧ drag</b> all four sides · <b>⌥ drag</b> both opposite sides · <b>⌥ hover</b> shows zero margins too<br>
    <b>Click</b> to choose it: a chip of − / + for what it is (type, image, logo or box). Drag a number to scrub it, click it to type one.<br>
    <b>Chosen image:</b> drag or two-finger scroll inside it to reframe, pinch to zoom.<br>
    <b>Chosen, hover another:</b> the distance between them.<br>
    <b>Double-click text</b> to change the words.<br>
    <b>↑ ↓</b> the parent or child · <b>S</b> scope: all like it, this page only, just this one<br>
    <b>Hold \\</b> to see before · <b>⌘Z</b> undo · <b>⇧⌘Z</b> redo · <b>Esc</b> let go · <b>⌥E</b> editor off<br>
    <b>Copy</b> puts the change list on the clipboard: paste it to Claude, who applies it to the source. ⌘-click still follows links.`;

  /* ── state ────────────────────────────────────────────────────────────────── */
  let on = false, hov = null, sel = null, drag = null, alt = false, down = null, editing = null;
  const alive = el => el && el.isConnected;

  function pick(x, y) {
    for (let el of D.elementsFromPoint(x, y)) {
      if (el === host) return 'ui';
      if (el === D.documentElement) continue;
      if (el instanceof SVGElement && !isSvg(el)) { let s = el; while (s.ownerSVGElement) s = s.ownerSVGElement; el = s; }
      const c = cs(el);
      if (+c.opacity === 0 || c.visibility === 'hidden') continue;          // curtains and faded layers are not what you meant
      if (c.display === 'inline' && !tagIs(el, /^(IMG|SVG|VIDEO)$/i) && el.parentElement && el.parentElement !== D.body) el = el.parentElement;          // words belong to their block
      return el;
    }
    return null;
  }

  /* ── drawing ──────────────────────────────────────────────────────────────── */
  // a band is at least 10px thick so it can be grabbed; it grows away from the edge it belongs to
  const MIN = 10;
  function band(kind, side, axis, x, y, w, h, value) {
    const grow = axis === 'ns' ? MIN - h : MIN - w;
    if (grow > 0) {
      const away = {pad: {t: 0, l: 0, b: 1, r: 1}, mar: {t: 1, l: 1, b: 0, r: 0}}[kind];
      const shift = kind === 'gap' ? grow / 2 : away[side] ? grow : 0;
      if (axis === 'ns') { y -= shift; h = MIN; } else { x -= shift; w = MIN; }
    }
    const b = at(mk('band ' + kind + ' ' + axis + (value === 0 ? ' zero' : '')), x, y, w, h);
    b.dataset.k = kind; b.dataset.side = side; mk('grip', b);
    if (drag && drag.k === kind && drag.side === side) b.classList.add('live');
    return b;
  }
  function draw() {
    dyn.textContent = '';
    if (!on) return;
    if (sel && !alive(sel)) sel = null;
    if (hov && !alive(hov)) hov = null;
    const a = (drag && drag.el) || sel || hov; if (!a) { if (chip) placeChip(); return; }
    const r = seen(a), c = cs(a);
    const bt = n(c.borderTopWidth), br = n(c.borderRightWidth), bb = n(c.borderBottomWidth), bl = n(c.borderLeftWidth);
    const P = {t: n(c.paddingTop), r: n(c.paddingRight), b: n(c.paddingBottom), l: n(c.paddingLeft)};
    const M = {t: n(c.marginTop), r: n(c.marginRight), b: n(c.marginBottom), l: n(c.marginLeft)};
    // padding, inside the border
    const ix = r.left + bl, iy = r.top + bt, iw = r.width - bl - br, ih = r.height - bt - bb;
    if (!isMedia(a) && !isSvg(a) && iw > 24 && ih > 16) {
      band('pad', 't', 'ns', ix, iy, iw, P.t, P.t); band('pad', 'b', 'ns', ix, iy + ih - P.b, iw, P.b, P.b);
      band('pad', 'l', 'ew', ix, iy, P.l, ih, P.l); band('pad', 'r', 'ew', ix + iw - P.r, iy, P.r, ih, P.r);
    }
    // margin, outside; zero margins only while ⌥ is held
    if (M.t || alt) band('mar', 't', 'ns', r.left, r.top - Math.max(M.t, 0), r.width, Math.max(M.t, 0), M.t);
    if (M.b || alt) band('mar', 'b', 'ns', r.left, r.bottom, r.width, Math.max(M.b, 0), M.b);
    if (M.l || alt) band('mar', 'l', 'ew', r.left - Math.max(M.l, 0), r.top, Math.max(M.l, 0), r.height, M.l);
    if (M.r || alt) band('mar', 'r', 'ew', r.right, r.top, Math.max(M.r, 0), r.height, M.r);
    // gaps between the children of a flex or grid box: its own, and its parent's (so a gap is found from either side)
    gaps(a, 0); const up = flexUp(a); if (up) gaps(up.el, up.depth);
    at(mk('box' + (sel === a ? ' sel' : '')), r.left, r.top, r.width, r.height);
    // handles: corner radius, width, height
    if (isBoxy(a) && r.width > 30 && r.height > 30) {
      const rad = n(c.borderTopLeftRadius), d = Math.min(Math.max(rad * .29 + 8, 8), Math.min(r.width, r.height) / 3);
      const h = at(mk('handle rad'), r.left + d - 7, r.top + d - 7); h.dataset.k = 'rad';
    }
    const vx = (lo, hi) => (lo + hi) / 2, cy = vx(Math.max(r.top, 0), Math.min(r.bottom, innerHeight)), cx = vx(Math.max(r.left, 0), Math.min(r.right, innerWidth));          // the part on screen
    if (isMedia(a) || isSvg(a) || isText(a)) { const h = at(mk('handle w'), Math.min(r.right - 4, innerWidth - 12), cy - 17); h.dataset.k = 'w'; }
    if ((isMedia(a) || r.height >= innerHeight * .4) && !isText(a)) { const h = at(mk('handle h'), cx - 17, Math.min(r.bottom - 4, innerHeight - 12)); h.dataset.k = 'h'; }
    if (sel === a && isMedia(a) && !tagIs(a, /CANVAS/i)) {
      const [px, py] = framePos(a); at(mk('cross'), r.left + r.width * px / 100, r.top + r.height * py / 100);
    }
    // name
    const nm = mk('name', dyn, esc2(shortName(a)) + ' <em>' + scopeWords(a) + '</em>');
    at(nm, Math.max(6, Math.min(r.left, innerWidth - 260)), r.top > 26 ? r.top - 24 : r.bottom + 30 < innerHeight ? r.bottom + 6 : Math.max(6, r.top + 6));          // above, else below, else just inside
    // distances from the chosen element to the one under the pointer
    if (sel && hov && hov !== sel && !drag) { const q = hov.getBoundingClientRect(); at(mk('box peer'), q.left, q.top, q.width, q.height); measure(sel.getBoundingClientRect(), q, sel.contains(hov) || hov.contains(sel)); }
    if (chip) placeChip();
  }
  function seen(el) {          // the part of an element you can actually see: clipped by any container that hides overflow
    const q = el.getBoundingClientRect(); let l = q.left, t = q.top, rr = q.right, b = q.bottom;
    for (let p = el.parentElement; p && p !== D.documentElement; p = p.parentElement) {
      const c = cs(p); if (c.overflowX === 'visible' && c.overflowY === 'visible') continue;
      const pr = p.getBoundingClientRect();
      if (c.overflowX !== 'visible') { l = Math.max(l, pr.left); rr = Math.min(rr, pr.right); }
      if (c.overflowY !== 'visible') { t = Math.max(t, pr.top); b = Math.min(b, pr.bottom); }
    }
    if (rr <= l || b <= t) return q;
    return {left: l, top: t, right: rr, bottom: b, width: rr - l, height: b - t};
  }
  function flexUp(el) {          // the nearest flex or grid container above, within three levels
    let e = el, d = 0;
    while (e.parentElement && d < 3) { e = e.parentElement; d++; if (/flex|grid/.test(cs(e).display) && e.children.length > 1) return {el: e, depth: d}; }
    return null;
  }
  function gaps(box, owner) {
    const c = cs(box); if (!/flex|grid/.test(c.display)) return;
    const kids = [...box.children].map(k => ({k, q: k.getBoundingClientRect()})).filter(o => o.q.width && o.q.height && !/absolute|fixed/.test(cs(o.k).position));
    let gx = 0, gy = 0;
    for (let i = 0; i < kids.length - 1 && (gx < 6 || gy < 6); i++) {
      const p = kids[i].q, q = kids[i + 1].q, rowOverlap = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
      let b = null;
      if (rowOverlap > 4 && q.left >= p.right - 1 && gx < 6) { b = band('gap', 'gx', 'ew', p.right, Math.max(p.top, q.top), q.left - p.right, rowOverlap, q.left - p.right); gx++; }
      else if (q.top >= p.bottom - 1 && gy < 6) {
        const x0 = Math.min(p.left, q.left), x1 = Math.max(p.right, q.right);
        b = band('gap', 'gy', 'ns', x0, p.bottom, x1 - x0, q.top - p.bottom, q.top - p.bottom); gy++;
      }
      if (b) b.dataset.owner = owner;
    }
  }
  const esc2 = s => s.replace(/[&<>]/g, m => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[m]));
  function shortName(el) { const s = likeSel(el); return s.length > 48 ? s.slice(0, 46) + '…' : s; }
  function scopeWords(el) {
    if (scope === 'one') return 'just this one';
    const k = matches(likeSel(el));
    return (scope === 'page' ? 'this page · ' : '') + (k > 1 ? 'all ' + k : 'only one');
  }
  function line(x, y, w, h, label, lx, ly) { at(mk('ml'), x, y, w, h); if (label != null) { const t = mk('mt'); t.textContent = label; at(t, lx, ly); } }
  function measure(a, b, nested) {
    if (nested) {          // inside its container: distance to each inner edge
      const o = a.left >= b.left && a.right <= b.right ? [a, b] : [b, a], s = o[0], p = o[1], cy = s.top + s.height / 2, cx = s.left + s.width / 2;
      const d = [['l', s.left - p.left], ['r', p.right - s.right], ['t', s.top - p.top], ['b', p.bottom - s.bottom]];
      d.forEach(([k, v]) => { if (v <= 0) return; v = Math.round(v);
        if (k === 'l') line(p.left, cy, v, 1.5, v, p.left + v / 2, cy); if (k === 'r') line(s.right, cy, v, 1.5, v, s.right + v / 2, cy);
        if (k === 't') line(cx, p.top, 1.5, v, v, cx, p.top + v / 2); if (k === 'b') line(cx, s.bottom, 1.5, v, v, cx, s.bottom + v / 2); });
      return;
    }
    const cyA = Math.max(a.top, b.top) + (Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top)) / 2, cxA = Math.max(a.left, b.left) + (Math.min(a.right, b.right) - Math.max(a.left, b.left)) / 2;
    const cy = (a.top + a.bottom) / 2, cx = (a.left + a.right) / 2;
    if (b.left >= a.right) { const v = Math.round(b.left - a.right); line(a.right, isFinite(cyA) && Math.min(a.bottom, b.bottom) > Math.max(a.top, b.top) ? cyA : cy, v, 1.5, v, a.right + v / 2, cyA || cy); }
    else if (a.left >= b.right) { const v = Math.round(a.left - b.right); line(b.right, cy, v, 1.5, v, b.right + v / 2, cy); }
    if (b.top >= a.bottom) { const v = Math.round(b.top - a.bottom); const x = Math.min(a.right, b.right) > Math.max(a.left, b.left) ? cxA : cx; line(x, a.bottom, 1.5, v, v, x, a.bottom + v / 2); }
    else if (a.top >= b.bottom) { const v = Math.round(a.top - b.bottom); line(cx, b.bottom, 1.5, v, v, cx, b.bottom + v / 2); }
  }

  /* ── images: where they sit in their frame ────────────────────────────────── */
  function framePos(el) {
    const v = tagIs(el, /^(IMG|VIDEO)$/i) ? cs(el).objectPosition : cs(el).backgroundPosition;
    const p = (v || '50% 50%').split(/\s+/).map(s => /%$/.test(s) ? parseFloat(s) : s === 'left' || s === 'top' ? 0 : s === 'right' || s === 'bottom' ? 100 : 50);
    return [p[0] ?? 50, p[1] ?? 50];
  }
  function overflow(el) {          // how far, in px, the picture reaches past its box on each axis
    const r = el.getBoundingClientRect(), c = cs(el);
    const nw = el.naturalWidth || el.videoWidth || 0, nh = el.naturalHeight || el.videoHeight || 0, z = n(c.scale) || 1;
    if (!nw || !nh) return [r.width * .5, r.height * .5];
    const fit = c.objectFit, k = fit === 'cover' ? Math.max(r.width / nw, r.height / nh) : fit === 'none' ? 1 : Math.min(r.width / nw, r.height / nh);
    return [Math.max(nw * k * z - r.width, 0), Math.max(nh * k * z - r.height, 0)];
  }
  function reframe(el, dx, dy, x0, y0) {
    const [ox, oy] = overflow(el);
    const x = ox ? Math.max(0, Math.min(100, x0 - dx / ox * 100)) : x0, y = oy ? Math.max(0, Math.min(100, y0 - dy / oy * 100)) : y0;
    const val = (+x.toFixed(1)) + '% ' + (+y.toFixed(1)) + '%';
    setProp(el, tagIs(el, /^(IMG|VIDEO)$/i) ? 'object-position' : 'background-position', val);
    return {val, stuck: !ox && !oy};
  }
  function zoomBy(el, f) {
    const z = Math.max(1, Math.min(4, +((n(cs(el).scale) || 1) * f).toFixed(3)));
    setProp(el, 'scale', z === 1 ? 'none' : z);
    if (el.parentElement && z > 1 && cs(el.parentElement).overflow === 'visible') setProp(el.parentElement, 'overflow', 'clip');          // a zoomed picture stays inside its frame
    return z;
  }

  /* ── dragging a band or handle ────────────────────────────────────────────── */
  const OPP = {t: 'b', b: 't', l: 'r', r: 'l'};
  const PROPS = {pad: s => 'padding-' + {t: 'top', r: 'right', b: 'bottom', l: 'left'}[s], mar: s => 'margin-' + {t: 'top', r: 'right', b: 'bottom', l: 'left'}[s]};
  function startDrag(k, side, e, parent) {
    let el = sel || hov; if (!el) return;
    for (let i = 0; i < (parent || 0) && el.parentElement; i++) el = el.parentElement;          // a gap belongs to the container it sits in
    mark();
    const c = cs(el), start = {};
    if (k === 'pad' || k === 'mar') ['t', 'r', 'b', 'l'].forEach(s => start[s] = n(c.getPropertyValue(PROPS[k](s))));
    if (k === 'gap') { start.gx = n(c.columnGap); start.gy = n(c.rowGap); }
    if (k === 'rad') start.v = n(c.borderTopLeftRadius);
    if (k === 'w') { start.v = el.getBoundingClientRect().width; start.prop = isText(el) ? 'max-width' : 'width'; }
    if (k === 'h') { start.v = el.getBoundingClientRect().height; start.prop = n(c.minHeight) > 0 && authored(el, 'min-height') ? 'min-height' : 'height'; }
    drag = {k, side, el, x: e.clientX, y: e.clientY, start};
  }
  function moveDrag(e) {
    const d = drag, dx = e.clientX - d.x, dy = e.clientY - d.y, el = d.el, st = d.start;
    let msg = '';
    if (d.k === 'pad' || d.k === 'mar') {
      const sign = {pad: {t: dy, b: -dy, l: dx, r: -dx}, mar: {t: -dy, b: dy, l: -dx, r: dx}}[d.k][d.side];
      const sides = e.shiftKey ? ['t', 'r', 'b', 'l'] : e.altKey ? [d.side, OPP[d.side]] : [d.side];
      sides.forEach(s => { let v = Math.round(st[s] + sign); if (d.k === 'pad') v = Math.max(0, v); setProp(el, PROPS[d.k](s), v + 'px'); });
      msg = (d.k === 'pad' ? 'padding ' : 'margin ') + (sides.length === 4 ? 'all' : sides.join('+')) + ' ' + Math.round(n(cs(el).getPropertyValue(PROPS[d.k](d.side)))) + 'px';
    }
    if (d.k === 'gap') {
      const ax = d.side === 'gx', v = Math.max(0, Math.round((ax ? st.gx : st.gy) + (ax ? dx : dy)));
      setProp(el, ax ? 'column-gap' : 'row-gap', v + 'px'); msg = (ax ? 'column gap ' : 'row gap ') + v + 'px';
    }
    if (d.k === 'rad') { const v = Math.max(0, Math.round(st.v + (dx + dy) / 2)); setProp(el, 'border-radius', v + 'px'); msg = 'corners ' + v + 'px'; }
    if (d.k === 'w') {
      const v = Math.max(8, Math.round(st.v + dx)), pw = el.parentElement ? el.parentElement.getBoundingClientRect().width : 0;
      setProp(el, st.prop, v + 'px'); if (isSvg(el)) setProp(el, 'height', 'auto');          // a logo keeps its proportions; a picture keeps its frame
      msg = st.prop + ' ' + v + 'px' + (pw ? ' · ' + (v / pw * 100).toFixed(1) + '% of its frame' : '');
    }
    if (d.k === 'h') { const v = Math.max(8, Math.round(st.v + dy)); setProp(el, st.prop, v + 'px'); msg = st.prop + ' ' + v + 'px · ' + (v / innerHeight * 100).toFixed(1) + 'vh'; }
    if (d.k === 'frame') { const o = reframe(el, dx, dy, st.x, st.y); msg = o.stuck ? 'it fits its frame: zoom in to move it' : 'framing ' + o.val; }
    say(msg + ' · ' + scopeWords(el), e.clientX, e.clientY);
    draw();
  }
  function endDrag() { if (!drag) return; drag = null; commit(); }

  /* ── the chip: − / + for what the chosen thing is ─────────────────────────── */
  function stepper(label, get, set, step, big, fmt = v => String(+v.toFixed(3))) {
    const s = D.createElement('div'); s.className = 'st';
    s.innerHTML = '<button title="smaller (⇧ bigger step)">−</button><b></b><button title="bigger (⇧ bigger step)">+</button><i>' + label + '</i>';
    const [m, b, p] = [s.children[0], s.children[1], s.children[2]];
    const show = () => { b.textContent = fmt(get()); };
    const nudge = (k, e) => { mark(); set(get() + k * (e.shiftKey ? big : step)); show(); commit(); };
    m.onclick = e => nudge(-1, e); p.onclick = e => nudge(1, e);
    // scrub: drag the number sideways; a click without moving lets you type one
    b.onpointerdown = e => {
      e.preventDefault(); b.setPointerCapture(e.pointerId);
      const x0 = e.clientX, v0 = get(); let moved = false;
      b.onpointermove = ev => { const k = Math.round((ev.clientX - x0) / 4); if (!k && !moved) return; if (!moved) mark(); moved = true; set(v0 + k * (ev.shiftKey ? big : step)); show(); draw(); };
      b.onpointerup = () => {
        b.onpointermove = b.onpointerup = null;
        if (moved) { commit(); return; }
        const inp = D.createElement('input'); inp.value = fmt(get()); b.replaceWith(inp); inp.focus(); inp.select();
        const done = ok => { if (ok && inp.value.trim() !== '' && isFinite(parseFloat(inp.value))) { mark(); set(parseFloat(inp.value)); commit(); } inp.replaceWith(b); show(); };
        inp.onkeydown = ev => { ev.stopPropagation(); if (ev.key === 'Enter') done(true); if (ev.key === 'Escape') done(false); };
        inp.onblur = () => done(true);
      };
    };
    show(); return s;
  }
  function toggle(label, values, get, set) {
    const t = D.createElement('button'); t.className = 'tog';
    const show = () => { t.innerHTML = get() + ' <i>' + label + '</i>'; };
    t.onclick = () => { mark(); const i = values.indexOf(get()); set(values[(i + 1) % values.length]); show(); commit(); };
    show(); return t;
  }
  function swatch(title, get, set) {
    const w = D.createElement('label'); w.className = 'sw'; w.title = title;
    const inp = D.createElement('input'); inp.type = 'color';
    const show = () => { const v = get(); w.style.background = v; inp.value = hex(v); };
    inp.onfocus = () => mark();
    inp.oninput = () => { set(inp.value); w.style.background = inp.value; draw(); };
    inp.onchange = () => commit();
    w.appendChild(inp); show(); return w;
  }
  function hex(c) { const m = /rgba?\(([^)]+)\)/.exec(c || ''); if (!m) return '#000000'; const [r, g, b] = m[1].split(',').map(x => parseInt(x)); return '#' + [r, g, b].map(v => (v | 0).toString(16).padStart(2, '0')).join(''); }
  function scopeCtl() {
    const s = D.createElement('div'); s.className = 'scope';
    const words = {all: 'all ' + matches(likeSel(sel)), page: 'this page', one: 'just this'};
    SCOPES.forEach(k => { const b = D.createElement('button'); b.textContent = words[k]; b.title = 'Changes from now on apply to ' + words[k]; if (k === scope) b.className = 'on'; b.onclick = () => { scope = k; buildChip(); draw(); }; s.appendChild(b); });
    return s;
  }
  function buildChip() {
    if (chip) chip.remove(); chip = null;
    if (!on || !sel || !alive(sel)) return;
    const el = sel, c = () => cs(el);
    chip = mk('chip', fix);
    const add = x => chip.appendChild(x);
    const fsz = () => n(c().fontSize);
    if (isSvg(el)) {          // a logo or icon
      add(stepper('width', () => el.getBoundingClientRect().width, v => { setProp(el, 'width', Math.max(4, Math.round(v)) + 'px'); setProp(el, 'height', 'auto'); }, 2, 10, v => Math.round(v)));
      add(swatch('colour', () => c().color, v => { setProp(el, 'color', v); setProp(el, 'fill', v); }));
    } else if (isMedia(el)) {          // a picture
      const pw = () => el.parentElement ? el.parentElement.getBoundingClientRect().width || 1 : 1;
      add(stepper('% of frame', () => el.getBoundingClientRect().width / pw() * 100, v => setProp(el, 'width', Math.max(5, Math.min(100, +v.toFixed(1))) + '%'), 1, 5, v => v.toFixed(1)));
      add(stepper('zoom', () => n(c().scale) || 1, v => { const cur = n(c().scale) || 1; zoomBy(el, Math.max(1, v) / cur); }, .05, .25, v => v.toFixed(2)));
      if (tagIs(el, /^(IMG|VIDEO)$/i)) add(toggle('fit', ['cover', 'contain'], () => c().objectFit === 'contain' ? 'contain' : 'cover', v => setProp(el, 'object-fit', v)));
      const reset = D.createElement('button'); reset.className = 'tog'; reset.textContent = 'reframe'; reset.title = 'Back to the page\'s own framing';
      reset.onclick = () => { mark(); clearProps(el, ['object-position', 'background-position', 'scale']); buildChip(); commit(); }; add(reset);
    } else if (isText(el)) {          // words
      add(stepper('size', fsz, v => setProp(el, 'font-size', Math.max(4, +v.toFixed(2)) + 'px'), 1, 4, v => +v.toFixed(2)));
      add(stepper('tracking', () => { const l = c().letterSpacing; return l === 'normal' ? 0 : n(l) / fsz(); }, v => setProp(el, 'letter-spacing', +v.toFixed(3) + 'em'), .005, .02, v => (v >= 0 ? '' : '') + v.toFixed(3)));
      add(stepper('leading', () => { const l = c().lineHeight; return l === 'normal' ? 1.2 : n(l) / fsz(); }, v => setProp(el, 'line-height', Math.max(.5, +v.toFixed(2))), .05, .2, v => v.toFixed(2)));
      add(stepper('weight', () => n(c().fontWeight) || 400, v => setProp(el, 'font-weight', Math.max(100, Math.min(900, Math.round(v / 50) * 50))), 100, 100, v => Math.round(v)));
      add(toggle('align', ['start', 'center', 'end', 'justify'], () => ({left: 'start', right: 'end'})[c().textAlign] || c().textAlign, v => setProp(el, 'text-align', v)));
      add(toggle('case', ['none', 'uppercase', 'lowercase', 'capitalize'], () => c().textTransform, v => setProp(el, 'text-transform', v)));
      add(swatch('colour', () => c().color, v => setProp(el, 'color', v)));
    } else {          // a box
      add(stepper('scale', () => n(c().zoom) || 1, v => setProp(el, 'zoom', Math.max(.2, +v.toFixed(3))), .05, .2, v => v.toFixed(2)));
      add(stepper('opacity', () => n(c().opacity), v => setProp(el, 'opacity', Math.max(0, Math.min(1, +v.toFixed(2)))), .05, .2, v => v.toFixed(2)));
      add(swatch('background', () => c().backgroundColor, v => setProp(el, 'background-color', v)));
    }
    add(scopeCtl());
    placeChip();
  }
  function placeChip() {
    if (!chip || !sel || !alive(sel)) return;
    const r = sel.getBoundingClientRect(), h = chip.offsetHeight || 36, w = chip.offsetWidth || 300;
    const c = cs(sel), mb = Math.max(0, n(c.marginBottom)), mt = Math.max(0, n(c.marginTop));          // clear of its margin, where its own handles are
    let y = r.bottom + mb + 12; if (y + h > innerHeight - 64) y = r.top - mt - h - 34; if (y < 8) y = Math.max(8, Math.min(innerHeight - h - 64, r.bottom - h - 14));          // no room outside: just inside its bottom edge, clear of its name and the site's nav
    at(chip, Math.max(8, Math.min(r.left, innerWidth - w - 8)), y);
  }

  /* ── choosing ─────────────────────────────────────────────────────────────── */
  function choose(el) { sel = el; buildChip(); draw(); }

  /* ── words ────────────────────────────────────────────────────────────────── */
  function editText(el) {
    if (editing) return; editing = el;
    const before = el.textContent;
    el.contentEditable = 'plaintext-only'; if (el.contentEditable !== 'plaintext-only') el.contentEditable = 'true';
    el.focus();
    const r = D.createRange(); r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r);
    const finish = keep => {
      el.removeEventListener('blur', onBlur); el.removeEventListener('keydown', onKey, true);
      el.contentEditable = 'inherit'; el.removeAttribute('contenteditable'); editing = null;
      if (!keep) { el.textContent = before; return; }
      const after = el.textContent; if (after === before) return;
      mark(); const sel1 = oneSel(el);
      const t = S.texts.find(x => x.sel === sel1 && x.page === location.pathname);
      if (t) t.to = after; else S.texts.push({sel: sel1, page: location.pathname, from: before, to: after});
      commit();
    };
    const onBlur = () => finish(true);
    const onKey = e => { e.stopPropagation(); if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); finish(true); } if (e.key === 'Escape') { e.preventDefault(); finish(false); } };
    el.addEventListener('blur', onBlur); el.addEventListener('keydown', onKey, true);
  }
  function applyTexts() {
    S.texts.filter(t => t.page === location.pathname).forEach(t => { try { const el = D.querySelector(t.sel); if (el && el.textContent === t.from) el.textContent = t.to; } catch (e) {} });
  }

  /* ── the change list, for Claude ──────────────────────────────────────────── */
  function report() {
    const out = [], plain = [];
    out.push('Design edits from /editor on ' + location.origin + location.pathname + ' (window ' + innerWidth + '×' + innerHeight + ')');
    out.push('Apply these to the source files, then press Reset in the editor. Values were tried live in the browser.');
    out.push('');
    let i = 0;
    S.rules.forEach(r => {
      const el = (() => { try { return D.querySelector(r.sel); } catch (e) { return null; } })();
      const k = matches(r.sel);
      const where = r.scope === 'one' ? 'just this one (' + r.label + ')' : r.scope === 'page' ? 'this page only, ' + r.page + (k ? ' (' + k + ' here)' : '') : 'site-wide, every ' + r.sel + (k ? ' (' + k + ' on this page)' : '');
      const widths = r.widths.map(w => w + 'px' + (w < 768 ? ' (narrow)' : '')).join(', ');
      out.push((++i) + '. ' + r.sel + ': ' + where + ' · edited at ' + widths + (r.route !== location.pathname && r.scope !== 'page' ? ' · on ' + r.route : ''));
      Object.keys(r.props).forEach(p => {
        const v = r.props[p], tok = el ? inTokens(el, v.authored, v.to) : '';
        out.push('   ' + p + ': ' + (v.from || '(unset)') + ' → ' + v.to + (v.authored ? '   [written as: ' + v.authored + (tok ? ' → ' + tok : '') + ']' : ''));
      });
      plain.push((r.scope === 'page' ? '/* only on ' + r.page + ' */ ' : '') + r.sel + ' { ' + Object.keys(r.props).map(p => p + ': ' + r.props[p].to).join('; ') + ' }');
    });
    S.texts.forEach(t => { out.push((++i) + '. Words on ' + t.page + ', ' + t.sel + ':'); out.push('   "' + t.from + '" → "' + t.to + '"'); });
    if (!i) return 'No design edits yet.';
    out.push(''); out.push('As CSS overrides (for reference; write them into the source the way it is written):'); out.push('```css'); out.push(...plain); out.push('```');
    return out.join('\n');
  }
  function copy() {
    const text = report();
    const shown = () => { note.innerHTML = '<b>Copy this and paste it to Claude</b><textarea></textarea>'; const ta = note.querySelector('textarea'); ta.value = text; note.classList.add('on'); ta.focus(); ta.select(); };
    (navigator.clipboard && navigator.clipboard.writeText ? navigator.clipboard.writeText(text) : Promise.reject())
      .then(() => flash('Copied ' + count() + ' change' + (count() === 1 ? '' : 's') + ': paste it to Claude, then Reset once applied'))
      .catch(shown);
  }
  const count = () => S.rules.reduce((a, r) => a + Object.keys(r.props).length, 0) + S.texts.length;

  /* ── changes already in the code drop out on their own ────────────────────── */
  function tidy() {
    let gone = 0;
    S.rules.filter(here).forEach(r => {
      let el; try { el = D.querySelector(r.sel); } catch (e) {} if (!el) return;
      Object.keys(r.props).forEach(p => { if (same(bare(el, p), r.props[p].to)) { delete r.props[p]; gone++; } });
    });
    S.rules = S.rules.filter(r => Object.keys(r.props).length);
    if (gone) { save(); css(); if (on) flash(gone + ' change' + (gone === 1 ? ' is' : 's are') + ' already in the code: cleared'); }
  }

  /* ── the pill ─────────────────────────────────────────────────────────────── */
  let resetArmed = false;
  function drawPill() {
    const k = count();
    pill.innerHTML = '<i class="dot"></i><span>' + (k ? k + ' change' + (k === 1 ? '' : 's') : 'editor') + '</span>' +
      (k ? '<button data-a="undo">Undo</button><button data-a="reset">' + (resetArmed ? 'Reset all?' : 'Reset') + '</button><button class="k" data-a="copy">Copy</button>' : '') +
      '<button data-a="help">?</button><button data-a="off" title="Editor off (⌥E)">×</button>';
  }
  pill.addEventListener('click', e => {
    const a = e.target.dataset && e.target.dataset.a; if (!a) return;
    if (a === 'undo') undo();
    if (a === 'copy') copy();
    if (a === 'help') { help.classList.toggle('on'); note.classList.remove('on'); }
    if (a === 'off') setOn(false);
    if (a === 'reset') {
      if (!resetArmed) { resetArmed = true; drawPill(); setTimeout(() => { resetArmed = false; drawPill(); }, 2500); return; }
      mark(); S = {rules: [], texts: []}; resetArmed = false; commit(); flash('All changes cleared (⌘Z brings them back)');
    }
  });

  function commit(fromHistory) { css(); save(); drawPill(); if (fromHistory) { applyTexts(); buildChip(); } else if (chip) buildChip(); draw(); }

  /* ── input ────────────────────────────────────────────────────────────────── */
  const inUI = e => e.composedPath().includes(host);
  const handleOf = e => e.composedPath().find(x => x.dataset && x.dataset.k);
  let raf = 0;
  const soon = () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; draw(); }); };

  W.addEventListener('pointermove', e => {
    if (!on) return;
    if (drag) { e.preventDefault(); moveDrag(e); return; }
    if (down && down.frame && Math.hypot(e.clientX - down.x, e.clientY - down.y) > 3) {          // dragging inside a chosen picture
      const [x, y] = framePos(sel); mark(); drag = {k: 'frame', el: sel, x: down.x, y: down.y, start: {x, y}}; down = null; moveDrag(e); return;
    }
    const p = pick(e.clientX, e.clientY);
    if (p !== 'ui' && p !== hov) { hov = p; soon(); }
  }, true);
  W.addEventListener('pointerdown', e => {
    if (!on || e.button !== 0) return;
    const h = handleOf(e);
    if (h) { e.preventDefault(); e.stopPropagation(); startDrag(h.dataset.k, h.dataset.side, e, +(h.dataset.owner || 0)); return; }
    if (inUI(e) || e.metaKey || e.ctrlKey || editing) return;
    const p = pick(e.clientX, e.clientY);
    down = {x: e.clientX, y: e.clientY, frame: sel && p === sel && isMedia(sel) && !tagIs(sel, /CANVAS/i)};
    e.preventDefault();          // no text selection or native image drag while editing
  }, true);
  W.addEventListener('pointerup', () => { if (drag) endDrag(); }, true);
  W.addEventListener('click', e => {
    if (!on || inUI(e) || e.metaKey || e.ctrlKey || editing) return;
    e.preventDefault(); e.stopPropagation();
    const wasDown = down; down = null;
    if (wasDown && Math.hypot(e.clientX - wasDown.x, e.clientY - wasDown.y) > 3) return;
    const p = pick(e.clientX, e.clientY);
    if (p && p !== 'ui') choose(p);
  }, true);
  W.addEventListener('dblclick', e => {
    if (!on || inUI(e)) return;
    const p = pick(e.clientX, e.clientY);
    if (p && p !== 'ui' && isText(p)) { e.preventDefault(); e.stopPropagation(); editText(p); }
  }, true);
  W.addEventListener('wheel', e => {
    if (!on || !sel || !isMedia(sel) || tagIs(sel, /CANVAS/i)) return;
    const r = sel.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return;
    e.preventDefault();
    if (!W.__edWheel || Date.now() - W.__edWheel > 300) mark(); W.__edWheel = Date.now();
    if (e.ctrlKey) { const z = zoomBy(sel, Math.exp(-e.deltaY * .01)); say('zoom ' + z.toFixed(2) + ' · ' + scopeWords(sel), e.clientX, e.clientY); }
    else { const [x, y] = framePos(sel); const o = reframe(sel, -e.deltaX, -e.deltaY, x, y); say(o.stuck ? 'it fits its frame: pinch to zoom in first' : 'framing ' + o.val, e.clientX, e.clientY); }
    clearTimeout(W.__edWheelEnd); W.__edWheelEnd = setTimeout(() => { commit(); }, 350);
    draw();
  }, {capture: true, passive: false});
  W.addEventListener('keydown', e => {
    if (e.altKey && e.code === 'KeyE') { e.preventDefault(); setOn(!on); return; }
    if (!on || editing) return;
    if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && !inUI(e)) return;
    if (e.key === 'Alt') { alt = true; soon(); }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
    if (inUI(e) && /^(INPUT|TEXTAREA)$/.test((e.composedPath()[0] || {}).tagName || '')) return;
    if (e.key === '?') { help.classList.toggle('on'); return; }
    if (e.key === 'Escape') { if (help.classList.contains('on') || note.classList.contains('on')) { help.classList.remove('on'); note.classList.remove('on'); } else { sel = null; buildChip(); } draw(); return; }
    if (e.key === '\\') { if (sheet.sheet) sheet.sheet.disabled = true; flash('Before'); return; }
    if (!sel) return;
    if (e.key === 's' || e.key === 'S') { scope = SCOPES[(SCOPES.indexOf(scope) + 1) % 3]; buildChip(); draw(); flash('Changes now apply to ' + ({all: 'all like it', page: 'this page only', one: 'just this one'})[scope]); }
    if (e.key === 'ArrowUp' && sel.parentElement && sel.parentElement !== D.documentElement) { e.preventDefault(); choose(sel.parentElement); }
    if (e.key === 'ArrowDown' && sel.firstElementChild) { e.preventDefault(); choose(sel.firstElementChild); }
  }, true);
  W.addEventListener('keyup', e => {
    if (e.key === 'Alt') { alt = false; soon(); }
    if (e.key === '\\' && sheet.sheet) sheet.sheet.disabled = false;
  }, true);
  W.addEventListener('scroll', soon, {capture: true, passive: true});
  W.addEventListener('resize', soon);

  /* ── on and off ───────────────────────────────────────────────────────────── */
  function loop() { if (!on) return; if (sel || hov) draw(); requestAnimationFrame(loop); }          // follows scrolling, animation, re-renders
  function setOn(v) {
    on = v; try { localStorage.setItem(ONKEY, v ? '1' : '0'); } catch (e) {}
    if (v) { D.documentElement.appendChild(host); drawPill(); flash('Editor on: hover anything, press ? for gestures'); requestAnimationFrame(loop); }
    else { host.remove(); hov = sel = drag = null; if (chip) chip.remove(); chip = null; }
  }
  function start() {
    css(); applyTexts(); tidy(); learnClasses();
    const q = new URLSearchParams(location.search);
    if (q.has(PARAM)) { try { localStorage.setItem(ONKEY, q.get(PARAM) === '0' ? '0' : '1'); } catch (e) {} }
    let want = false; try { want = localStorage.getItem(ONKEY) === '1'; } catch (e) {}
    if (want) setOn(true);
    // single-page apps: new routes keep their page-only changes and words
    let path = location.pathname;
    setInterval(() => { mount(); if (location.pathname !== path) { path = location.pathname; css(); applyTexts(); } }, 700);
  }
  W.__editor = {on: () => setOn(true), off: () => setOn(false), copy, report, reset: () => { mark(); S = {rules: [], texts: []}; commit(); }};
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start); else start();
})();
