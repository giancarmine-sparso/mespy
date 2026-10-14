/* Get started: installation tabs and copy buttons. Without JavaScript every
   installation panel stays visible and the copy buttons stay hidden. */
(() => {
  function initTabs(root) {
    const tablist = root.querySelector('[role="tablist"]');
    const tabs = [...tablist.querySelectorAll('[role="tab"]')];
    const panels = tabs.map((tab) => document.getElementById(tab.getAttribute('aria-controls')));

    function select(index, focus = false) {
      tabs.forEach((tab, i) => {
        const selected = i === index;
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
        panels[i].hidden = !selected;
      });
      if (focus) tabs[index].focus();
    }

    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => select(index));
      tab.addEventListener('keydown', (event) => {
        const last = tabs.length - 1;
        const next = {
          ArrowRight: index === last ? 0 : index + 1,
          ArrowDown: index === last ? 0 : index + 1,
          ArrowLeft: index === 0 ? last : index - 1,
          ArrowUp: index === 0 ? last : index - 1,
          Home: 0,
          End: last,
        }[event.key];
        if (next === undefined) return;
        event.preventDefault();
        select(next, true);
      });
    });
    panels.forEach((panel) => { panel.tabIndex = 0; });

    // A link such as #install-pip opens that method directly.
    const linked = panels.findIndex((panel) => `#${panel.id}` === window.location.hash);
    select(linked === -1 ? 0 : linked);
    tablist.hidden = false;
    root.classList.add('gs-tabs-ready');
    if (linked !== -1) root.scrollIntoView();
  }

  async function writeClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    // file:// previews and older browsers.
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.append(area);
    area.select();
    const copied = document.execCommand('copy');
    area.remove();
    if (!copied) throw new Error('copy failed');
  }

  function initCopy(main) {
    const status = document.getElementById('gs-copy-status');
    main.querySelectorAll('[data-copy]').forEach((button) => {
      const source = document.getElementById(button.dataset.copy);
      const idle = button.innerHTML;
      let timer = 0;
      button.hidden = false;
      button.addEventListener('click', async () => {
        clearTimeout(timer);
        let ok = true;
        try {
          await writeClipboard(source.textContent.trim());
        } catch {
          ok = false;
          window.getSelection().selectAllChildren(source);
        }
        button.textContent = ok ? main.dataset.copied : main.dataset.copyFailed;
        button.classList.toggle('gs-copied', ok);
        status.textContent = '';
        // Clearing first lets screen readers repeat an identical message.
        setTimeout(() => {
          status.textContent = ok ? main.dataset.copiedStatus : main.dataset.copyFailedStatus;
        }, 50);
        timer = setTimeout(() => {
          button.innerHTML = idle;
          button.classList.remove('gs-copied');
        }, 2000);
      });
    });
  }

  function init() {
    const main = document.querySelector('.mespy-start #main-content');
    if (!main) return;
    main.querySelectorAll('[data-tabs]').forEach(initTabs);
    initCopy(main);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
