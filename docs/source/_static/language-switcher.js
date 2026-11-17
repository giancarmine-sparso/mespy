(() => {
  // The build already resolves each link's destination (the same page in the
  // other language, or its home when the page has no counterpart). Links
  // stay native: this only carries the current query and fragment over to a
  // same-page link, without network requests or preventDefault.
  const LINK_SELECTOR =
    "[data-language-switcher-link='true']:not([data-language-fallback='true'])";

  function carryLocation(link) {
    const url = new URL(link.href, window.location.href);
    url.search = window.location.search;
    url.hash = window.location.hash;
    link.href = url.href;
  }

  function carryLocationToAll() {
    document.querySelectorAll(LINK_SELECTOR).forEach(carryLocation);
  }

  function initLanguageSwitcher() {
    carryLocationToAll();
    window.addEventListener("hashchange", carryLocationToAll);
    // Also refresh right before activation, in case the URL changed through
    // the History API, which fires no hashchange.
    document.querySelectorAll(LINK_SELECTOR).forEach((link) => {
      link.addEventListener("click", () => carryLocation(link));
      link.addEventListener("auxclick", () => carryLocation(link));
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLanguageSwitcher);
  } else {
    initLanguageSwitcher();
  }
})();
