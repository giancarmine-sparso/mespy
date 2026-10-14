/* Shared pixel-sprite renderer for the homepage mascots (duck, cat). */
window.mespyPixel = (() => {
  const SVG_NS = 'http://www.w3.org/2000/svg';

  function svgEl(name, attrs) {
    const el = document.createElementNS(SVG_NS, name);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
    return el;
  }

  // One char per logical pixel; chars missing from the palette are transparent.
  function frameGroup(id, rows, palette) {
    const group = svgEl('g', { id });
    rows.forEach((row, y) => {
      // Merge runs of equal pixels into a single rect.
      for (let x = 0; x < row.length;) {
        let end = x + 1;
        while (row[end] === row[x]) end += 1;
        if (palette[row[x]]) {
          const rect = svgEl('rect', { x, y, width: end - x, height: 1 });
          rect.style.fill = palette[row[x]];
          group.append(rect);
        }
        x = end;
      }
    });
    return group;
  }

  return { svgEl, frameGroup };
})();
