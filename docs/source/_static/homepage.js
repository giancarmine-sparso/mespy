/* Landing-style pages: compact menu, one-shot reveals and an event-driven
   scroll response for the homepage hero (absent on Get started). */
(() => {

  function init() {
    const page = document.querySelector('.mespy-home');
    if (!page) return;

    const menu = page.querySelector('.mh-menu-toggle');
    const navigation = page.querySelector('#mh-navigation');
    const compactNavigation = window.matchMedia('(max-width: 1050px)');
    const closeMenu = (restoreFocus = false) => {
      page.classList.remove('mh-menu-open');
      menu.setAttribute('aria-expanded', 'false');
      if (restoreFocus) menu.focus();
    };
    menu.hidden = false;
    page.classList.add('mh-menu-ready');
    menu.addEventListener('click', () => {
      const expanded = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(expanded));
      page.classList.toggle('mh-menu-open', expanded);
    });
    navigation.addEventListener('click', (event) => {
      if (compactNavigation.matches && event.target.closest('a')) {
        closeMenu(navigation.contains(document.activeElement));
      }
    });
    page.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && page.classList.contains('mh-menu-open')) {
        closeMenu(true);
      }
    });

    compactNavigation.addEventListener('change', () => {
      closeMenu(compactNavigation.matches && navigation.contains(document.activeElement));
    });

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const revealTargets = [...page.querySelectorAll('[data-reveal]')];
    const hero = page.querySelector('.mh-hero-visual');
    const art = page.querySelector('.mh-scroll-art');
    let revealObserver;
    let heroObserver;
    let heroVisible = false;
    let frame = 0;

    function updateScroll() {
      frame = 0;
      if (!heroVisible || document.hidden || reducedMotion.matches) return;
      // Bounded movement, only within the hero; no perpetual animation loop.
      art.style.setProperty('--mh-scroll-shift', `${Math.min(window.scrollY * .045, 24)}px`);
    }
    function onScroll() {
      if (heroVisible && !frame) frame = requestAnimationFrame(updateScroll);
    }
    function configureMotion() {
      revealObserver?.disconnect();
      heroObserver?.disconnect();
      window.removeEventListener('scroll', onScroll);
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      heroVisible = false;
      art?.style.removeProperty('--mh-scroll-shift');
      revealTargets.forEach((target) => target.classList.remove('mh-pending', 'mh-in-view'));
      if (reducedMotion.matches || !('IntersectionObserver' in window)) return;

      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.remove('mh-pending');
          entry.target.classList.add('mh-in-view');
          revealObserver.unobserve(entry.target);
        });
      }, { threshold: .08 });
      revealTargets.forEach((target) => {
        target.classList.add('mh-pending');
        revealObserver.observe(target);
      });
      if (!hero || !art) return;
      heroObserver = new IntersectionObserver(([entry]) => {
        heroVisible = entry.isIntersecting;
        if (heroVisible) onScroll();
      });
      heroObserver.observe(hero);
      window.addEventListener('scroll', onScroll, { passive: true });
    }
    reducedMotion.addEventListener('change', configureMotion);
    configureMotion();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
