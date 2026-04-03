(() => {
  function navigateToLanguage(event) {
    const link = event.currentTarget;
    const targetUrl = new URL(link.href, window.location.href);
    const homeUrl = new URL(link.dataset.languageHome, window.location.href);

    if (window.location.search) {
      targetUrl.search = window.location.search;
      homeUrl.search = window.location.search;
    }
    if (window.location.hash) {
      targetUrl.hash = window.location.hash;
      homeUrl.hash = window.location.hash;
    }

    event.preventDefault();

    const goTo = (url) => {
      window.location.assign(url.toString());
    };

    if (window.location.protocol === "file:") {
      goTo(targetUrl);
      return;
    }

    fetch(targetUrl, { method: "HEAD" })
      .then((response) => {
        goTo(response.ok ? targetUrl : homeUrl);
      })
      .catch(() => {
        goTo(homeUrl);
      });
  }

  function initLanguageSwitcher() {
    document
      .querySelectorAll("[data-language-switcher-link='true']")
      .forEach((link) => {
        link.addEventListener("click", navigateToLanguage);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLanguageSwitcher);
  } else {
    initLanguageSwitcher();
  }
})();
