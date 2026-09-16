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
</script>
