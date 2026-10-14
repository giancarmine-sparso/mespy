/* Guide pages (GUIDE_PAGES in conf.py): highlight the section being read in
   the example navigators and keep the mobile menu summary in sync. Without
   JavaScript the navigators are plain lists of anchor links. */
(() => {
  function init() {
    const links = [...document.querySelectorAll('[data-guide-nav] a[href^="#"]')];
    if (!links.length) return;

    const targets = [...new Set(links.map((link) => decodeURIComponent(link.hash.slice(1))))]
      .map((id) => document.getElementById(id))
      .filter(Boolean)
      .sort((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1));
    const menu = document.querySelector('[data-guide-menu]');
    const current = menu && menu.querySelector('[data-guide-current]');
    const sidebar = document.querySelector('.gd-aside');
    let active = null;

    // A section becomes current once its start rises into the top quarter
    // of the visible area (below the sticky mobile menu, when it is shown).
    function readingLine() {
      const bar = menu && menu.offsetParent ? menu.getBoundingClientRect().bottom : 0;
      const top = Math.max(bar, 0);
      return top + Math.min((window.innerHeight - top) / 4, 200);
    }

    function keepVisible(link) {
      if (!sidebar || !sidebar.contains(link) || sidebar.scrollHeight <= sidebar.clientHeight) return;
      const box = sidebar.getBoundingClientRect();
      const item = link.getBoundingClientRect();
      if (item.top < box.top + 48) sidebar.scrollTop -= box.top + 48 - item.top;
      else if (item.bottom > box.bottom - 48) sidebar.scrollTop += item.bottom - box.bottom + 48;
    }

    function update() {
      const line = readingLine();
      let next = targets[0];
      for (const target of targets) {
        if (target.getBoundingClientRect().top > line) break;
        next = target;
      }
      const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      if (atBottom) next = targets[targets.length - 1];
      if (next === active) return;
      active = next;

      links.forEach((link) => {
        const on = link.hash === `#${active.id}`;
        if (on) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
        if (on) keepVisible(link);
      });
      document.querySelectorAll('[data-guide-nav] .mx-guide-nav__group').forEach((group) => {
        group.classList.toggle('mx-guide-nav__group--active', Boolean(group.querySelector('[aria-current]')));
      });
      if (current) {
        const label = links.find((link) => link.hash === `#${active.id}`);
        const text = label && label.querySelector('.mx-guide-nav__text');
        current.textContent = (text || label).textContent.trim();
      }
    }

    let queued = false;
    function schedule() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => {
        queued = false;
        update();
      });
    }
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    update();

    if (!menu) return;
    const summary = menu.querySelector('summary');
    menu.addEventListener('click', (event) => {
      if (event.target.closest('a[href^="#"]')) menu.open = false;
    });
    menu.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menu.open) {
        menu.open = false;
        summary.focus();
      }
    });
    document.addEventListener('click', (event) => {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
