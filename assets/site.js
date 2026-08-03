// Studio Maçon — shared behavior

// fullscreen menu overlay
document.addEventListener('click', e => {
  if (e.target.closest('[data-menu-open]')) document.body.classList.add('menu-open');
  if (e.target.closest('[data-menu-close]')) document.body.classList.remove('menu-open');
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.body.classList.remove('menu-open');
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
