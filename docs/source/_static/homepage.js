/* Landing-style pages: the header's compact menu. The pages have no scroll
   effects; the homepage's only motion is its two mascots (homepage-duck.js,
   homepage-cat.js). */
(() => {

  function init() {
    const page = document.querySelector('.mespy-home');
    if (!page) return;

    const menu = page.querySelector('.mh-menu-toggle');
    const navigation = page.querySelector('#mh-navigation');
    // The compact menu's width, as in homepage.css and search.css.
    const compactNavigation = window.matchMedia('(max-width: 1200px)');
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
      // Escape in the search dialog closes the dialog only, which gives the
      // focus back to the search button.
      if (event.target.closest('#pst-search-dialog')) return;
      if (event.key === 'Escape' && page.classList.contains('mh-menu-open')) {
        closeMenu(true);
      }
    });

    compactNavigation.addEventListener('change', () => {
      closeMenu(compactNavigation.matches && navigation.contains(document.activeElement));
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
