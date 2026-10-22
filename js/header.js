/* Shared site header: sticky shrink, mobile menu, tap/keyboard dropdowns, current page. */
/* ---------- HEADER ---------- */
(() => {
  const header = document.getElementById('site-header');
  const menuBtn = header.querySelector('.menu-toggle');
  const drops = Array.from(header.querySelectorAll('.has-dropdown'));

  // Header compacto al hacer scroll
  const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 10);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Menú hamburguesa (móvil)
  function setMenu(open) {
    header.classList.toggle('menu-open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    if (!open) closeDrops();
  }
  menuBtn.addEventListener('click', () => setMenu(!header.classList.contains('menu-open')));

  // Desplegables: funcionan con clic/tap y teclado, no solo con hover
  function closeDrops(except) {
    drops.forEach(li => {
      if (li === except) return;
      li.classList.remove('is-open');
      li.querySelector('.dropdown-toggle').setAttribute('aria-expanded', 'false');
    });
  }
  drops.forEach(li => {
    const btn = li.querySelector('.dropdown-toggle');
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const open = !li.classList.contains('is-open');
      closeDrops(li);
      li.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  document.addEventListener('click', e => {
    if (!header.contains(e.target)) { closeDrops(); setMenu(false); }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeDrops(); setMenu(false); }
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) setMenu(false);
  });

  // Marca la página actual
  const clean = p => p.replace(/index\.html$/, '').replace(/\/?$/, '/');
  const here = clean(location.pathname);
  header.querySelectorAll('.nav-list a').forEach(a => {
    if (clean(a.getAttribute('href')) === here) {
      a.setAttribute('aria-current', 'page');
      const parent = a.closest('.has-dropdown');
      if (parent) parent.querySelector('.dropdown-toggle').classList.add('is-current');
    }
  });
})();
