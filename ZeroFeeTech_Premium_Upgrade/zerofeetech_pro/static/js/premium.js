(() => {
  const menu = document.getElementById('menuToggle');
  const nav = document.getElementById('mainNav');
  if (menu && nav) {
    menu.addEventListener('click', () => {
      const open = nav.classList.toggle('nav-open');
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      nav.classList.remove('nav-open'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Open navigation');
    }));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') { nav.classList.remove('nav-open'); menu.setAttribute('aria-expanded','false'); } });
  }
  const revealItems = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
    }), { threshold: 0.12, rootMargin: '0px 0px -35px 0px' });
    revealItems.forEach(item => observer.observe(item));
  } else revealItems.forEach(item => item.classList.add('is-visible'));
  const sections = [...document.querySelectorAll('main section[id]')];
  const navLinks = [...document.querySelectorAll('#mainNav a[href*="#"]')];
  if ('IntersectionObserver' in window && sections.length && navLinks.length) {
    const activeObserver = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) navLinks.forEach(link => {
        const target = link.getAttribute('href').split('#')[1];
        link.classList.toggle('active', target === entry.target.id);
      });
    }), { rootMargin: '-28% 0px -62% 0px' });
    sections.forEach(section => activeObserver.observe(section));
  }
  document.querySelectorAll('[data-service]').forEach(link => link.addEventListener('click', () => {
    const service = link.dataset.service;
    const select = document.getElementById('service');
    if (!select || !service) return;
    const options = [...select.options];
    const match = options.find(option => option.text.toLowerCase().includes(service.toLowerCase())) || options.find(option => service.toLowerCase().includes(option.text.toLowerCase()));
    if (match) select.value = match.value || match.text;
  }));
  document.querySelectorAll('[data-configure-contact]').forEach(button => button.addEventListener('click', () => {
    const note = document.getElementById('contactConfigNote');
    if (note) note.textContent = `${button.dataset.configureContact} contact is not connected yet. Add the official ${button.dataset.configureContact} URL in the site configuration before enabling this button.`;
  }));
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
  // The existing prompt studio is kept intact; this ensures its save endpoint receives CSRF protection.
  const saveButton = document.getElementById('savePrompt');
  if (saveButton) saveButton.dataset.csrf = csrf;
})();
