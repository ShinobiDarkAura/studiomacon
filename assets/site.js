// Studio Maçon — shared behavior

// fullscreen menu overlay — hamburger animates to an X in place
document.addEventListener('click', e => {
  if (e.target.closest('[data-menu-toggle]')) document.body.classList.toggle('menu-open');
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.body.classList.remove('menu-open');
});

// nav logo — the eye follows the cursor and blinks on a random interval.
// Pupil + eyelid are plain elements layered behind the silhouette PNG, so the
// transparent eye opening clips them for free. No JS = static, correct logo.
(function () {
  const goats = [...document.querySelectorAll('.nav .logo .goat')];
  if (!goats.length) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // blink — one independent random 4–7s timer per logo
  goats.forEach(goat => {
    const again = () => setTimeout(blink, 4000 + Math.random() * 3000);
    const blink = () => {
      goat.classList.add('blink');
      setTimeout(() => goat.classList.remove('blink'), 300);
      again();
    };
    again();
  });

  // cursor tracking — skipped on touch / coarse pointers
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

  const MAX_X = 0.06;   // pupil travel, as a fraction of the logo's rendered width
  const MAX_Y = 0.03;
  const REACH = 420;    // px from the logo at which the eye is fully deflected
  const eyes = goats.map(goat => ({
    el: goat.querySelector('.goat-pupil'),
    box: goat,
    x: 0, y: 0, tx: 0, ty: 0,
  }));

  let px = 0, py = 0, seen = false, raf = 0;

  function measure() {
    for (const e of eyes) {
      const r = e.box.getBoundingClientRect();
      if (!r.width) { e.tx = e.ty = 0; continue; }
      const dx = (px - (r.left + r.width / 2)) / REACH;
      const dy = (py - (r.top + r.height / 2)) / REACH;
      const d = Math.hypot(dx, dy) || 1;
      const k = Math.min(1, d) / d;          // clamp to the unit disc, keep direction
      e.tx = dx * k * MAX_X * r.width;
      e.ty = dy * k * MAX_Y * r.width;
    }
  }

  function tick() {
    raf = 0;
    measure();
    let moving = false;
    for (const e of eyes) {
      e.x += (e.tx - e.x) * 0.14;            // ease toward the target
      e.y += (e.ty - e.y) * 0.14;
      if (Math.abs(e.tx - e.x) > 0.02 || Math.abs(e.ty - e.y) > 0.02) moving = true;
      e.el.style.transform = 'translate(' + e.x.toFixed(2) + 'px,' + e.y.toFixed(2) + 'px)';
    }
    if (moving) raf = requestAnimationFrame(tick);
  }

  function wake() { if (!raf) raf = requestAnimationFrame(tick); }

  window.addEventListener('pointermove', ev => {
    if (ev.pointerType && ev.pointerType !== 'mouse') return;
    px = ev.clientX; py = ev.clientY; seen = true;
    wake();
  }, { passive: true });
  window.addEventListener('scroll', () => { if (seen) wake(); }, { passive: true });
})();

// NOTES accordion
document.querySelectorAll('[data-notes-toggle]').forEach(btn => {
  btn.addEventListener('click', () => {
    const block = btn.closest('.notes-block');
    const open = block.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
});

// product gallery — click a thumbnail to swap the main image
document.querySelectorAll('.thumbs img').forEach(t => {
  t.addEventListener('click', () => {
    const main = document.getElementById('mainImg');
    if (main) main.src = t.dataset.full;
    document.querySelectorAll('.thumbs img').forEach(x => x.classList.remove('on'));
    t.classList.add('on');
  });
});

// contact form — interim: opens the visitor's mail client prefilled.
// TODO: swap for Formspree or a Supabase function before launch.
const cform = document.getElementById('cform');
if (cform) {
  cform.addEventListener('submit', e => {
    e.preventDefault();
    const f = e.target;
    const body = encodeURIComponent(`Name: ${f.first.value} ${f.last.value}\nEmail: ${f.email.value}\n\n${f.message.value}`);
    const subject = encodeURIComponent('Hello from ' + f.first.value);
    window.location.href = `mailto:hello@studiomacon.co?subject=${subject}&body=${body}`;
  });
}
