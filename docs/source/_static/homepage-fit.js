/* The homepage's editable example. All scientific work happens in a worker. */
(() => {
  function highlight(code, language) {
    const fragment = document.createDocumentFragment();
    // A small lexical highlighter, using text nodes throughout: editor content
    // and exported labels can never become HTML or script in the page.
    const tokens = /#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:from|import|True|False|None)\b|\b(?:lin_fit)\b|\b\d+(?:\.\d*)?(?:[eE][+-]?\d+)?\b|\[[A-Za-z_][^\]\n]*\]/g;
    let end = 0;
    for (const match of code.matchAll(tokens)) {
      fragment.append(document.createTextNode(code.slice(end, match.index)));
      const span = document.createElement('span');
      const token = match[0];
      const kind = token.startsWith('#') ? 'c' : /^["']/.test(token) ? 's'
        : /^\d/.test(token) ? 'mi' : token === 'lin_fit' ? 'nf'
        : language === 'toml' && token.startsWith('[') ? 'k' : 'k';
      span.className = `mh-syntax-${kind}`;
      span.textContent = token;
      fragment.append(span);
      end = match.index + token.length;
    }
    fragment.append(document.createTextNode(code.slice(end)));
    return fragment;
  }
  function init() {
    const editor = document.querySelector('[data-fit-demo]');
    if (!editor) return;
    const source = editor.querySelector('textarea');
    const preview = editor.querySelector('.mh-editor-highlight code');
    const lines = editor.querySelector('.mh-editor-lines');
    const run = editor.querySelector('.mh-fit-run');
    const cancel = editor.querySelector('.mh-fit-cancel');
    const status = editor.querySelector('.mh-fit-status');
    const error = editor.querySelector('p.mh-fit-error');
    const results = document.getElementById('demo-fit-results');
    const image = results.querySelector('img');
    const openFigure = results.querySelector('.mh-fit-open');
    const output = results.querySelector('.mh-fit-toml code');
    const copy = results.querySelector('.mh-fit-copy');
    let worker;
    let runId = 0;
    let busy = false;
    let ready = false;
    let timer;
    let imageURL;
    let toml = '';
    function syncEditor() {
      preview.replaceChildren(highlight(source.value, 'python'));
      lines.textContent = Array.from({length: source.value.split('\n').length}, (_, i) => i + 1).join('\n');
      moveEditor();
    }
    function moveEditor() {
      preview.style.transform = `translate(${-source.scrollLeft}px, ${-source.scrollTop}px)`;
      lines.style.transform = `translateY(${-source.scrollTop}px)`;
    }
    function clearResults() {
      results.hidden = true;
      image.removeAttribute('src');
      openFigure.removeAttribute('href');
      if (imageURL) URL.revokeObjectURL(imageURL);
      imageURL = undefined;
      toml = '';
      output.replaceChildren();
    }
    function setBusy(value) {
      busy = value;
      run.disabled = value;
      source.readOnly = value;
      cancel.hidden = !value;
      editor.querySelector('.mh-editor-code').setAttribute('aria-busy', String(value));
    }
    function destroyWorker() {
      worker?.terminate();
      worker = undefined;
      ready = false;
    }
    function fail(message, reset = false) {
      clearTimeout(timer);
      clearResults();
      if (reset) destroyWorker();
      setBusy(false);
      status.textContent = '';
      error.textContent = message;
      error.hidden = false;
      if (document.activeElement === document.body) run.focus({preventScroll:true});
    }
    function timeLimit(ms) {
      clearTimeout(timer);
      timer = setTimeout(() => fail(editor.dataset.timeout, true), ms);
    }
    async function receive({ data }) {
      if (data.id !== runId || !busy) return;
      if (data.stage) {
        status.textContent = editor.dataset[data.stage];
        if (data.stage === 'execute') { ready = true; timeLimit(30000); }
        return;
      }
      if (data.error) { fail(`${editor.dataset.loadError}\n${data.error}`, true); return; }
      const result = data.result;
      if (!result?.ok) {
        const translated = editor.querySelector(`[data-error="${result?.code || 'structure'}"]`);
        fail(result?.error || translated?.textContent || editor.dataset.loadError);
        return;
      }
      // Decode before revealing either panel. Both outputs become visible in
      // one task, tagged with the same run id; never show a half-updated pair.
      const url = URL.createObjectURL(new Blob([result.svg], {type:'image/svg+xml'}));
      const pending = new Image();
      pending.src = url;
      try { await pending.decode(); }
      catch {
        URL.revokeObjectURL(url);
        if (data.id === runId && busy) fail(editor.dataset.loadError);
        return;
      }
      if (data.id !== runId || !busy) { URL.revokeObjectURL(url); return; }
      clearTimeout(timer);
      imageURL = url;
      image.src = url;
      openFigure.href = url;
      toml = result.toml;
      output.replaceChildren(highlight(toml, 'toml'));
      results.dataset.runId = String(data.id);
      results.hidden = false;
      // Begin at the fitted parameters. The complete, unchanged export remains
      // available above/below this position and is copied in full.
      const fitStart = toml.indexOf('[fit]');
      const pre = output.parentElement;
      pre.scrollTop = fitStart < 0 ? 0 : (toml.slice(0, fitStart).split('\n').length - 1)
        * parseFloat(getComputedStyle(pre).lineHeight);
      setBusy(false);
      status.textContent = editor.dataset.success + (result.warnings?.length ? ` ${result.warnings.join(' ')}` : '');
      if (document.activeElement === document.body) run.focus({preventScroll:true});
    }
    function execute() {
      if (busy) return;
      clearResults();
      error.hidden = true;
      runId += 1;
      setBusy(true);
      status.textContent = ready ? editor.dataset.execute : editor.dataset.runtime;
      timeLimit(ready ? 30000 : 180000);
      try {
        if (!worker) {
          worker = new Worker(editor.dataset.worker, {type:'module'});
          worker.addEventListener('message', receive);
          const current = worker;
          const runtimeError = () => { if (worker === current && busy) fail(editor.dataset.loadError, true); };
          worker.addEventListener('error', runtimeError);
          worker.addEventListener('messageerror', runtimeError);
        }
        worker.postMessage({id:runId, code:source.value});
      } catch (exception) { fail(`${editor.dataset.loadError}\n${exception.message}`, true); }
    }
    run.addEventListener('click', execute);
    cancel.addEventListener('click', () => {
      runId += 1;
      clearTimeout(timer);
      destroyWorker();
      clearResults();
      setBusy(false);
      status.textContent = editor.dataset.cancelled;
      run.focus({preventScroll:true});
    });
    source.addEventListener('input', () => {
      syncEditor();
      clearResults();
      error.hidden = true;
      status.textContent = editor.dataset.stale;
    });
    source.addEventListener('scroll', moveEditor);
    source.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); execute(); }
    });
    function fallbackCopy(text) {
      const field = document.createElement('textarea');
      field.value = text;
      field.readOnly = true;
      field.style.cssText = 'position:fixed;opacity:0;width:1px;height:1px';
      document.body.append(field);
      try {
        field.focus({preventScroll:true});
        field.select();
        return document.execCommand('copy');
      } finally { field.remove(); copy.focus({preventScroll:true}); }
    }
    copy.addEventListener('click', async () => {
      const snapshot = toml;
      let copied = false;
      try {
        if (navigator.clipboard?.writeText) {
          try { await navigator.clipboard.writeText(snapshot); copied = true; }
          catch { copied = fallbackCopy(snapshot); }
        } else copied = fallbackCopy(snapshot);
      } catch { copied = false; }
      if (toml === snapshot) status.textContent = copied ? editor.dataset.copySuccess : editor.dataset.copyFailure;
    });
    window.addEventListener('pagehide', () => { clearTimeout(timer); destroyWorker(); clearResults(); setBusy(false); });
    syncEditor();
    if ('Worker' in window) run.disabled = false;
    else { error.textContent = editor.dataset.loadError; error.hidden = false; }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
