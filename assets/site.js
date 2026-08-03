// Studio Maçon — shared behavior

// fullscreen menu overlay — hamburger animates to an X in place
document.addEventListener('click', e => {
  if (e.target.closest('[data-menu-toggle]')) document.body.classList.toggle('menu-open');
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.body.classList.remove('menu-open');
});

// nav logo — replay the blink animation on hover (GIF restarts when src is re-set)
document.querySelectorAll('.nav .logo img').forEach(img => {
  const base = img.getAttribute('src').split('?')[0];
  let busy = false;
  img.closest('.logo').addEventListener('mouseenter', () => {
    if (busy) return;
    busy = true;
    img.src = base + '?t=' + Date.now();
    setTimeout(() => { busy = false; }, 900);   // let the blink finish before re-arming
  });
});

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
