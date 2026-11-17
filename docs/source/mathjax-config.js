// MathJax font: STIX2, the formula counterpart of STIX Two Text. Inlined by
// sphinx.ext.mathjax (mathjax_config_path in conf.py) after MyST's
// `window.MathJax = ...` and before MathJax loads: it extends that object, so
// MyST's processHtmlClass and the TeX delimiters stay as they are. The font
// data URL starts from the page's content root, so it is right at any depth
// and under /mespy/, and is absolute so MathJax does not resolve it against
// its CDN location.
(() => {
  const root = new URL(document.documentElement.dataset.content_root ?? "./", document.baseURI);
  const config = (window.MathJax ??= {});
  config.output = {
    ...config.output,
    font: "mathjax-stix2",
    fontPath: new URL("_static/fonts/mathjax-stix2-font", root).href,
  };
})();
